import streamlit as st
import pandas as pd
import math

# --- BASES DE DATOS AMPLIADAS ---
TABLA_COBRE_75 = {
    "14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, 
    "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, 
    "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, 
    "500 kcmil": 380
}

# Áreas mm2 (Para cálculo de tubería)
AREAS_THHN = {"14 AWG": 8.96, "12 AWG": 11.68, "10 AWG": 15.67, "8 AWG": 28.19, "6 AWG": 46.90, "4 AWG": 62.77, "2 AWG": 85.93}

# Tubería Conduit Pared Gruesa (40% de ocupación)
CONDUIT_40 = {"1/2\"": 78, "3/4\"": 137, "1\"": 222, "1 1/4\"": 384, "1 1/2\"": 524, "2\"": 863}

st.set_page_config(page_title="SOCEMB Engineering", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Parámetros")
    nombre = st.text_input("Proyecto", "Alimentador-01")
    pkva = st.number_input("Potencia (kVA)", value=10.0)
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=2)
    fases = st.radio("Fases", [1, 3], index=1)
    dist = st.number_input("Distancia (m)", value=50)
    temp = st.slider("Temp (°C)", 30, 50, 40)

# --- CÁLCULOS ---
k_fase = 1.732 if fases == 3 else 1.0
i_nom = (pkva * 1000) / (v * k_fase)
# Factor de ajuste por temperatura simplificado
f_t = 0.88 if temp <= 40 else 0.82
i_dis = (i_nom * 1.25) / f_t

# 1. Selección de Calibre
cal_fase = "N/A"
for cal, amp in TABLA_COBRE_75.items():
    if i_dis <= amp:
        cal_fase = cal
        break

# 2. Selección de Interruptor (ITCM)
itcm_list = [15, 20, 30, 40, 50, 60, 70, 80, 100, 125, 150, 175, 200, 225, 250]
itcm = 15
for b in itcm_list:
    if b >= i_dis:
        itcm = b
        break

# 3. Cálculo de Tubería (Asumiendo 3 Fases + 1 Tierra)
area_tot = (AREAS_THHN.get(cal_fase, 15) * (fases + 1))
tubo = "1/2\""
for t, cap in CONDUIT_40.items():
    if area_tot <= cap:
        tubo = t
        break

# --- INTERFAZ DE RESULTADOS ---
st.markdown(f"### Reporte para: {nombre}")
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("Corriente Diseño", f"{round(i_dis,2)} A")
    st.success(f"**Conductores:** {fases}x {cal_fase}")

with c2:
    st.metric("Protección (ITCM)", f"{itcm} A")
    st.info(f"**Tubería:** {tubo} Conduit")

with c3:
    vd = (k_fase * i_nom * dist * 0.003) / v * 100 # Estimado rápido
    st.metric("Caída de Tensión", f"{round(vd,2)} %")
    if vd > 3: st.error("⚠️ Excede el 3%")
    else: st.write("✅ Voltaje dentro de norma")

st.markdown("---")
st.caption("SOCEMB v3.0 | Basado en NOM-001-SEDE / NEC")
