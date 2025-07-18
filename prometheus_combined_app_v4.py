import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from scipy.fft import fft, fftfreq
from statsmodels.tsa.holtwinters import ExponentialSmoothing

st.set_page_config(page_title="Prometheus Fuel Monitor", layout="wide")
st.title("🚍 Prometheus Fuel Monitor – Forecast & Spectral Analysis")

st.sidebar.header("📁 Cargar datos")
file = st.sidebar.file_uploader("Sube tu archivo CSV o Excel", type=["csv", "xlsx"])

if file is not None:
    if file.name.endswith("csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    df.columns = df.columns.str.lower()
    df["fecha"] = pd.to_datetime(df["fecha"], errors='coerce')
    df = df.dropna(subset=["fecha"])

    st.success("Archivo cargado correctamente")
    st.dataframe(df.head())

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📊 Visión general", "🚐 Por taxibús", "📈 Evolución",
        "🛠 Modelos", "🏆 Eficiencia", "🔮 Pronóstico y Ciclos"
    ])

    with tab6:
        st.markdown("""
        <div style='background-color: #f0f2f6; padding: 12px; border-left: 6px solid #2c6ef5; border-radius: 5px;'>
        📌 <strong>Resumen ejecutivo:</strong> Esta pestaña permite anticipar consumos y emisiones con modelos estadísticos y detectar ciclos operacionales mediante análisis espectral, facilitando decisiones presupuestarias, ambientales y logísticas.
        </div>
        """, unsafe_allow_html=True)

        st.subheader("🔮 Pronóstico y análisis de ciclos")
        variable = st.selectbox("Selecciona variable a proyectar", ["litros", "co2_kg", "pasajeros"])
        periodo = st.selectbox("Periodo de pronóstico", [7, 30, 90])

        df_time = df[["fecha", variable]].copy()
        df_time["fecha"] = pd.to_datetime(df_time["fecha"], errors='coerce')
        df_time = df_time.dropna().groupby("fecha").sum().asfreq("D").fillna(method="ffill")

        if len(df_time) > 2 * periodo:
            modelo = ExponentialSmoothing(df_time[variable], trend="add", seasonal=None)
            ajuste = modelo.fit()
            forecast = ajuste.forecast(periodo)

            st.markdown(f"#### 📈 Pronóstico de {variable} próximos {periodo} días")
            df_pred = df_time.copy()
            df_pred["Pronóstico"] = forecast
            fig_pred = px.line(df_pred, y=[variable, "Pronóstico"], labels={variable: variable},
                               title=f"Proyección de {variable}")
            st.plotly_chart(fig_pred, use_container_width=True)

            tendencia = "creciente" if forecast.iloc[-1] > ajuste.fittedvalues.iloc[-1] else "decreciente"
            st.info(f"📊 El modelo proyecta una tendencia **{tendencia}** para los próximos {periodo} días.")

            st.markdown("#### 🌀 Análisis espectral (FFT)")
            y_fft = df_time[variable] - df_time[variable].mean()
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
            st.warning("No hay suficientes datos para generar pronóstico o análisis espectral.")

else:
    st.warning("Por favor sube un archivo para comenzar.")








          
