import streamlit as st
import pandas as pd
from datetime import datetime
import io
import math

# --- 1. CONFIGURACIÓN DE DATOS SOCEMB ---
# Áreas de cables (mm2) según diámetros comerciales típicos Cu 75°C
AREAS_EXT_NOM = {"14 AWG": 8.9, "12 AWG": 11.6, "10 AWG": 15.6, "8 AWG": 28.1, "6 AWG": 46.9, "4 AWG": 62.7, "2 AWG": 85.9, "1/0": 143.4, "2/0": 175.4, "3/0": 214.3, "4/0": 263.4, "250 kcmil": 320.5, "500 kcmil": 582.4}

# Áreas para Corto Circuito (mm2 de sección transversal del conductor)
AREAS_MM2_CC = {"1/0": 53.49, "2/0": 67.43, "3/0": 85.01, "4/0": 107.2, "250 kcmil": 126.7, "300 kcmil": 152.0, "350 kcmil": 177.3, "400 kcmil": 202.7, "500 kcmil": 253.4}

# Áreas útiles de charolas con PERALTE 4" (101.6 mm)
# Cálculo: Ancho(mm) * 101.6mm
ANCHOS_CHAROLA_4IN = {
    6: 15484,  # 6"
    9: 23226,  # 9"
    12: 30968, # 12"
    18: 46451, # 18"
    24: 61935, # 24"
    30: 77419, # 30"
    36: 92903  # 36"
}

st.set_page_config(page_title="SOCEMB Engineering Pro", layout="wide")

if 'lista_circuitos' not in st.session_state:
    st.session_state.lista_circuitos = []

st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

# --- 2. INTERFAZ DE CAPTURA ---
with st.sidebar:
    st.header("📋 Identificación")
    c_tag = st.text_input("Tag del Circuito", "M-101")
    c_charola = st.text_input("ID Charola Origen", "CH-A-01")
    
    st.header("⚙️ Parámetros de Carga")
    tipo_p = st.selectbox("Unidad", ["HP (NEMA)", "kW", "kVA"])
    if tipo_p == "HP (NEMA)":
        from bases import TABLA_NEMA_3F_460V # Asumiendo que las tablas están accesibles
        val_p = st.selectbox("Valor HP", sorted(TABLA_NEMA_3F_460V.keys()), index=5)
    else:
        val_p = st.number_input("Valor", value=10.0)
    
    v = st.selectbox("Voltaje (V)", [220, 440, 460, 480], index=2)
    dist = st.number_input("Longitud (m)", value=50)

    st.header("🛡️ Corto Circuito")
    i_falla = st.number_input("I de Falla (kA)", value=10.0)
    t_falla = st.number_input("Tiempo (seg)", value=0.016, format="%.3f")

# --- 3. LÓGICA DE CÁLCULO (Omitida por brevedad, igual a la validada previa) ---
# [Aquí va la lógica de Corriente, VD y CC ya revisada]

# --- 4. REPORTE DE CHAROLAS (NOM-001 Art 392) ---
if st.session_state.lista_circuitos:
    df = pd.DataFrame(st.session_state.lista_circuitos)
    st.subheader("📋 Memoria de Llenado de Charolas (Peralte 4\")")
    
    rep_charola = df.groupby("CHAROLA")["ÁREA CABLE (mm2)"].sum().reset_index()
    
    def calc_ancho_nom(area_acum):
        for pulg, area_tot in ANCHOS_CHAROLA_4IN.items():
            if area_acum <= (area_tot * 0.40):
                return f"{pulg}\" ({pulg*25.4} mm)", f"{round((area_acum/(area_tot*0.4))*100,1)}%"
        return "SOBRESATURADA", "100%+"

    rep_charola[['Ancho Sugerido', 'Ocupación (%)']] = rep_charola['ÁREA CABLE (mm2)'].apply(lambda x: pd.Series(calc_ancho_nom(x)))
    st.table(rep_charola)
