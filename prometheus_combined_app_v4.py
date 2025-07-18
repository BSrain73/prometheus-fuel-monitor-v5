import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy.fft import fft, fftfreq
import io

st.set_page_config(page_title="Prometheus Fuel Monitor", layout="wide")
st.title("🚍 Prometheus Fuel Monitor – Análisis completo")

uploaded_file = st.file_uploader("📤 Sube tu archivo CSV o Excel", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.lower()
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])

    if all(col in df.columns for col in ["km", "litros", "pasajeros"]):
        df["consumo_l_km"] = df["litros"] / df["km"]
        df["co2_kg"] = df["litros"] * 2.68
        df["consumo_por_pasajero"] = df["litros"] / df["pasajeros"]
        df["co2_por_pasajero"] = df["co2_kg"] / df["pasajeros"]
        df["alerta"] = df["consumo_l_km"] > 0.6

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Visión general", "🚐 Por taxibús", "📈 Evolución",
            "🛠 Modelos", "🏆 Eficiencia", "🔮 Pronóstico y Ciclos"
        ])

        with tab1:
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 12px; border-left: 6px solid #2c6ef5; border-radius: 5px;'>
            📌 <strong>Resumen ejecutivo:</strong> Esta vista resume los promedios generales de eficiencia, pasajeros transportados y emisiones, permitiendo comparar el rendimiento global de la flota con los objetivos operativos y ambientales.
            </div>
            """, unsafe_allow_html=True)

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
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 12px; border-left: 6px solid #2c6ef5; border-radius: 5px;'>
            📌 <strong>Resumen ejecutivo:</strong> Análisis detallado por vehículo individual, útil para detectar unidades ineficientes o fuera de estándar, evaluar anomalías de consumo y priorizar mantenimientos.
            </div>
            """, unsafe_allow_html=True)

            buses = sorted(df["cod_maq"].unique())
            selected = st.selectbox("Selecciona un vehículo", buses)
            df_bus = df[df["cod_maq"] == selected]

            colb1, colb2, colb3 = st.columns(3)
            colb1.metric("Consumo (L/km)", round(df_bus["consumo_l_km"].mean(), 2))
            colb2.metric("Pasajeros transportados", int(df_bus["pasajeros"].sum()))
            colb3.metric("CO₂ eq total (kg)", int(df_bus["co2_kg"].sum()))

            df_bus["fecha"] = pd.to_datetime(df_bus["fecha"], errors='coerce')
            df_bus = df_bus.dropna(subset=["fecha"])

            st.markdown("#### 📈 Consumo por fecha")
            fig_evol = px.line(df_bus, x="fecha", y="consumo_l_km", markers=True,
                               title="Consumo L/km por fecha")
            fig_evol.add_hline(y=0.6, line_dash="dot", line_color="red",
                               annotation_text="Umbral", annotation_position="top right")
            st.plotly_chart(fig_evol, use_container_width=True)

            st.markdown("#### 🧍‍♂️ Pasajeros transportados por fecha")
            fig_pax = px.line(df_bus, x="fecha", y="pasajeros", markers=True)
            st.plotly_chart(fig_pax, use_container_width=True)

            st.markdown("#### ♻️ Emisiones CO₂eq por fecha")
            fig_co2 = px.line(df_bus, x="fecha", y="co2_kg", markers=True)
            st.plotly_chart(fig_co2, use_container_width=True)

            st.markdown("#### 🌱 CO₂eq por pasajero transportado")
            fig_copax = px.line(df_bus, x="fecha", y="co2_por_pasajero", markers=True)
            st.plotly_chart(fig_copax, use_container_width=True)

        with tab3:
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 12px; border-left: 6px solid #2c6ef5; border-radius: 5px;'>
            📌 <strong>Resumen ejecutivo:</strong> Evolución temporal diaria de consumo, emisiones y pasajeros, útil para identificar patrones, variabilidad y efectos de cambios operacionales.
            </div>
            """, unsafe_allow_html=True)

            df_time = df.groupby("fecha").agg({
                "litros": "sum",
                "co2_kg": "sum",
                "pasajeros": "sum"
            }).reset_index()

            fig_line = px.line(df_time, x="fecha", y=["litros", "co2_kg", "pasajeros"],
                               title="Evolución de litros, CO₂eq y pasajeros")
            st.plotly_chart(fig_line, use_container_width=True)

        with tab4:
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 12px; border-left: 6px solid #2c6ef5; border-radius: 5px;'>
            📌 <strong>Resumen ejecutivo:</strong> Compara modelos de vehículos según su rendimiento ambiental y energético, ayudando a decisiones de renovación de flota o eficiencia tecnológica.
            </div>
            """, unsafe_allow_html=True)

            fig_box = px.box(df, x="modelo", y="consumo_l_km",
                             title="Distribución de consumo por modelo (L/km)")
            st.plotly_chart(fig_box, use_container_width=True)

            fig_copax_model = px.box(df, x="modelo", y="co2_por_pasajero",
                                     title="Distribución de CO₂eq por pasajero por modelo")
            st.plotly_chart(fig_copax_model, use_container_width=True)
        with tab5:
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 12px; border-left: 6px solid #2c6ef5; border-radius: 5px;'>
            📌 <strong>Resumen ejecutivo:</strong> Ranking comparativo entre modelos según eficiencia energética y emisiones por pasajero, útil para benchmarking interno o decisiones de compra.
            </div>
            """, unsafe_allow_html=True)

            modelo_ranking = df.groupby("modelo").agg({
                "consumo_l_km": "mean",
                "co2_por_pasajero": "mean"
            }).reset_index().sort_values("co2_por_pasajero")

            st.dataframe(modelo_ranking.style.format({
                "consumo_l_km": "{:.2f}",
                "co2_por_pasajero": "{:.2f}"
            }), use_container_width=True)

            fig_rank_co2 = px.bar(modelo_ranking, x="modelo", y="co2_por_pasajero",
                                  title="Ranking eficiencia ambiental (CO₂eq/pax)",
                                  labels={"co2_por_pasajero": "CO₂eq/pax"})
            st.plotly_chart(fig_rank_co2, use_container_width=True)

            fig_rank_lkm = px.bar(modelo_ranking, x="modelo", y="consumo_l_km",
                                  title="Ranking eficiencia de combustible (L/km)",
                                  labels={"consumo_l_km": "L/km"})
            st.plotly_chart(fig_rank_lkm, use_container_width=True)

        with tab6:
            st.markdown("""
            <div style='background-color: #f0f2f6; padding: 12px; border-left: 6px solid #2c6ef5; border-radius: 5px;'>
            📌 <strong>Resumen ejecutivo:</strong> Esta pestaña permite anticipar consumos y emisiones con modelos estadísticos y detectar ciclos operacionales mediante análisis espectral, facilitando decisiones presupuestarias, ambientales y logísticas.
            </div>
            """, unsafe_allow_html=True)

            st.subheader("🔮 Pronóstico y análisis de ciclos")
            variable = st.selectbox("Selecciona variable a proyectar", ["litros", "co2_kg", "pasajeros"])
            periodo = st.selectbox("Periodo de pronóstico", [7, 30, 90])

            df_ts = df[["fecha", variable]].copy()
            df_ts = df_ts.groupby("fecha").sum().asfreq("D").fillna(method="ffill")

            if len(df_ts) > 2 * periodo:
                modelo = ExponentialSmoothing(df_ts[variable], trend="add", seasonal=None)
                ajuste = modelo.fit()
                forecast = ajuste.forecast(periodo)

                df_ts["Pronóstico"] = np.nan
                df_pred = df_ts.copy()
                df_pred.loc[forecast.index, "Pronóstico"] = forecast.values

                st.markdown(f"#### 📈 Proyección de {variable} próximos {periodo} días")
                fig_pred = px.line(df_pred, y=[variable, "Pronóstico"], title=f"Pronóstico de {variable}")
                st.plotly_chart(fig_pred, use_container_width=True)

                tendencia = "creciente" if forecast[-1] > ajuste.fittedvalues[-1] else "decreciente"
                st.info(f"📊 El modelo proyecta una tendencia **{tendencia}** para los próximos {periodo} días.")

                st.markdown("#### 🌀 Análisis espectral (FFT)")
                y_fft = df_ts[variable] - df_ts[variable].mean()
                fft_vals = np.abs(fft(y_fft))[:len(y_fft)//2]
                fft_freqs = fftfreq(len(y_fft), d=1)[:len(y_fft)//2]
                df_fft = pd.DataFrame({"Frecuencia": fft_freqs, "Potencia": fft_vals})
                df_fft = df_fft[df_fft["Frecuencia"] > 0]

                fig_fft = px.line(df_fft, x="Frecuencia", y="Potencia", title="Espectro de frecuencias")
                st.plotly_chart(fig_fft, use_container_width=True)

                freq_dominante = df_fft.sort_values("Potencia", ascending=False).iloc[0]["Frecuencia"]
                periodo_dominante = round(1 / freq_dominante) if freq_dominante != 0 else "indeterminado"
                st.success(f"🔁 Se detecta un ciclo dominante cada **{periodo_dominante} días**.")
            else:
                st.warning("⚠️ No hay suficientes datos para aplicar pronóstico o análisis espectral.")









          
