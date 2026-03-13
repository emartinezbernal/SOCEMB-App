import streamlit as st
import pandas as pd
import math

# --- 1. BASES DE DATOS TÉCNICAS ---
# Ampacidad Cobre 75°C (NOM-001-SEDE Tabla 310-15 b 16)
TABLA_COBRE_75 = {
    "14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, 
    "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, 
    "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, 
    "400 kcmil": 335, "500 kcmil": 380
}

# Áreas de conductores mm2 (THHN/THW) para cálculo de ducto
AREAS_MM2 = {
    "14 AWG": 8.96, "12 AWG": 11.68, "10 AWG": 15.67, "8 AWG": 28.19, 
    "6 AWG": 46.90, "4 AWG": 62.77, "2 AWG": 85.93, "1/0": 143.42, 
    "2/0": 175.48, "3/0": 214.38, "4/0": 263.42, "250 kcmil": 320.58,
    "300 kcmil": 371.87, "350 kcmil": 423.74, "400 kcmil": 476.32, "500 kcmil": 582.45
}

# Capacidad de tubería Conduit Pared Gruesa (40% ocupación según Norma)
CONDUIT_40 = {
    "1/2\"": 78, "3/4\"": 137, "1\"": 222, "1 1/4\"": 384, 
    "1 1/2\"": 524, "2\"": 863, "2 1/2\"": 1232, "3\"": 1903, "4\"": 3271
}

# --- 2. CONFIGURACIÓN DE LA INTERFAZ ---
st.set_page_config(page_title="SOCEMB Engineering", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

# --- 3. BARRA LATERAL (INPUTS) ---
with st.sidebar:
    st.header("⚙️ Parámetros de Diseño")
    nombre = st.text_input("Nombre del Proyecto", "Alimentador-01")
    
    tipo_potencia = st.selectbox("Tipo de Carga", ["kVA (Aparente)", "kW (Activa)"])
    valor_p = st.number_input("Valor de Potencia", value=10.0, step=1.0)
    fp = st.slider("Factor de Potencia (FP)", 0.70, 1.0, 0.90)
    
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=2)
    fases = st.radio("Fases", [1, 3], index=1)
    dist = st.number_input("Distancia (m)", value=50, step=5)
    temp = st.slider("Temp. Ambiente (°C)", 30, 55, 40)

# --- 4. MOTOR DE CÁLCULO ---
# Convertir a kVA si es necesario
pkva = valor_p if "kVA" in tipo_potencia else (valor_p / fp)

k_fase = 1.732 if fases == 3 else 1.0
i_nom = (pkva * 1000) /
