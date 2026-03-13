import streamlit as st
import pandas as pd
import math

# --- 1. TABLAS TÉCNICAS (Valores Reales NOM-001) ---
# Ampacidad Cobre 75°C
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
ORDEN_CALIBRES = ["14 AWG", "12 AWG", "10 AWG", "8 AWG", "6 AWG", "4 AWG", "2 AWG", "1/0", "2/0", "3/0", "4/0", "250 kcmil", "300 kcmil", "350 kcmil", "400 kcmil", "500 kcmil"]

# Resistencia Ohm/km (Aproximada para ducto magnético)
RESISTENCIA_OHM_KM = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17}

st.set_page_config(page_title="SOCEMB Pro", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Pro")

# --- 2. ENTRADAS ---
with st.sidebar:
    st.header("⚙️ Configuración")
    val_p = st.number_input("Potencia (kW/kVA)", value=5.0)
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=0)
    fases = st.radio("Fases", [1, 3], index=0)
    dist = st.number_input("Distancia (m)", value=30)
    opt_vd = st.checkbox("Optimizar para < 3% VD", value=True)

# --- 3. CÁLCULOS ---
k_fase = 2.0 if fases == 1 else 1.732
i_nom = (val_p * 1000) / (v * (1.732 if fases == 3 else 1.0))
i_dis = i_nom * 1.25

# Selección inicial por Ampacidad
cal_final = "14 AWG"
for cal in ORDEN_CALIBRES:
    if i_dis <= TABLA_COBRE_75[cal]:
        cal_final = cal
        break

# Optimización por Caída de Tensión
if opt_vd:
    for cal in ORDEN_CALIBRES[ORDEN_CALIBRES.index(cal_final):]:
        r = RESISTENCIA_OHM_KM.get(cal, 0.15)
        # Fórmula: VD = (K * I * L * R) / (V * 10)  donde R es Ohm/km y L es metros
        vd = (k_fase * i_nom * dist * r) / (v * 10)
        cal_final = cal
        if vd <= 3.0:
            break

# --- 4. RESULTADOS ---
st.info(f"Corriente Nominal: **{round(i_nom,2)} A** | Corriente Diseño: **{round(i_dis,2)} A**")
c1, c2 = st.columns(2)
with c1:
    st.success(f"**Calibre Sugerido:** {cal_final}")
with c2:
    r_final = RESISTENCIA_OHM_KM.get(cal_final, 0.15)
    vd_final = (k_fase * i_nom * dist * r_final) / (v * 10)
    st.metric("Caída de Tensión Final", f"{round(vd_final,2)} %")
