import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="Prometheus Fuel Monitor", layout="wide")

st.markdown("## 🚍 Prometheus Fuel Monitor")
st.markdown("**Dashboard de consumo, emisiones, eficiencia y pasajeros transportados**")
st.markdown("---")

uploaded_file = st.file_uploader("📤 Sube tu archivo CSV o Excel con registros de flota", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ Archivo cargado correctamente")
        df.columns = df.columns.str.strip().str.lower()

        if all(col in df.columns for col in ['km', 'litros', 'pasajeros']):
            df["consumo_l_km"] = df["litros"] / df["km"]
            df["co2_kg"] = df["litros"] * 2.68
            df["consumo_por_pasajero"] = df["litros"] / df["pasajeros"]
            df["co2_por_pasajero"] = df["co2_kg"] / df["pasajeros"]
            df["alerta"] = df["consumo_l_km"] > 0.6

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Visión general", "🚐 Por taxibús", "📈 Evolución", "🛠 Modelos", "🏆 Eficiencia"])

            with tab1:
                st.subheader("📌 Indicadores globales")
                col1, col2, col3 = st.columns(3)
                col1.metric("Consumo (L/km)", round(df["consumo_l_km"].mean(), 2))
                col2.metric("Pasajeros totales", int(df["pasajeros"].sum()))
                col3.metric("CO₂ eq por pasajero (kg)", round(df["co2_por_pasajero"].mean(), 2))

                fig_eff = px.histogram(df, x="consumo_por_pasajero", nbins=25,
                                       title="Distribución de consumo por pasajero (L/pax)")
                st.plotly_chart(fig_eff, use_container_width=True)

                fig_alert = px.bar(df, x="cod_maq", y="consumo_l_km", color="alerta",
                                   color_discrete_map={True: "red", False: "green"},
                                   title="Consumo por vehículo (con alerta)")
                st.plotly_chart(fig_alert, use_container_width=True)

            with tab2:
                st.subheader("🚐 Indicadores por taxibús")
                buses = sorted(df["cod_maq"].unique())
                selected = st.selectbox("Selecciona un vehículo", buses)
                df_bus = df[df["cod_maq"] == selected]

                colb1, colb2, colb3 = st.columns(3)
                colb1.metric("Consumo (L/km)", round(df_bus["consumo_l_km"].mean(), 2))
                colb2.metric("Pasajeros transportados", int(df_bus["pasajeros"].sum()))
                colb3.metric("CO₂ eq total (kg)", int(df_bus["co2_kg"].sum()))

                if "fecha" in df_bus.columns:
                    df_bus["fecha"] = pd.to_datetime(df_bus["fecha"], errors='coerce')
                    df_bus = df_bus.dropna(subset=["fecha"])

                    st.markdown("#### 📈 Evolución del consumo (L/km)")
                    fig_evol = px.line(df_bus, x="fecha", y="consumo_l_km", markers=True,
                                       title="Consumo L/km por fecha")
                    fig_evol.add_hline(y=0.6, line_dash="dot", line_color="red",
                                       annotation_text="Umbral", annotation_position="top right")
                    st.plotly_chart(fig_evol, use_container_width=True)

                    st.markdown("#### 🧍‍♂️ Evolución de pasajeros transportados")
                    fig_pax = px.line(df_bus, x="fecha", y="pasajeros", markers=True,
                                      title="Pasajeros transportados por fecha")
                    st.plotly_chart(fig_pax, use_container_width=True)

                    st.markdown("#### ♻️ Evolución de emisiones CO₂eq (kg)")
                    fig_co2 = px.line(df_bus, x="fecha", y="co2_kg", markers=True,
                                      title="Emisiones CO₂eq por fecha")
                    st.plotly_chart(fig_co2, use_container_width=True)

                    st.markdown("#### 🌱 CO₂eq por pasajero transportado")
                    df_bus["co2_por_pasajero"] = df_bus["co2_kg"] / df_bus["pasajeros"]
                    fig_copax = px.line(df_bus, x="fecha", y="co2_por_pasajero", markers=True,
                                        title="Emisiones CO₂eq por pasajero (kg/pax)")
                    st.plotly_chart(fig_copax, use_container_width=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_bus.to_excel(writer, index=False, sheet_name="Datos_bus")
                st.download_button("⬇️ Descargar Excel", data=output.getvalue(),
                                   file_name=f"reporte_{selected}.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            with tab3:
                st.subheader("📈 Evolución temporal general")
                if "fecha" in df.columns:
                    df["fecha"] = pd.to_datetime(df["fecha"], errors='coerce')
                    df_time = df.dropna(subset=["fecha"])
                    resumen = df_time.groupby("fecha").agg({
                        "litros": "sum",
                        "co2_kg": "sum",
                        "pasajeros": "sum"
                    }).reset_index()
                    fig_line = px.line(resumen, x="fecha", y=["litros", "co2_kg", "pasajeros"],
                                       title="Evolución de litros, CO₂eq y pasajeros")
                    st.plotly_chart(fig_line, use_container_width=True)
                else:
                    st.info("El archivo no contiene columna 'fecha'.")

            with tab4:
                st.subheader("📦 Comparación por modelo")
                if "modelo" in df.columns:
                    fig_box = px.box(df, x="modelo", y="consumo_l_km",
                                     title="Distribución de consumo por modelo (L/km)")
                    st.plotly_chart(fig_box, use_container_width=True)

                    st.markdown("#### 🌱 CO₂eq por pasajero por modelo (Box Plot)")
                    fig_copax_model = px.box(df, x="modelo", y="co2_por_pasajero",
                                             title="Distribución de CO₂eq por pasajero por modelo",
                                             labels={"co2_por_pasajero": "CO₂eq/pax"})
                    st.plotly_chart(fig_copax_model, use_container_width=True)
                else:
                    st.info("No se encontró la columna 'modelo'.")

            with tab5:
                st.subheader("🏆 Ranking de eficiencia por modelo")
                if "modelo" in df.columns:
                    modelo_ranking = df.groupby("modelo").agg({
                        "consumo_l_km": "mean",
                        "co2_por_pasajero": "mean"
                    }).reset_index().sort_values("co2_por_pasajero")

                    st.dataframe(modelo_ranking.style.format({
                        "consumo_l_km": "{:.2f}",
                        "co2_por_pasajero": "{:.2f}"
                    }), use_container_width=True)

                    st.markdown("### 🌱 CO₂eq por pasajero (promedio)")
                    fig_rank_co2 = px.bar(modelo_ranking, x="modelo", y="co2_por_pasajero",
                                          title="Ranking de eficiencia ambiental (CO₂eq/pax)",
                                          labels={"co2_por_pasajero": "CO₂eq/pax"})
                    st.plotly_chart(fig_rank_co2, use_container_width=True)

                    st.markdown("### ⛽ Consumo de combustible (L/km promedio)")
                    fig_rank_lkm = px.bar(modelo_ranking, x="modelo", y="consumo_l_km",
                                          title="Ranking de eficiencia de combustible (L/km)",
                                          labels={"consumo_l_km": "L/km"})
                    st.plotly_chart(fig_rank_lkm, use_container_width=True)
                else:
                    st.warning("No se encontró la columna 'modelo'.")

        else:
            st.error("❌ Las columnas 'km', 'litros' y 'pasajeros' son requeridas.")
    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
else:
    st.info("⬆️ Carga un archivo para comenzar.")








          
