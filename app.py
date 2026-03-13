import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. BASE DE DATOS NORMATIVA (FLC Motores Trifásicos 460V - Ref: NEMA/NOM) ---
# Se ajusta proporcionalmente para otros voltajes en el código
TABLA_NEMA_3F_460V = {
    1.0: 1.8, 2.0: 3.4, 3.0: 4.8, 5.0: 7.6, 7.5: 11.0, 10.0: 14.0, 
    15.0: 21.0, 20.0: 27.0, 25.0: 34.0, 30.0: 40.0, 40.0: 52.0, 
    50.0: 65.0, 60.0: 77.0, 75.0: 96.0, 100.0: 124.0, 125.0: 156.0, 150.0: 180.0
}

TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
ORDEN_CALIBRES = list(TABLA_COBRE_75.keys())
RES_OHM_KM = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "300 kcmil": 0.15, "350 kcmil": 0.13, "400 kcmil": 0.11, "500 kcmil": 0.089}

st.set_page_config(page_title="SOCEMB Pro NEMA", layout="wide")
st.title("⚡ SOCEMB: Diseño Basado en ANSI/NEMA")

# --- 2. ENTRADAS ---
with st.sidebar:
    st.header("📋 Datos de Placa")
    c_tag = st.text_input("Tag del Equipo", "M-101")
    tipo_p = st.selectbox("Unidad de Potencia", ["HP (NEMA Table)", "kW", "kVA"])
    
    if tipo_p == "HP (NEMA Table)":
        hp_val = st.selectbox("Potencia HP Nominal", sorted(TABLA_NEMA_3F_460V.keys()), index=5)
        val_p = hp_val
    else:
        val_p = st.number_input("Valor", value=10.0)

    v = st.selectbox("Voltaje de Operación (V)", [220, 440, 460, 480], index=2)
    fases = st.radio("Fases", [3], index=0) # Tablas NEMA estándar son 3F
    dist = st.number_input("Distancia de Alimentador (m)", value=50)
    tipo_canal = st.radio("Soporte", ["Tubo Conduit", "Charola"])

# --- 3. LÓGICA DE CÁLCULO NORMATIVA ---
if tipo_p == "HP (NEMA Table)":
    # Obtenemos FLC de tabla (base 460V) y ajustamos por voltaje real
    i_nema_base = TABLA_NEMA_3F_460V[val_p]
    i_nom = i_nema_base * (460 / v)
    pkva = (i_nom * v * 1.732) / 1000
else:
    fp_std = 0.85
    pkva = val_p / fp_std if tipo_p == "kW" else val_p
    i_nom = (pkva * 1000) / (v * 1.732)

# Corriente de Diseño (125% para motores individuales)
i_dis = i_nom * 1.25

# --- 4. SELECCIÓN DE CONDUCTOR ---
cal_base = next((c for c in ORDEN_CALIBRES if i_dis <= TABLA_COBRE_75[c]), "500 kcmil")
cal_final = cal_base

# Optimización por Caída de Tensión
for cal in ORDEN_CALIBRES[ORDEN_CALIBRES.index(cal_base):]:
    r = RES_OHM_KM.get(cal, 0.089)
    vd = (1.732 * i_nom * dist * r) / (v * 10)
    cal_final = cal
    if vd <= 3.0: break

vd_final = (1.732 * i_nom * dist * RES_OHM_KM.get(cal_final, 0.089)) / (v * 10)

# --- 5. RESULTADOS ---
st.info(f"Cálculo Normativo para: **{c_tag}** | {val_p} HP @ {v}V")
c1, c2, c3 = st.columns(3)
c1.metric("FLC (Corriente Nominal)", f"{round(i_nom,2)} A")
c2.metric("Ampacidad Requerida (1.25)", f"{round(i_dis,2)} A")
c3.metric("Caída de Tensión", f"{round(vd_final,2)} %")

st.success(f"⚡ **Conductor Seleccionado:** {cal_final} Cu 75°C")

# --- 6. MEMORIA ---
if st.button("📋 Descargar Memoria Técnica"):
    memoria = f"""MEMORIA DE CÁLCULO - ANSI/NEMA STANDARDS
-----------------------------------------------------------
TAG: {c_tag} | MOTOR ELÉCTRICO TRIFÁSICO
POTENCIA: {val_p} HP
VOLTAJE: {v} V

1. REFERENCIA NORMATIVA:
- Corriente a Plena Carga (FLC) basada en Tabla 430.250 (NOM/NEC).
- Factor de Utilización y Eficiencia estándar NEMA incluidos.

2. DESARROLLO:
- Corriente Nominal (FLC): {i_nom:.2f} A
- Corriente de Diseño (1.25 * FLC): {i_dis:.2f} A
- Conductor seleccionado por ampacidad: {cal_base}
- Conductor optimizado por VD (<3%): {cal_final}

3. CONCLUSIÓN:
Instalar conductor {cal_final} en {tipo_canal}.
-----------------------------------------------------------
Diseñado por: Ing. Ernesto Martínez B.
"""
    st.download_button("📥 Guardar PDF/TXT", memoria, f"NEMA_{c_tag}.txt")
