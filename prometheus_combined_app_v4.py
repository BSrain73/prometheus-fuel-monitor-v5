
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy.fft import fft, fftfreq

st.set_page_config(page_title="Prometheus Fuel Monitor", layout="wide")
st.title("🚍 Prometheus Fuel Monitor")

uploaded_file = st.file_uploader("📥 Sube archivo CSV", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.lower()
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["co2_kg"] = df["litros"] * 2.68
    df["consumo_l_km"] = df["litros"] / df["km"]
    df["co2_por_pasajero"] = df["co2_kg"] / df["pasajeros"]

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Visión general", "🚐 Por taxibús", "📈 Evolución",
        "🛠️ Modelos", "🏆 Eficiencia", "🔮 Pronóstico y Ciclos"
    ])

    with tab1:
        st.header("📊 Visión general")
        col1, col2, col3 = st.columns(3)
        col1.metric("CO₂eq total (kg)", f"{df['co2_kg'].sum():,.0f}")
        col2.metric("Promedio CO₂eq/pasajero", f"{df['co2_por_pasajero'].mean():.2f} kg")
        col3.metric("Total pasajeros", f"{df['pasajeros'].sum():,.0f}")

        fig1 = px.histogram(df, x="consumo_l_km", nbins=30, title="Distribución consumo L/km")
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown("🧠 **Interpretación:** La distribución muestra concentración entre 0.4 y 0.6 L/km. Revisar outliers por sobre 0.7 L/km para mejorar eficiencia.")

    with tab2:
        st.header("🚐 Análisis por vehículo")
        bus = st.selectbox("Selecciona vehículo", df["cod_maq"].unique())
        df_bus = df[df["cod_maq"] == bus]
        consumo_prom = df_bus["consumo_l_km"].mean()
        co2_total = df_bus["co2_kg"].sum()

        fig2 = px.line(df_bus, x="fecha", y="consumo_l_km", title="Consumo L/km por fecha")
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown(f"🧠 **Interpretación:** El consumo promedio de este vehículo es {consumo_prom:.2f} L/km. {'⚠️ Sobre el umbral de eficiencia (0.6)' if consumo_prom > 0.6 else '✅ Bajo el umbral de eficiencia'}.")

        fig3 = px.line(df_bus, x="fecha", y="co2_kg", title="Emisiones CO₂eq")
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown(f"🧠 **Interpretación:** Emisión acumulada de CO₂eq para este vehículo: {co2_total:,.0f} kg.")

        fig4 = px.line(df_bus, x="fecha", y="pasajeros", title="Pasajeros transportados")
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown("🧠 **Interpretación:** Evaluar tendencias decrecientes que puedan reflejar baja demanda o desvíos operativos.")

    with tab3:
        st.header("📈 Evolución global diaria")
        df_time = df.groupby("fecha").agg({"litros": "sum", "co2_kg": "sum", "pasajeros": "sum"}).reset_index()
        fig5 = px.line(df_time, x="fecha", y=["litros", "co2_kg", "pasajeros"], title="Evolución temporal")
        st.plotly_chart(fig5, use_container_width=True)
        st.markdown("🧠 **Interpretación:** Variaciones semanales/mensuales pueden reflejar estacionalidad o eventos. Combinar con análisis FFT.")

    with tab4:
        st.header("🛠️ Comparación por modelo")
        fig6 = px.box(df, x="modelo", y="consumo_l_km", title="Consumo L/km por modelo")
        st.plotly_chart(fig6, use_container_width=True)
        st.markdown("🧠 **Interpretación:** Modelos con menor dispersión en consumo indican desempeño más predecible. Evaluar modelos con mediana < 0.55 L/km.")

        fig7 = px.box(df, x="modelo", y="co2_por_pasajero", title="CO₂eq por pasajero por modelo")
        st.plotly_chart(fig7, use_container_width=True)
        st.markdown("🧠 **Interpretación:** Modelos con mayor CO₂eq/pasajero podrían priorizarse para renovación o intervención operativa.")

    with tab5:
        st.header("🏆 Ranking de eficiencia")
        ranking = df.groupby("modelo").agg({
            "consumo_l_km": "mean",
            "co2_por_pasajero": "mean"
        }).reset_index().sort_values("co2_por_pasajero")
        st.dataframe(ranking)
        fig8 = px.bar(ranking, x="modelo", y="co2_por_pasajero", title="Ranking CO₂eq/pax")
        st.plotly_chart(fig8, use_container_width=True)
        fig9 = px.bar(ranking, x="modelo", y="consumo_l_km", title="Ranking consumo L/km")
        st.plotly_chart(fig9, use_container_width=True)
        st.markdown("🧠 **Interpretación:** Modelos en los primeros lugares son preferibles para expansión de flota o benchmarking interno.")

    with tab6:
        st.header("🔮 Pronóstico y análisis espectral")
        variable = st.selectbox("Variable a proyectar", ["litros", "co2_kg", "pasajeros"])
        periodo = st.selectbox("Días a predecir", [7, 30, 90])
        ts = df[["fecha", variable]].groupby("fecha").sum().asfreq("D").fillna(method="ffill")

        if len(ts) > 2 * periodo:
            model = ExponentialSmoothing(ts[variable], trend="add")
            fit = model.fit()
            forecast = fit.forecast(periodo)

            df_pred = ts.copy()
            forecast_df = pd.DataFrame({"fecha": forecast.index, "Pronóstico": forecast.values}).set_index("fecha")
            df_full = pd.concat([df_pred, forecast_df], axis=0)

            fig_pred = px.line(df_full, y=[variable, "Pronóstico"], title=f"Pronóstico de {variable}")
            st.plotly_chart(fig_pred, use_container_width=True)

            tendencia = "creciente" if forecast[-1] > fit.fittedvalues[-1] else "decreciente"
            st.info(f"📊 Tendencia proyectada: {tendencia}")

            y = ts[variable] - ts[variable].mean()
            fft_vals = np.abs(fft(y))[:len(y)//2]
            fft_freqs = fftfreq(len(y), d=1)[:len(y)//2]
            df_fft = pd.DataFrame({"Frecuencia": fft_freqs, "Potencia": fft_vals})
            df_fft = df_fft[df_fft["Frecuencia"] > 0]
            freq_dom = df_fft.sort_values("Potencia", ascending=False).iloc[0]["Frecuencia"]
            ciclo = round(1 / freq_dom) if freq_dom != 0 else "indefinido"

            fig_fft = px.line(df_fft, x="Frecuencia", y="Potencia", title="Espectro FFT")
            st.plotly_chart(fig_fft, use_container_width=True)
            st.success(f"🔁 Ciclo dominante estimado: cada {ciclo} días")
            st.markdown("🧠 **Interpretación:** Esta proyección permite anticipar escenarios operativos futuros. Ciclos de 7 días indican comportamiento semanal típico.")
        else:
            st.warning("No hay suficientes datos para pronóstico.")
else:
    st.info("Por favor sube un archivo para comenzar.")










          
