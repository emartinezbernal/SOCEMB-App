import streamlit as st
import pandas as pd
import math

# --- 1. TABLAS TÉCNICAS ---
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
ORDEN_CALIBRES = ["14 AWG", "12 AWG", "10 AWG", "8 AWG", "6 AWG", "4 AWG", "2 AWG", "1/0", "2/0", "3/0", "4/0", "250 kcmil", "300 kcmil", "350 kcmil", "400 kcmil", "500 kcmil"]
AREAS_MM2 = {"14 AWG": 8.96, "12 AWG": 11.68, "10 AWG": 15.67, "8 AWG": 28.19, "6 AWG": 46.90, "4 AWG": 62.77, "2 AWG": 85.93, "1/0": 143.42, "2/0": 175.48, "3/0": 214.38, "4/0": 263.42, "250 kcmil": 320.58, "300 kcmil": 371.87, "350 kcmil": 423.74, "400 kcmil": 476.32, "500 kcmil": 582.45}
CONDUIT_40 = {"1/2\"": 78, "3/4\"": 137, "1\"": 222, "1 1/4\"": 384, "1 1/2\"": 524, "2\"": 863, "2 1/2\"": 1232, "3\"": 1903, "4\"": 3271}

st.set_page_config(page_title="SOCEMB Pro", layout="wide")
st.title("⚡ SOCEMB: Ingeniería Eléctrica Pro")

# --- 2. ENTRADAS ---
with st.sidebar:
    st.header("⚙️ Configuración")
    nombre = st.text_input("Proyecto", "Alimentador-01")
    tipo_p = st.selectbox("Unidad", ["kVA", "kW"])
    val_p = st.number_input("Potencia", value=10.0)
    fp = st.slider("Factor de Potencia", 0.7, 1.0, 0.9)
    v = st.selectbox("Voltaje (V)", [127, 220, 440, 480], index=0)
    fases = st.radio("Fases", [1, 3], index=0)
    dist = st.number_input("Distancia (m)", value=50)
    temp = st.slider("Temp. Ambiente (°C)", 30, 55, 40)
    opt_vd = st.checkbox("Optimizar para < 3% VD", value=True)

# --- 3. CÁLCULOS ---
pkva = val_p if tipo_p == "kVA" else (val_p / fp)
k_fase = 1.732 if fases == 3 else 2.0 # 2.0 para monofásico 127V
i_nom = (pkva * 1000) / (v * (1.732 if fases == 3 else 1.0))
f_t = 0.91 if temp <= 35 else (0.88 if temp <= 40 else 0.82)
i_dis = (i_nom * 1.25) / f_t

# Selección por Ampacidad
cal_final = "N/A"
for cal in ORDEN_CALIBRES:
    if i_dis <= TABLA_COBRE_75[cal]:
        cal_final = cal
        break

# Selección de Interruptor
itcm_list = [15, 20, 30, 40, 50, 60, 70, 80, 100, 125, 150, 175, 200, 225, 250, 300, 400, 500]
itcm = next((x for x in itcm_list if x >= i_dis), 500)

# Bucle de Optimización por Caída de Tensión
if opt_vd and cal_final != "N/A":
    while True:
        vd = (k_fase * i_nom * dist * 0.0028) / v * 100
        if vd <= 3.0 or cal_final == "500 kcmil":
            break
        idx = ORDEN_CALIBRES.index(cal_final)
        if idx < len(ORDEN_CALIBRES) - 1:
            cal_final = ORDEN_CALIBRES[idx + 1]
        else:
            break

# Conductor de Tierra
if itcm <= 60: cal_tierra = "10 AWG"
elif itcm <= 100: cal_tierra = "8 AWG"
elif itcm <= 200: cal_tierra = "6 AWG"
else: cal_tierra = "4 AWG"

# Tubería
area_c = (AREAS_MM2.get(cal_final, 15) * fases) + AREAS_MM2.get(cal_tierra, 15)
tubo = next((t for t, cap in sorted(CONDUIT_40.items(), key=lambda x: x[1]) if area_c <= cap), "Revisar")

# --- 4. RESULTADOS ---
st.info(f"Carga: **{round(pkva,2)} kVA** | Corriente Nominal: **{round(i_nom,2)} A**")
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Corriente Diseño", f"{round(i_dis,2)} A")
    st.success(f"**Calibre Fases:** {cal_final}")
    st.caption(f"Tierra: {cal_tierra}")
with c2:
    st.metric("Protección", f"{itcm} A")
    st.info(f"**Canalización:** {tubo}")
with c3:
    vd_final = (k_fase * i_nom * dist * 0.0028) / v * 100
    st.metric("Caída Tensión", f"{round(vd_final,2)} %")
    if vd_final > 3: st.error("⚠️ Excede 3%")
    else: st.success("✅ Voltaje Óptimo")
