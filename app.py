import streamlit as st
import pandas as pd
import math

# BASES DE DATOS SOCEMB
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255}
IEEE_9 = {"14 AWG": {"R": 3.1, "X": 0.058}, "12 AWG": {"R": 2.0, "X": 0.054}, "10 AWG": {"R": 1.2, "X": 0.050}, "8 AWG": {"R": 0.78, "X": 0.052}, "6 AWG": {"R": 0.49, "X": 0.051}, "4 AWG": {"R": 0.31, "X": 0.048}, "2 AWG": {"R": 0.19, "X": 0.045}, "1/0": {"R": 0.12, "X": 0.044}, "2/0": {"R": 0.10, "X": 0.043}, "3/0": {"R": 0.077, "X": 0.042}, "4/0": {"R": 0.062, "X": 0.041}, "250 kcmil": {"R": 0.052, "X": 0.041}}
AREAS = {"14 AWG": 8.96, "12 AWG": 11.68, "10 AWG": 15.67, "8 AWG": 28.19, "6 AWG": 46.90, "4 AWG": 62.77, "2 AWG": 85.93, "1/0": 143.42, "2/0": 175.48, "3/0": 214.38, "4/0": 263.42, "250 kcmil": 320.58}
CONDUIT_40 = {"1/2": 78, "3/4": 137, "1": 222, "1 1/4": 384, "1 1/2": 524, "2": 863, "3": 1903, "4": 3271}

st.set_page_config(page_title="SOCEMB Engineering", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

with st.sidebar:
    nombre = st.text_input("Nombre del Proyecto", "Alimentador-01")
    pkva = st.number_input("Potencia (kVA)", value=45.0)
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480])
    fases = st.radio("Fases", [1, 3], index=1)
    dist = st.number_input("Distancia (m)", value=50)
    temp = st.slider("Temp. Ambiente (°C)", 30, 50, 40)
    fp = st.slider("Factor de Potencia", 0.8, 1.0, 0.9)

k_fase = 1.732 if fases == 3 else 1.0
i_nom = (pkva * 1000) / (v * k_fase)
i_dis = (i_nom * 1.25) / (0.88 if temp <= 40 else 0.82)

cal_fase = "N/A"
for cal, amp in TABLA_COBRE_75.items():
    if i_dis <= amp:
        cal_fase = cal
        break

col1, col2 = st.columns(2)
col1.metric("Corriente Diseño", f"{round(i_dis,2)} A")
col1.success(f"**Calibre Fases:** {cal_fase}")

vd = (k_fase * i_nom * ((dist*3.28)/1000) * (IEEE_9.get(cal_fase, {"R":0})["R"]*fp)) / v * 100
col2.metric("Caída de Tensión", f"{round(vd,2)} %")