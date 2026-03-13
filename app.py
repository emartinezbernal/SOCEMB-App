import streamlit as st
import pandas as pd
from datetime import datetime

# --- 1. BASES DE DATOS (NEMA / NOM-001) ---
TABLA_NEMA_3F_460V = {
    1.0: 1.8, 2.0: 3.4, 3.0: 4.8, 5.0: 7.6, 7.5: 11.0, 10.0: 14.0, 
    15.0: 21.0, 20.0: 27.0, 25.0: 34.0, 30.0: 40.0, 40.0: 52.0, 
    50.0: 65.0, 60.0: 77.0, 75.0: 96.0, 100.0: 124.0, 125.0: 156.0, 150.0: 180.0
}

TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
ORDEN_CALIBRES = list(TABLA_COBRE_75.keys())
RES_OHM_KM = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "300 kcmil": 0.15, "350 kcmil": 0.13, "400 kcmil": 0.11, "500 kcmil": 0.089}

st.set_page_config(page_title="SOCEMB Engineering Pro", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

# --- 2. ENTRADAS (TAG, ORIGEN, DESTINO) ---
with st.sidebar:
    st.header("📋 Identificación del Proyecto")
    c_tag = st.text_input("Tag del Circuito", "M-101")
    c_origen = st.text_input("Origen (De:)", "CCM-01")
    c_destino = st.text_input("Destino (A:)", "Bomba de Proceso")
    
    st.header("⚙️ Parámetros de Potencia")
    tipo_p = st.selectbox("Unidad de Potencia", ["HP (NEMA)", "kW", "kVA"])
    
    if tipo_p == "HP (NEMA)":
        val_p = st.selectbox("Potencia HP", sorted(TABLA_NEMA_3F_460V.keys()), index=5)
    else:
        val_p = st.number_input("Valor", value=10.0)
    
    fp = st.slider("Factor de Potencia", 0.70, 1.0, 0.85)
    v = st.selectbox("Voltaje (V)", [220, 440, 460, 480], index=2)
    dist = st.number_input("Distancia (m)", value=50)
    tipo_canal = st.radio("Soporte", ["Tubo Conduit", "Charola"])

# --- 3. LÓGICA DE CÁLCULO ---
if tipo_p == "HP (NEMA)":
    i_nom = TABLA_NEMA_3F_460V[val_p] * (460 / v)
    pkva = (i_nom * v * 1.732) / 1000
else:
    pkva = val_p / fp if tipo_p == "kW" else val_p
    i_nom = (pkva * 1000) / (v * 1.732)

i_dis = i_nom * 1.25
f_ajuste = 0.85 if tipo_canal == "Charola" else 0.80
i_ajustada = i_dis / f_ajuste

# Selección y VD
cal_base = next((c for c in ORDEN_CALIBRES if i_ajustada <= TABLA_COBRE_75[c]), "500 kcmil")
cal_final = cal_base
for cal in ORDEN_CALIBRES[ORDEN_CALIBRES.index(cal_base):]:
    r = RES_OHM_KM.get(cal, 0.089)
    vd = (1.732 * i_nom * dist * r) / (v * 10)
    cal_final = cal
    if vd <= 3.0: break

vd_final = (1.732 * i_nom * dist * RES_OHM_KM.get(cal_final, 0.089)) / (v * 10)

# --- 4. RESULTADOS ---
st.info(f"Circuito: **{c_tag}** | {c_origen} ➔ {c_destino}")
c1, c2, c3 = st.columns(3)
c1.metric("FLC (Corriente)", f"{round(i_nom,2)} A")
c2.metric("Ampacidad Requerida", f"{round(i_ajustada,2)} A")
c3.metric("Caída de Tensión", f"{round(vd_final,2)} %")

st.success(f"⚡ **Conductor Recomendado:** {cal_final} Cu 75°C en {tipo_canal}")

# --- 5. REPORTE ---
if st.button("📋 Generar Memoria de Cálculo"):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    memoria = f"""MEMORIA DE CÁLCULO TÉCNICA - SOCEMB
-----------------------------------------------------------
PROYECTO: {c_tag}
ORIGEN: {c_origen} | DESTINO: {c_destino}
FECHA: {fecha}

1. DATOS DE DISEÑO:
- Potencia: {val_p} {tipo_p}
- Voltaje: {v} V | Fases: 3F
- Distancia: {dist} m | Soporte: {tipo_canal}

2. ANÁLISIS NORMATIVO:
- FLC (Tabla 430.250 / NEMA): {i_nom:.2f} A
- Corriente Ajustada (1.25 / {f_ajuste}): {i_ajustada:.2f} A

3. RESULTADOS:
- Calibre por Ampacidad: {cal_base}
- Calibre Optimizado por VD: {cal_final}
- Caída de Tensión Final: {vd_final:.2f} %

-----------------------------------------------------------
Ing. Ernesto Martínez B. - SOCEMB Ingeniería
"""
    st.text_area("Previsualización", memoria, height=350)
    st.download_button("📥 Descargar Reporte", memoria, f"SOCEMB_{c_tag}.txt")
