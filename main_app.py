import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# Configuración de la página
st.set_page_config(page_title="Dashboard COVID-19", page_icon="🦠", layout="wide")

# ==========================================
# 1. GENERACIÓN DE DATOS SINTÉTICOS
# ==========================================
@st.cache_data
def load_data():
    """Genera 10 registros sintéticos con 8 columnas de diferentes tipos de datos."""
    np.random.seed(42) # Para reproducibilidad
    
    fechas = [datetime.today() - timedelta(days=i) for i in range(10)]
    paises = ['Colombia', 'México', 'Perú', 'Argentina', 'Chile', 'Ecuador', 'España', 'Italia', 'Francia', 'Alemania']
    casos = np.random.randint(1000, 50000, 10)
    
    data = {
        "ID_Registro": range(1, 11),                          # Entero
        "Fecha": fechas,                                      # Fecha (Datetime)
        "Pais": paises,                                       # Cadena (String)
        "Casos_Confirmados": casos,                           # Entero
        "Recuperados": casos - np.random.randint(100, 900, 10),# Entero (Lógica: Recuperados < Casos)
        "Tasa_Mortalidad_Porcentaje": np.random.uniform(0.5, 3.5, 10), # Flotante (Float)
        "Estado_Alerta": np.random.choice(['Alto', 'Medio', 'Bajo'], 10), # Categórico
        "Con_Restricciones": np.random.choice([True, False], 10) # Booleano
    }
    return pd.DataFrame(data)

df = load_data()

# ==========================================
# INTERFAZ DE USUARIO Y BARRA LATERAL (SIDEBAR)
# ==========================================
st.title("🦠 Dashboard Interactivo COVID-19 (Datos Sintéticos)")
st.markdown("Esta aplicación simula datos epidemiológicos y permite su análisis interactivo.")

st.sidebar.header("⚙️ Panel de Control")

# Selector de variables para graficar
col_numericas = ['Casos_Confirmados', 'Recuperados', 'Tasa_Mortalidad_Porcentaje']
col_categoricas = ['Pais', 'Estado_Alerta', 'Con_Restricciones']

var_x = st.sidebar.selectbox("Selecciona la variable para el Eje X", col_categoricas)
var_y = st.sidebar.selectbox("Selecciona la variable para el Eje Y", col_numericas)

# Slider para umbral dinámico (Filtro)
umbral_casos = st.sidebar.slider(
    "Filtro: Casos Confirmados mínimos", 
    min_value=int(df['Casos_Confirmados'].min()), 
    max_value=int(df['Casos_Confirmados'].max()), 
    value=int(df['Casos_Confirmados'].min()),
    step=1000
)

# Filtramos el DataFrame según el umbral elegido
df_filtrado = df[df['Casos_Confirmados'] >= umbral_casos]

# ==========================================
# 2. ESQUEMA DE MÉTRICAS
# ==========================================
st.header("📊 Resumen Estadístico")

if not df_filtrado.empty:
    col1, col2, col3, col4 = st.columns(4)
    
    # Métricas Cuantitativas
    col1.metric("Total Casos Confirmados", f"{df_filtrado['Casos_Confirmados'].sum():,}")
    col2.metric("Tasa Mortalidad Promedio", f"{df_filtrado['Tasa_Mortalidad_Porcentaje'].mean():.2f}%")
    
    # Métricas Cualitativas
    alerta_comun = df_filtrado['Estado_Alerta'].mode()[0]
    paises_restringidos = df_filtrado['Con_Restricciones'].sum()
    
    col3.metric("Estado de Alerta más común", alerta_comun)
    col4.metric("Países con Restricciones", f"{paises_restringidos} de {len(df_filtrado)}")
else:
    st.warning("El umbral seleccionado es demasiado alto. No hay datos para mostrar las métricas.")

# ==========================================
# MOSTRAR DATOS CRUDOS
# ==========================================
with st.expander("Ver Base de Datos Simulada (10 Registros, 8 Columnas)"):
    st.dataframe(df_filtrado, use_container_width=True)

# ==========================================
# 3. GRÁFICAS DINÁMICAS (PLOTLY)
# ==========================================
st.header("📈 Análisis Visual Dinámico")

if not df_filtrado.empty:
    tab1, tab2 = st.tabs(["Gráfico de Barras", "Gráfico de Dispersión"])
    
    with tab1:
        st.subheader(f"{var_y} por {var_x}")
        # Gráfica de Barras con Plotly Express
        fig_bar = px.bar(
            df_filtrado, 
            x=var_x, 
            y=var_y, 
            color='Estado_Alerta',
            color_discrete_map={'Alto': 'red', 'Medio': 'orange', 'Bajo': 'green'},
            text_auto='.2s',
            title=f"Distribución de {var_y.replace('_', ' ')} según {var_x.replace('_', ' ')}"
        )
        
        # Añadir línea de umbral promedio interactiva
        promedio = df_filtrado[var_y].mean()
        fig_bar.add_hline(y=promedio, line_dash="dot", 
                          annotation_text=f"Promedio: {promedio:.2f}", 
                          annotation_position="top right", 
                          line_color="black")
        
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.subheader("Relación Casos vs Recuperados")
        # Gráfica de Dispersión interactiva
        fig_scatter = px.scatter(
            df_filtrado, 
            x='Casos_Confirmados', 
            y='Recuperados', 
            size='Tasa_Mortalidad_Porcentaje', 
            color='Pais',
            hover_name='Pais',
            title="Relación de Casos Confirmados vs Recuperados (Tamaño = Tasa de Mortalidad)"
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.error("Ajusta el filtro en el panel lateral para poder visualizar los gráficos.")

st.markdown("---")
st.caption("Desarrollado con Streamlit y Plotly para el análisis de datos interactivos.")
