import streamlit as st
import pandas as pd
import io
import math

# --- 1. BASE DE DATOS TÉCNICA OKONITE C-L-X (Cu/Al) ---
# Datos: Ampacidades (60/75/90°C), Diámetro Exterior (mm) y Área Transversal (mm2)
DATOS_OKONITE = {
    "14 AWG": {"60C": 15, "75C": 20, "90C": 25, "area": 206, "od": 16.3},
    "12 AWG": {"60C": 20, "75C": 20, "90C": 30, "area": 239, "od": 17.5},
    "10 AWG": {"60C": 30, "75C": 30, "90C": 40, "area": 271, "od": 18.6},
    "8 AWG":  {"60C": 40, "75C": 50, "90C": 55, "area": 329, "od": 20.6},
    "6 AWG":  {"60C": 55, "75C": 65, "90C": 75, "area": 413, "od": 22.9},
    "4 AWG":  {"60C": 70, "75C": 85, "90C": 95, "area": 497, "od": 25.1},
    "2 AWG":  {"60C": 95, "75C": 115, "90C": 130, "area": 645, "od": 28.7},
    "1/0":    {"60C": 125, "75C": 150, "90C": 170, "area": 994, "od": 35.6},
    "2/0":    {"60C": 145, "75C": 175, "90C": 195, "area": 1103, "od": 37.6},
    "3/0":    {"60C": 165, "75C": 200, "90C": 225, "area": 1265, "od": 40.1},
    "4/0":    {"60C": 195, "75C": 230, "90C": 260, "area": 1516, "od": 44.0},
    "250 kcmil": {"60C": 215, "75C": 255, "90C": 290, "area": 1774, "od": 47.5},
    "350 kcmil": {"60C": 260, "75C": 310, "90C": 350, "area": 2213, "od": 53.0},
    "500 kcmil": {"60C": 320, "75C": 380, "90C": 430, "area": 2761, "od": 59.3}
}

# Resistencias para Caída de Tensión (Ohm/km - Cobre)
RES_CU = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "350 kcmil": 0.13, "500 kcmil": 0.089}

# Áreas útiles charolas Peralte 4" (mm2) - Límite NOM 40%
ANCHOS_CHAROLA_4IN = {6: 15484, 9: 23226, 12: 30968, 18: 46451, 24: 61935, 30: 77419, 36: 92903}

st.set_page_config(page_title="SOCEMB Engineering Pro", layout="wide")

if 'db' not in st.session_state:
    st.session_state.db = []

st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral (NOM-001 / Okonite C-L-X)")

# --- 2. ENTRADA DE DATOS (SIDEBAR) ---
with st.sidebar:
    st.header("📋 Datos del Proyecto")
    tag = st.text_input("Tag del Circuito", "M-101")
    charola_id = st.text_input("ID Charola", "CH-A-01")
    
    st.header("⚙️ Parámetros Eléctricos")
    hp = st.number_input("Potencia (HP)", value=10.0)
    v = st.selectbox("Voltaje (V)", [220, 440, 460, 480], index=2)
    dist = st.number_input("Longitud (m)", value=50)
    
    st.header("🌍 Condiciones de Instalación (Derating)")
    temp_amb = st.select_slider("Temp. Ambiente (°C)", options=[30, 35, 40, 45, 50], value=30)
    agrup = st.number_input("Conductores portadores de corriente", value=3)

# --- 3. MOTOR DE CÁLCULO SOCEMB ---
# Factores de corrección NOM
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(temp_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)

i_nom = (hp * 746) / (v * 1.732 * 0.85 * 0.90)
i_dis = i_nom * 1.25

def validar_cable(corriente):
    for cal, d in DATOS_OKONITE.items():
        # Criterio 1: Capacidad de la Terminal (NOM 110-14c)
        limite_terminal = d["60C"] if corriente <= 100 else d["75C"]
        
        # Criterio 2: Capacidad Ajustada (Derating sobre 90°C)
        capacidad_corregida = d["90C"] * f_t * f_a
        
        if corriente <= limite_terminal and corriente <= capacidad_corregida:
            # Validar Caída de Tensión (Límite 3%)
            vd = (1.732 * i_nom * dist * RES_CU[cal]) / (v * 10)
            if vd <= 3.0:
                return cal, round(vd, 2), limite_terminal, round(capacidad_corregida, 2)
    return "500 kcmil", 0, 0, 0

calibre, vd_final, lim_term, cap_corr = validar_cable(i_dis)

# --- 4. INTERFAZ DE RESULTADOS ---
col1, col2, col3 = st.columns(3)
col1.metric("Corriente Diseño", f"{round(i_dis, 2)} A")
col2.metric("Calibre Okonite", calibre)
col3.metric("Caída Tensión", f"{vd_final}%")

with st.expander("Ver Análisis de Cumplimiento NOM"):
    st.write(f"**Límite Terminal (60/75°C):** {lim_term} A")
    st.write(
