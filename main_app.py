import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Monitor Meteorológico - Alcaldía de Montería", page_icon="🌤️", layout="wide")

# ==========================================
# AUTENTICACIÓN Y PANEL IZQUIERDO
# ==========================================
st.sidebar.title("EAFIT 202, GomSal, Ciencia de Datos")
st.sidebar.markdown("---")

# Clave de acceso
password = st.sidebar.text_input("Ingrese la clave del dashboard (Código 2020)", type="password")

if password != "2020":
    st.warning("🔒 Por favor, ingrese la clave correcta en el panel izquierdo para acceder al dashboard.")
    st.stop()

st.sidebar.success("✅ Acceso concedido")

# ==========================================
# 1. GENERACIÓN DE DATOS SINTÉTICOS BASADOS EN IDEAM
# ==========================================
@st.cache_data
def load_data():
    """Genera 500 registros con 10 columnas sobre datos meteorológicos en Montería y área metropolitana, calibrados con promedios del IDEAM."""
    np.random.seed(42)
    n_records = 500
    
    # Comunas y barrios de Montería y área metropolitana
    comunas_barrios = {
        'Comuna 1': ['El Dorado', 'Vallejo', 'Rancho Grande'],
        'Comuna 2': ['San José', 'Los Laureles', 'Minuto de Dios'],
        'Comuna 3': ['Santa Elena', 'Buenavista', 'La Castellana'],
        'Comuna 4': ['La Granja', 'P5', 'San Martín'],
        'Comuna 5': ['El Prado', 'Alamedas', 'Los Colores']
    }
    
    # Serie de tiempo: 100 días para cada una de las 5 comunas (Total 500 registros)
    # Retrocedemos 100 días desde la fecha actual (Julio 2026)
    fecha_inicio = datetime.today() - timedelta(days=100)
    fechas = [fecha_inicio + timedelta(days=i) for i in range(100)] * 5
    comunas = np.repeat(list(comunas_barrios.keys()), 100)
    barrios = [np.random.choice(comunas_barrios[c]) for c in comunas]
    
    # Simulando variables meteorológicas según promedios del IDEAM para Montería (aprox. Julio)
    # Temperatura Media: ~28.6°C (Distribución normal ajustada para que las máximas lleguen ~37°C y mínimas ~20°C)
    temp = np.random.normal(28.6, 3.0, n_records) 
    
    # Humedad Promedio en Julio: ~78%
    humedad = np.random.normal(78, 8, n_records) 
    
    # Viento: Promedios moderados, simulando ráfagas ocasionales
    viento = np.random.gamma(2.5, 4.5, n_records) 
    
    # Precipitación mensual media en Julio ~146.5mm, lo que da un promedio diario bajo pero con picos en días de tormenta
    precipitacion = np.random.exponential(4.8, n_records) 
    
    poblacion = np.random.randint(3000, 25000, n_records) # Población afectada
    
    # Lógica de Riesgo (Cualitativa) para la alcaldía, ajustada a la realidad
    riesgo = []
    for t, h, p, v in zip(temp, humedad, precipitacion, viento):
        # Alerta máxima por picos de calor recientes (>37°C) o lluvias intensas (>25mm/día)
        if p > 25 or v > 30 or (t > 37 and h > 75): 
            riesgo.append("Alto")
        elif p > 10 or v > 20 or t > 34:
            riesgo.append("Medio")
        else:
            riesgo.append("Bajo")
            
    df = pd.DataFrame({
        "ID_Registro": range(1, n_records + 1),
        "Fecha": fechas,
        "Comuna": comunas,
        "Barrio": barrios,
        "Temp_C": temp.round(1),
        "Humedad_Pct": np.clip(humedad, 40, 100).round(1),
        "Viento_kmh": viento.round(1),
        "Precipitacion_mm": precipitacion.round(1),
        "Poblacion": poblacion,
        "Nivel_Riesgo": riesgo
    })
    return df

df = load_data()

# ==========================================
# INTERFAZ Y FILTROS
# ==========================================
st.title("🌤️ Sistema de Alerta Temprana Meteorológica (Datos Calibrados - IDEAM)")
st.markdown("**Ciudad:** Montería, Córdoba y Área Metropolitana")
st.markdown("*Nota: Los datos sintéticos han sido ajustados tomando como referencia los promedios históricos del IDEAM para el clima cálido y húmedo de la región.*")

st.sidebar.header("⚙️ Filtros de Análisis")
comunas_seleccionadas = st.sidebar.multiselect(
    "Selecciona Comuna(s)", 
    options=df['Comuna'].unique(),
    default=df['Comuna'].unique()
)

riesgo_seleccionado = st.sidebar.multiselect(
    "Filtrar por Nivel de Riesgo",
    options=['Bajo', 'Medio', 'Alto'],
    default=['Bajo', 'Medio', 'Alto']
)

# Filtramos la data en función de la selección del usuario
df_filtrado = df[(df['Comuna'].isin(comunas_seleccionadas)) & (df['Nivel_Riesgo'].isin(riesgo_seleccionado))]

# ==========================================
# 2. ESQUEMA DE MÉTRICAS (Cuantitativas y Cualitativas)
# ==========================================
st.header("📊 Métricas de Control y Riesgo")

if not df_filtrado.empty:
    c1, c2, c3, c4 = st.columns(4)
    
    # Métricas clave
    c1.metric("Temperatura Promedio", f"{df_filtrado['Temp_C'].mean():.1f} °C")
    c2.metric("Precipitación Máx. Diaria", f"{df_filtrado['Precipitacion_mm'].max():.1f} mm")
    
    # Población total en riesgo alto (Suma de afectados)
    pob_riesgo_alto = df_filtrado[df_filtrado['Nivel_Riesgo'] == 'Alto']['Poblacion'].sum()
    c3.metric("Población Riesgo Alto", f"{pob_riesgo_alto:,}")
    
    c4.metric("Registros Analizados", len(df_filtrado))
    
    with st.expander("Ver Base de Datos (500 Registros, 10 Columnas)"):
        st.dataframe(df_filtrado, use_container_width=True)
else:
    st.warning("No hay datos con los filtros seleccionados.")

# ==========================================
# 3. ANÁLISIS GRÁFICO DINÁMICO (PLOTLY)
# ==========================================
st.header("📈 Análisis Visual y Series de Tiempo")

if not df_filtrado.empty:
    tab1, tab2, tab3 = st.tabs(["Serie de Tiempo", "Dispersión (Viento vs Temp)", "Impacto Poblacional"])
    
    with tab1:
        st.subheader("Evolución Meteorológica en el Tiempo")
        var_tiempo = st.selectbox("Selecciona la variable a visualizar en el tiempo:", 
                                  ['Temp_C', 'Humedad_Pct', 'Precipitacion_mm', 'Viento_kmh'])
        
        # Agrupamos por fecha y comuna para la gráfica de serie de tiempo
        df_agrupado = df_filtrado.groupby(['Fecha', 'Comuna'])[var_tiempo].mean().reset_index()
        
        fig_time = px.line(
            df_agrupado, 
            x="Fecha", 
            y=var_tiempo, 
            color="Comuna",
            title=f"Serie de Tiempo: {var_tiempo} promedio por Comuna",
            markers=True
        )
        
        # Añadir línea de promedio histórico si es Temperatura o Humedad
        if var_tiempo == 'Temp_C':
             fig_time.add_hline(y=28.6, line_dash="dash", line_color="red", annotation_text="Promedio Histórico IDEAM (Julio): 28.6°C")
        elif var_tiempo == 'Humedad_Pct':
             fig_time.add_hline(y=78, line_dash="dash", line_color="blue", annotation_text="Promedio Histórico IDEAM (Julio): 78%")
             
        st.plotly_chart(fig_time, use_container_width=True)
        
    with tab2:
        st.subheader("Relación de Variables y Nivel de Riesgo")
        fig_scatter = px.scatter(
            df_filtrado,
            x="Temp_C",
            y="Viento_kmh",
            color="Nivel_Riesgo",
            size="Precipitacion_mm",
            hover_name="Barrio",
            color_discrete_map={'Alto': 'red', 'Medio': 'orange', 'Bajo': 'green'},
            title="Temp vs Viento (Tamaño de la burbuja = Nivel de Precipitación)"
        )
        # Líneas de umbral dinámicas configurables por el usuario
        umbral_temp = st.slider("Ajustar Umbral Crítico de Temperatura (°C)", 20.0, 42.0, 37.0)
        fig_scatter.add_vline(x=umbral_temp, line_dash="dot", line_color="blue", annotation_text="Límite Temp")
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with tab3:
        st.subheader("Población Afectada según Nivel de Riesgo")
        fig_bar = px.bar(
            df_filtrado.groupby('Nivel_Riesgo')['Poblacion'].sum().reset_index(),
            x='Nivel_Riesgo',
            y='Poblacion',
            color='Nivel_Riesgo',
            color_discrete_map={'Alto': 'red', 'Medio': 'orange', 'Bajo': 'green'},
            text_auto='.2s',
            title="Suma total de población por categoría de riesgo"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
