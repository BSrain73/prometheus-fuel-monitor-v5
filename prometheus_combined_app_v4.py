import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Prometheus Fuel Monitor", layout="wide")

# Estilo de encabezado
st.markdown("## 🚍 Prometheus Fuel Monitor")
st.markdown("**Dashboard de consumo, eficiencia energética y emisiones CO₂eq**")
st.markdown("---")

uploaded_file = st.file_uploader("📤 Sube tu archivo CSV o Excel con registros de flota", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ Archivo cargado correctamente")

        # Normalizar columnas
        df.columns = df.columns.str.strip().str.lower()

        if all(col in df.columns for col in ['km', 'litros']):
            df["consumo_l_km"] = df["litros"] / df["km"]
            df["co2_kg"] = df["litros"] * 2.68
            df["alerta"] = df["consumo_l_km"] > 0.6

            # Tabs para navegación
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Visión general", "🚐 Por taxibús", "📈 Evolución", "🛠 Modelos"])

            with tab1:
                st.subheader("📌 Indicadores generales")
                col1, col2, col3 = st.columns(3)
                col1.metric("Prom. consumo (L/km)", round(df["consumo_l_km"].mean(), 2))
                col2.metric("Litros totales", int(df["litros"].sum()))
                col3.metric("CO₂ equivalente (kg)", int(df["co2_kg"].sum()))

                st.markdown("#### 🚨 Alertas de sobreconsumo")
                sobre_umbral = df[df["alerta"]]
                st.warning(f"Se detectaron **{len(sobre_umbral)} registros** con consumo mayor a 0.6 L/km.")

                fig_alertas = px.bar(df, x="cod_maq", y="consumo_l_km", color="alerta",
                                     color_discrete_map={True: "red", False: "green"},
                                     title="Consumo por vehículo (con alerta visual)")
                st.plotly_chart(fig_alertas, use_container_width=True)

                fig_hist = px.histogram(df, x="consumo_l_km", nbins=25,
                                        title="Distribución de consumo L/km")
                fig_hist.add_vline(x=0.6, line_dash="dash", line_color="red", annotation_text="Umbral")
                st.plotly_chart(fig_hist, use_container_width=True)

            with tab2:
                st.subheader("🚐 Indicadores por taxibús")
                buses = sorted(df["cod_maq"].unique())
                selected = st.selectbox("Selecciona un vehículo", buses)
                df_bus = df[df["cod_maq"] == selected]

                colb1, colb2, colb3 = st.columns(3)
                colb1.metric("Consumo prom.", round(df_bus["consumo_l_km"].mean(), 2))
                colb2.metric("Litros totales", int(df_bus["litros"].sum()))
                colb3.metric("CO₂ eq (kg)", int(df_bus["co2_kg"].sum()))

                st.markdown("##### 📥 Exportar datos de este vehículo")
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_bus.to_excel(writer, index=False, sheet_name="Datos_bus")
                st.download_button("⬇️ Descargar Excel", data=output.getvalue(),
                                   file_name=f"reporte_{selected}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with tab3:
                st.subheader("📈 Evolución temporal")
                if "fecha" in df.columns:
                    df["fecha"] = pd.to_datetime(df["fecha"], errors='coerce')
                    df_time = df.dropna(subset=["fecha"])
                    resumen = df_time.groupby("fecha").agg({"litros": "sum", "co2_kg": "sum"}).reset_index()
                    fig_line = px.line(resumen, x="fecha", y=["litros", "co2_kg"],
                                       title="Evolución de litros y CO₂eq", labels={"value": "Cantidad"})
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("El archivo no contiene columna 'fecha'.")

            with tab4:
                st.subheader("🛠 Comparación por modelo de taxibús")
                if "modelo" in df.columns:
                    modelo_df = df.groupby("modelo").agg({"consumo_l_km": "mean"}).reset_index()
                    fig_modelo = px.bar(modelo_df, x="modelo", y="consumo_l_km",
                                        title="Consumo promedio por modelo")
                    st.plotly_chart(fig_modelo, use_container_width=True)
                else:
                    st.info("No se encontró la columna 'modelo'.")

        else:
            st.error("❌ Las columnas 'km' y 'litros' son necesarias para calcular consumo.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info("⬆️ Carga un archivo para comenzar.")



          
