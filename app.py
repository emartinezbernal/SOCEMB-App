import streamlit as st
import pandas as pd
import math

# 1. TABLAS AMPLIADAS (Hasta 500 kcmil)
TABLA_COBRE_75 = {
    "14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, 
    "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, 
    "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, 
    "400 kcmil": 335, "500 kcmil": 380
}

# Reactancia y Resistencia (IEEE Std 141 - Tabla 9)
IEEE_9 = {
    "250 kcmil": {"R": 0.052, "X": 0.041}, "300 kcmil": {"R": 0.044, "X": 0.041},
    "350 kcmil": {"R": 0.038, "X": 0.040}, "400 kcmil": {"R": 0.033, "X": 0.040},
    "500 kcmil": {"R": 0.027, "X": 0.039}
}

st.set_page_config(page_title="SOCEMB Engineering", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

# --- ENTRADAS ---
with st.sidebar:
    st.header("⚙️ Parámetros")
    nombre = st.text_input("Proyecto", "Alimentador-01")
    pkva = st.number_input("Potencia (kVA)", value=45.0)
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=2) # Puse 440 por defecto
    fases = st.radio("Fases", [1, 3], index=1)
    dist = st.number_input("Distancia (m)", value=50)
    temp = st.slider("Temp (°C)", 30, 50, 40)
    fp = st.slider("Factor de Potencia", 0.8, 1.0, 0.9)

# --- CÁLCULOS ---
k_fase = 1.732 if fases == 3 else 1.0
i_nom = (pkva * 1000) / (v * k_fase)
i_dis = (i_nom * 1.25) / (0.88 if temp <= 40 else 0.82)

# Selección de Calibre
cal_fase = "N/A (Excede Tabla)"
for cal, amp in TABLA_COBRE_75.items():
    if i_dis <= amp:
        cal_fase = cal
        break

# --- RESULTADOS ---
col1, col2 = st.columns(2)
col1.metric("Corriente Diseño", f"{round(i_dis,2)} A")
if "N/A" in cal_fase:
    col1.error(f"⚠️ {cal_fase}")
else:
    col1.success(f"✅ Calibre Fases: {cal_fase}")

# Cálculo VD si hay calibre
if cal_fase != "N/A (Excede Tabla)":
    r_x = IEEE_9.get(cal_fase, {"R": 0.05, "X": 0.04}) # Valores genéricos si no está en IEEE_9
    vd = (k_fase * i_nom * ((dist*3.28)/1000) * (r_x["R"]*fp + r_x["X"]*math.sin(math.acos(fp)))) / v * 100
    col2.metric("Caída de Tensión", f"{round(vd,2)} %")
