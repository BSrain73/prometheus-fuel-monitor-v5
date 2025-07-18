import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Prometheus Fuel Monitor", layout="wide")

st.title("🚍 Prometheus Fuel Monitor")
st.markdown("Carga tu archivo de consumo de combustible para visualizar métricas, eficiencia y emisiones.")

uploaded_file = st.file_uploader("Sube tu archivo CSV o Excel", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ Archivo cargado correctamente")
        st.dataframe(df.head())

        if all(col in df.columns for col in ['km', 'litros']):
            df["consumo_L_km"] = df["litros"] / df["km"]
            promedio = round(df["consumo_L_km"].mean(), 2)
            st.metric("Consumo promedio (L/km)", promedio)

            fig = px.histogram(df, x="consumo_L_km", nbins=30, title="Distribución del consumo (L/km)")
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("Análisis rápido completado.")
        else:
            st.warning("Las columnas 'km' y 'litros' son necesarias para calcular consumo.")
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("⬆️ Esperando que cargues un archivo para comenzar.")
