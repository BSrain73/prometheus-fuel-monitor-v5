import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io

st.set_page_config(page_title="Prometheus Fuel Monitor", layout="wide")

st.title("🚍 Prometheus Fuel Monitor")
st.markdown("Carga tu archivo de consumo de combustible para visualizar métricas, eficiencia, emisiones y alertas.")

uploaded_file = st.file_uploader("Sube tu archivo CSV o Excel", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ Archivo cargado correctamente")
        st.dataframe(df.head())

        # 🔧 Normalizar columnas
        df.columns = df.columns.str.strip().str.lower()

        if all(col in df.columns for col in ['km', 'litros']):
            # Cálculos base
            df["consumo_l_km"] = df["litros"] / df["km"]
            df["co2_kg"] = df["litros"] * 2.68  # Emisión CO2eq por litro de diesel

            # Umbral para alertas
            umbral = 0.6
            df["alerta"] = df["consumo_l_km"] > umbral

            # KPIs globales
            st.subheader("📌 Indicadores globales")
            col1, col2, col3 = st.columns(3)
            col1.metric("Promedio consumo (L/km)", round(df["consumo_l_km"].mean(), 2))
            col2.metric("Total litros consumidos", int(df["litros"].sum()))
            col3.metric("CO₂ equivalente (kg)", int(df["co2_kg"].sum()))

            # Selector de taxibús
            if "cod_maq" in df.columns:
                st.subheader("🚐 Indicadores por taxibús")
                vehiculos = sorted(df["cod_maq"].unique())
                selected_bus = st.selectbox("Selecciona un vehículo", vehiculos)
                df_bus = df[df["cod_maq"] == selected_bus]

                colb1, colb2, colb3 = st.columns(3)
                colb1.metric("Prom. consumo", round(df_bus["consumo_l_km"].mean(), 2))
                colb2.metric("Litros totales", int(df_bus["litros"].sum()))
                colb3.metric("CO₂ eq (kg)", int(df_bus["co2_kg"].sum()))

                # 📤 Exportar a Excel los datos del taxibús seleccionado
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_bus.to_excel(writer, index=False, sheet_name="Datos_bus")
                st.download_button(
                    label="📥 Descargar Excel del taxibús",
                    data=output.getvalue(),
                    file_name=f"reporte_{selected_bus}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            # Gráfico de consumo por vehículo, coloreado por alerta
            fig_bar = px.bar(df, x="cod_maq", y="consumo_l_km", color="alerta",
                             color_discrete_map={True: "red", False: "green"},
                             title="Consumo por vehículo (con alertas)",
                             labels={"cod_maq": "Vehículo", "alerta": "Sobreconsumo"})
            st.plotly_chart(fig_bar, use_container_width=True)

            # Histograma con línea de umbral
            fig_hist = px.histogram(df, x="consumo_l_km", nbins=20,
                                    title="Distribución del consumo (L/km)")
            fig_hist.add_vline(x=umbral, line_dash="dash", line_color="red",
                               annotation_text="Umbral", annotation_position="top right")
            st.plotly_chart(fig_hist, use_container_width=True)

            # Gráfico de evolución temporal
            if "fecha" in df.columns:
                df["fecha"] = pd.to_datetime(df["fecha"], errors='coerce')
                df_time = df.dropna(subset=["fecha"])
                df_time_grouped = df_time.groupby("fecha").agg({"litros": "sum", "co2_kg": "sum"}).reset_index()
                fig_time = px.line(df_time_grouped, x="fecha", y=["litros", "co2_kg"],
                                   title="Evolución temporal de consumo y CO₂eq",
                                   labels={"value": "Cantidad", "variable": "Indicador"})
                st.plotly_chart(fig_time, use_container_width=True)

            # Comparación por modelo de taxibús
            if "modelo" in df.columns:
                modelo_grouped = df.groupby("modelo").agg({"consumo_l_km": "mean"}).reset_index()
                fig_modelo = px.bar(modelo_grouped, x="modelo", y="consumo_l_km",
                                    title="Consumo promedio por modelo de taxibús",
                                    labels={"modelo": "Modelo", "consumo_l_km": "Consumo (L/km)"})
                st.plotly_chart(fig_modelo, use_container_width=True)

            # Alerta global
            ineficientes = df[df["alerta"]]
            if not ineficientes.empty:
                st.warning(f"⚠️ {len(ineficientes)} registros superan el umbral de consumo (> {umbral} L/km).")

        else:
            st.warning("⚠️ Las columnas 'km' y 'litros' son necesarias para calcular consumo.")
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("⬆️ Esperando que cargues un archivo para comenzar.")



          
