
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy.fft import fft, fftfreq

st.set_page_config(page_title="Prometheus Fuel Monitor", layout="wide")

st.title("🚍 Prometheus Fuel Monitor")
uploaded_file = st.file_uploader("Carga un archivo CSV o Excel con datos de combustible, pasajeros y fechas", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith("csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha")
    df["consumo_km_l"] = df["km"] / df["litros"]
    df["co2_kg"] = df["litros"] * 2.68
    df["co2_por_pasajero"] = df["co2_kg"] / df["pasajeros"]

    tabs = st.tabs(["📊 Visión general", "🚐 Por taxibús", "📈 Evolución", "🛠️ Modelos", "🏆 Eficiencia", "🔮 Pronóstico y Ciclos"])

    with tabs[5]:
        st.header("🔮 Pronóstico de consumo y análisis de ciclos")
        variable = st.selectbox("Selecciona variable a analizar", ["litros", "km", "co2_kg", "pasajeros"])

        df_ts = df[["fecha", variable]].copy()
        df_ts["fecha"] = pd.to_datetime(df_ts["fecha"])
        df_ts = df_ts.groupby("fecha").sum().asfreq("D").fillna(method="ffill")
        df_ts.index.name = "fecha"

        model = ExponentialSmoothing(df_ts[variable], trend="add", seasonal=None)
        model_fit = model.fit()
        forecast = model_fit.forecast(30)

        forecast_df = pd.DataFrame({
            "fecha": forecast.index,
            "Pronóstico": forecast.values
        }).set_index("fecha")

        df_pred = pd.concat([df_ts, forecast_df], axis=0)

        st.subheader(f"Pronóstico de {variable}")
        st.line_chart(df_pred)

        st.subheader("🔍 Análisis de frecuencia (FFT)")
        y = df_ts[variable].values
        N = len(y)
        yf = fft(y)
        xf = fftfreq(N, d=1)

        fft_df = pd.DataFrame({
            "Frecuencia": xf[:N//2],
            "Amplitud": 2.0/N * np.abs(yf[0:N//2])
        })

        fig_fft = px.line(fft_df, x="Frecuencia", y="Amplitud", title="Espectro de Frecuencias")
        st.plotly_chart(fig_fft, use_container_width=True)

        st.markdown("""
        **Interpretación sugerida:**  
        Las proyecciones permiten anticipar aumentos en el consumo o caídas en el transporte de pasajeros, lo que puede anticipar contingencias operativas o presupuestarias.  
        Los picos del análisis espectral indican patrones cíclicos (diarios, semanales) que pueden estar relacionados con turnos, estacionalidad o condiciones externas.
        """)

else:
    st.warning("Por favor sube un archivo para comenzar.")










          
