import streamlit as st
import pandas as pd
import math
from datetime import datetime

# --- 1. DATOS TÉCNICOS (NOM-001-SEDE) ---
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
ORDEN_CALIBRES = ["14 AWG", "12 AWG", "10 AWG", "8 AWG", "6 AWG", "4 AWG", "2 AWG", "1/0", "2/0", "3/0", "4/0", "250 kcmil", "300 kcmil", "350 kcmil", "400 kcmil", "500 kcmil"]
RES_OHM_KM = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "300 kcmil": 0.15, "350 kcmil": 0.13, "400 kcmil": 0.11, "500 kcmil": 0.089}
AREAS_MM2 = {"14 AWG": 8.96, "12 AWG": 11.68, "10 AWG": 15.67, "8 AWG": 28.19, "6 AWG": 46.90, "4 AWG": 62.77, "2 AWG": 85.93, "1/0": 143.42, "2/0": 175.48, "3/0": 214.38, "4/0": 263.42, "250 kcmil": 320.58, "300 kcmil": 371.87, "350 kcmil": 423.74, "400 kcmil": 476.32, "500 kcmil": 582.45}
CONDUIT_40 = {"1/2\"": 78, "3/4\"": 137, "1\"": 222, "1 1/4\"": 384, "1 1/2\"": 524, "2\"": 863, "3\"": 1903}

st.set_page_config(page_title="SOCEMB Pro", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Pro")

# --- 2. ENTRADAS ---
with st.sidebar:
    st.header("📋 Datos del Circuito")
    c_tag = st.text_input("Tag del Circuito", "C-01")
    c_origen = st.text_input("Origen", "CCM-01")
    c_destino = st.text_input("Destino", "Motor-101")
    
    st.header("⚙️ Parámetros Eléctricos")
    tipo_canal = st.radio("Tipo de Canalización", ["Tubo Conduit", "Charola (Cable Tray)"])
    tipo_p = st.selectbox("Unidad", ["kW", "kVA"])
    val_p = st.number_input("Valor", value=15.0)
    fp = st.slider("FP", 0.70, 1.0, 0.90)
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=2)
    fases = st.radio("Fases", [1, 3], index=1)
    dist = st.number_input("Distancia (m)", value=40)

# --- 3. CÁLCULOS ---
pkva = val_p / fp if tipo_p == "kW" else val_p
k_vd = 2.0 if fases == 1 else 1.732
i_nom = (pkva * 1000) / (v * (1.732 if fases == 3 else 1.0))

# Ajuste por canalización (Art. 310-15 / 392)
# En charola permitimos un factor un poco más holgado si hay espacio
f_ajuste = 0.85 if tipo_canal == "Charola (Cable Tray)" else 0.80
i_dis = (i_nom * 1.25) / f_ajuste

# Selección por Ampacidad
cal_base = next((c for c in ORDEN_CALIBRES if i_dis <= TABLA_COBRE_75[c]), "500 kcmil")

# Optimización VD
cal_final = cal_base
for cal in ORDEN_CALIBRES[ORDEN_CALIBRES.index(cal_base):]:
    r = RES_OHM_KM.get(cal, 0.089)
    vd = (k_vd * i_nom * dist * r) / (v * 10)
    cal_final = cal
    if vd <= 3.0: break

vd_final = (k_vd * i_nom * dist * RES_OHM_KM.get(cal_final, 0.089)) / (v * 10)

# Canalización sugerida
if tipo_canal == "Tubo Conduit":
    area_tot = (AREAS_MM2.get(cal_final, 15) * (fases + 1))
    soporte = next((t for t, cap in sorted(CONDUIT_40.items(), key=lambda x: x[1]) if area_tot <= cap), "Revisar")
else:
    soporte = "Charola de Aluminio / Tipo Escalera"

# --- 4. RESULTADOS ---
st.info(f"Circuito: **{c_tag}** | {c_origen} ➔ {c_destino}")
c1, c2, c3 = st.columns(3)
with c1: st.success(f"**Conductor:** {cal_final} Cu")
with c2: st.metric("Caída de Tensión", f"{round(vd_final,2)} %")
with c3: st.info(f"**Soporte:** {soporte}")

# --- 5. MEMORIA DE CÁLCULO ---
st.markdown("---")
if st.button("📋 Generar Memoria de Cálculo"):
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    memoria = f"""MEMORIA DE CÁLCULO TÉCNICA - SOCEMB
-----------------------------------------------------------
FECHA: {fecha}
CIRCUITO: {c_tag} | {c_origen} -> {c_destino}

1. DATOS DE DISEÑO:
- Carga: {val_p} {tipo_p} ({pkva:.2f} kVA)
- Voltaje: {v} V | Fases: {fases}
- Método de Canalización: {tipo_canal}

2. ANÁLISIS ELÉCTRICO:
- Corriente Nominal: {i_nom:.2f} A
- Corriente de Diseño (Factor de Ajuste {f_ajuste}): {i_dis:.2f} A

3. ESPECIFICACIÓN:
- CONDUCTOR: {cal_final} AWG/kcmil Cobre 75°C
- CAÍDA DE TENSIÓN: {vd_final:.2f} % (Límite 3%)
- SOPORTE: {soporte}

4. CUMPLIMIENTO NORMATIVO:
- Basado en NOM-001-SEDE Art. 310 y Art. 392 (Charolas).
-----------------------------------------------------------
Ing. Ernesto Martínez B. - SOCEMB Ingeniería
"""
    st.text_area("Previsualización", memoria, height=350)
    st.download_button("📥 Descargar Reporte", memoria, f"Memoria_{c_tag}.txt")
