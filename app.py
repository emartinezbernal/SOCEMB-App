import streamlit as st
import pandas as pd
import math

# --- 1. TABLAS TÉCNICAS ---
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
AREAS_MM2 = {"14 AWG": 8.96, "12 AWG": 11.68, "10 AWG": 15.67, "8 AWG": 28.19, "6 AWG": 46.90, "4 AWG": 62.77, "2 AWG": 85.93, "1/0": 143.42, "2/0": 175.48, "3/0": 214.38, "4/0": 263.42, "250 kcmil": 320.58, "300 kcmil": 371.87, "350 kcmil": 423.74, "400 kcmil": 476.32, "500 kcmil": 582.45}
CONDUIT_40 = {"1/2\"": 78, "3/4\"": 137, "1\"": 222, "1 1/4\"": 384, "1 1/2\"": 524, "2\"": 863, "2 1/2\"": 1232, "3\"": 1903, "4\"": 3271}

st.set_page_config(page_title="SOCEMB Engineering", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

# --- 2. ENTRADAS ---
with st.sidebar:
    st.header("⚙️ Parámetros")
    nombre = st.text_input("Proyecto", "Alimentador-01")
    tipo_p = st.selectbox("Unidad", ["kVA", "kW"])
    val_p = st.number_input("Potencia", value=10.0)
    fp = st.slider("Factor de Potencia", 0.7, 1.0, 0.9)
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=2)
    fases = st.radio("Fases", [1, 3], index=1)
    dist = st.number_input("Distancia (m)", value=50)
    temp = st.slider("Temp. Ambiente (°C)", 30, 55, 40)

# --- 3. CÁLCULOS (Fórmulas Blindadas) ---
pkva = val_p if tipo_p == "kVA" else (val_p / fp)
k_fase = 1.732 if fases == 3 else 1.0
i_nom = (pkva * 1000) / (v * k_fase)
f_t = 0.91 if temp <= 35 else (0.88 if temp <= 40 else 0.82)
i_dis = (i_nom * 1.25) / f_t

# Selección de Calibre e ITCM
cal_fase = "N/A"
for cal, amp in TABLA_COBRE_75.items():
    if i_dis <= amp:
        cal_fase = cal
        break

itcm_list = [15, 20, 30, 40, 50, 60, 70, 80, 100, 125, 150, 175, 200, 225, 250, 300, 400]
itcm = next((x for x in itcm_list if x >= i_dis), 400)

# Tierra y Ducto
cal_tierra = "10 AWG" if itcm <= 60 else ("8 AWG" if itcm <= 100 else "6 AWG")
area_c = (AREAS_MM2.get(cal_fase, 15) * fases) + AREAS_MM2.get(cal_tierra, 15)
tubo = next((t for t, cap in sorted(CONDUIT_40.items(), key=lambda x: x[1]) if area_c <= cap), "N/A")

# --- 4. RESULTADOS ---
st.info(f"Carga: **{round(pkva,2)} kVA** | Corriente Nominal: **{round(i_nom,2)} A**")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Corriente Diseño", f"{round(i_dis,2)} A")
    st.success(f"**Fases:** {fases}x {cal_fase}")
with c2:
    st.metric("Protección", f"{itcm} A")
    st.info(f"**Tubería:** {tubo}")
with c3:
    vd = (k_fase * i_nom * dist * 0.0028) / v * 100
    st.metric("Caída Tensión", f"{round(vd,2)} %")
    st.write("✅ Dentro de Norma" if vd <= 3 else "⚠️ Revisar VD")
