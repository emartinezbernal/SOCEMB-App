import streamlit as st
import pandas as pd
import math
from datetime import datetime

# --- 1. DATOS TÉCNICOS (NOM-001-SEDE) ---
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
ORDEN_CALIBRES = ["14 AWG", "12 AWG", "10 AWG", "8 AWG", "6 AWG", "4 AWG", "2 AWG", "1/0", "2/0", "3/0", "4/0", "250 kcmil", "300 kcmil", "350 kcmil", "400 kcmil", "500 kcmil"]
RES_OHM_KM = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "300 kcmil": 0.15, "350 kcmil": 0.13, "400 kcmil": 0.11, "500 kcmil": 0.089}

st.set_page_config(page_title="SOCEMB Pro", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Pro")

# --- 2. ENTRADAS ---
with st.sidebar:
    st.header("⚙️ Datos del Proyecto")
    proj_name = st.text_input("Nombre del Proyecto", "Alimentador-MareaMadre")
    tipo_p = st.selectbox("Unidad de Potencia", ["kW", "kVA"])
    val_p = st.number_input("Valor", value=10.0)
    fp = st.slider("Factor de Potencia", 0.70, 1.0, 0.90)
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=0)
    fases = st.radio("Fases", [1, 3], index=0)
    dist = st.number_input("Distancia (m)", value=30)

# --- 3. CÁLCULOS ---
pkva = val_p / fp if tipo_p == "kW" else val_p
k_vd = 2.0 if fases == 1 else 1.732
i_nom = (pkva * 1000) / (v * (1.732 if fases == 3 else 1.0))
i_dis = i_nom * 1.25

# Selección por Ampacidad
cal_base = "14 AWG"
for cal in ORDEN_CALIBRES:
    if i_dis <= TABLA_COBRE_75[cal]:
        cal_base = cal
        break

# Optimización VD
cal_final = cal_base
for cal in ORDEN_CALIBRES[ORDEN_CALIBRES.index(cal_base):]:
    r = RES_OHM_KM.get(cal, 0.089)
    vd = (k_vd * i_nom * dist * r) / (v * 10)
    cal_final = cal
    if vd <= 3.0: break

vd_final = (k_vd * i_nom * dist * RES_OHM_KM.get(cal_final, 0.089)) / (v * 10)

# --- 4. RESULTADOS EN PANTALLA ---
st.info(f"Carga: **{round(pkva,2)} kVA** | Corriente Nominal: **{round(i_nom,2)} A**")
c1, c2 = st.columns(2)
with c1:
    st.success(f"**Conductor Sugerido:** {cal_final}")
with c2:
    st.metric("Caída de Tensión", f"{round(vd_final,2)} %")

# --- 5. GENERACIÓN DE MEMORIA DE CÁLCULO ---
st.markdown("---")
if st.button("📋 Generar Memoria de Cálculo"):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    memoria = f"""MEMORIA DE CÁLCULO DE CONDUCTOR ELÉCTRICO - SOCEMB
-----------------------------------------------------------
FECHA: {fecha}
PROYECTO: {proj_name}

1. DATOS DE ENTRADA:
- Potencia: {val_p} {tipo_p}
- Factor de Potencia (FP): {fp}
- Voltaje: {v} V
- Fases: {fases}
- Distancia: {dist} m

2. CONVERSIÓN Y CORRIENTE:
- Potencia Aparente: {pkva:.2f} kVA
- I_nominal = (kVA * 1000) / (V * k) = {i_nom:.2f} A
- I_diseño (1.25 Factor Seguridad) = {i_dis:.2f} A

3. SELECCIÓN DE CONDUCTOR:
- Por Ampacidad (NOM-001): {cal_base}
- Por Caída de Tensión (<3%): {cal_final}
- Resistencia del Conductor: {RES_OHM_KM.get(cal_final)} Ohm/km

4. RESULTADO FINAL:
- Caída de Tensión Calculada: {vd_final:.2f} %
- CONDUCTOR SELECCIONADO: {cal_final} COPPER 75°C
-----------------------------------------------------------
Diseñado con SOCEMB Pro por: Ing. Ernesto Martínez B.
"""
    st.text_area("Previsualización del Reporte", memoria, height=300)
    st.download_button(label="📥 Descargar Reporte .TXT", data=memoria, file_name=f"Memoria_{proj_name}.txt", mime="text/plain")
