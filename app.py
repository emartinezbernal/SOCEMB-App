import streamlit as st
import pandas as pd
import math

# --- 1. DATOS TÉCNICOS (NOM-001-SEDE Tabla 9 y Tabla 310-15) ---
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
ORDEN_CALIBRES = ["14 AWG", "12 AWG", "10 AWG", "8 AWG", "6 AWG", "4 AWG", "2 AWG", "1/0", "2/0", "3/0", "4/0", "250 kcmil", "300 kcmil", "350 kcmil", "400 kcmil", "500 kcmil"]

# Resistencia efectiva (Ohm/km) para conductores en tubo de acero
RES_OHM_KM = {
    "14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, 
    "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, 
    "4/0": 0.20, "250 kcmil": 0.17, "300 kcmil": 0.15, "350 kcmil": 0.13, 
    "400 kcmil": 0.11, "500 kcmil": 0.089
}

st.set_page_config(page_title="SOCEMB Pro", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Pro")

# --- 2. ENTRADAS ---
with st.sidebar:
    st.header("⚙️ Parámetros de Carga")
    tipo_p = st.selectbox("Unidad de Potencia", ["kW (Activa)", "kVA (Aparente)"])
    val_p = st.number_input(f"Valor en {tipo_p}", value=10.0)
    
    # El Factor de Potencia solo es editable si la unidad es kW
    fp = st.slider("Factor de Potencia (cos φ)", 0.70, 1.0, 0.90)
    
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=0)
    fases = st.radio("Fases", [1, 3], index=0)
    dist = st.number_input("Distancia (m)", value=30)
    opt_vd = st.checkbox("Optimizar Calibre para VD < 3%", value=True)

# --- 3. LÓGICA DE CONVERSIÓN Y CÁLCULO ---
# Si es kW, convertimos a kVA usando el FP
pkva = val_p / fp if tipo_p == "kW (Activa)" else val_p

# Corriente Nominal (A)
i_nom = (pkva * 1000) / (v * (1.732 if fases == 3 else 1.0))
i_dis = i_nom * 1.25 # Factor de seguridad 125%

# Factor de distancia (K)
k_vd = 2.0 if fases == 1 else 1.732

# Selección por Ampacidad
cal_final = "14 AWG"
for cal in ORDEN_CALIBRES:
    if i_dis <= TABLA_COBRE_75[cal]:
        cal_final = cal
        break

# Optimización por Caída de Tensión (VD)
if opt_vd:
    for cal in ORDEN_CALIBRES[ORDEN_CALIBRES.index(cal_final):]:
        r = RES_OHM_KM.get(cal, 0.089)
        # Fórmula VD% = (K * I * L * R * 100) / (V * 1000) -> Simplificado abajo:
        vd = (k_vd * i_nom * dist * r) / (v * 10)
        cal_final = cal
        if vd <= 3.0:
            break

# --- 4. RESULTADOS ---
st.info(f"Carga Resultante: **{round(pkva,2)} kVA** | Corriente Nominal: **{round(i_nom,2)} A**")

c1, c2 = st.columns(2)
with c1:
    st.metric("Corriente Diseño (1.25)", f"{round(i_dis,2)} A")
    st.success(f"**Calibre Sugerido:** {cal_final}")

with c2:
    r_final = RES_OHM_KM.get(cal_final, 0.089)
    vd_final = (k_vd * i_nom * dist * r_final) / (v * 10)
    st.metric("Caída de Tensión", f"{round(vd_final,2)} %")
    if vd_final > 3.0:
        st.error("⚠️ Fuera de norma (>3%)")
    else:
        st.success("✅ Dentro de norma")
