import streamlit as st
import pandas as pd
import io

# --- 1. BASE DE DATOS TÉCNICA OKONITE C-L-X (MODELO MC-HL) ---
# Configuración: 3 Conductores de Cobre + Tierra Simétrica (VFD)
# Aislamiento: X-Olene (XHHW-2) 90°C / Cubierta: Okoseal (PVC)
DATOS_OKONITE = {
    "14 AWG": {"60C": 15, "75C": 20, "90C": 25, "area": 206, "od": 16.3, "cat": "546-31-3403"},
    "12 AWG": {"60C": 20, "75C": 20, "90C": 30, "area": 239, "od": 17.5, "cat": "546-31-3453"},
    "10 AWG": {"60C": 30, "75C": 30, "90C": 40, "area": 271, "od": 18.6, "cat": "546-31-3503"},
    "8 AWG":  {"60C": 40, "75C": 50, "90C": 55, "area": 329, "od": 20.6, "cat": "571-31-3190"},
    "6 AWG":  {"60C": 55, "75C": 65, "90C": 75, "area": 413, "od": 22.9, "cat": "571-31-3191"},
    "4 AWG":  {"60C": 70, "75C": 85, "90C": 95, "area": 497, "od": 25.1, "cat": "571-31-3200"},
    "2 AWG":  {"60C": 95, "75C": 115, "90C": 130, "area": 645, "od": 28.7, "cat": "571-31-3204"},
    "1/0":    {"60C": 125, "75C": 150, "90C": 170, "area": 994, "od": 35.6, "cat": "571-31-3213"},
    "2/0":    {"60C": 145, "75C": 175, "90C": 195, "area": 1103, "od": 37.6, "cat": "571-31-3216"},
    "3/0":    {"60C": 165, "75C": 200, "90C": 225, "area": 1265, "od": 40.1, "cat": "571-31-3218"},
    "4/0":    {"60C": 195, "75C": 230, "90C": 260, "area": 1516, "od": 44.0, "cat": "571-31-3224"},
    "250 kcmil": {"60C": 215, "75C": 255, "90C": 290, "area": 1774, "od": 47.5, "cat": "571-31-3228"},
    "350 kcmil": {"60C": 260, "75C": 310, "90C": 350, "area": 2213, "od": 53.0, "cat": "571-31-3236"},
    "500 kcmil": {"60C": 320, "75C": 380, "90C": 430, "area": 2761, "od": 59.3, "cat": "571-31-3244"}
}

# Resistencias Ohm/km (Cobre @ 75°C) para Caída de Tensión
RES_CU = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "350 kcmil": 0.13, "500 kcmil": 0.089}

# Configuración de Charolas Peralte 4" (101.6 mm)
ANCHOS_CHAROLA_4IN = {6: 15484, 9: 23226, 12: 30968, 18: 46451, 24: 61935, 30: 77419, 36: 92903}

st.set_page_config(page_title="SOCEMB: Okonite Selection Pro", layout="wide")

if 'db' not in st.session_state: st.session_state.db = []

st.title("⚡ SOCEMB: Ingeniería de Selección Okonite C-L-X")
st.markdown("### Configuración del Cable: Tipo MC-HL (XHHW-2) con Armadura de Aluminio")

# --- 2. ENTRADA DE DATOS ---
with st.sidebar:
    st.header("📋 Datos del Circuito")
    tag = st.text_input("Tag", "M-101")
    charola_id = st.text_input("ID Charola", "CH-A-01")
    hp = st.number_input("Potencia (HP)", value=10.0)
    voltaje = st.selectbox("Voltaje (V)", [440, 460, 480], index=1)
    dist = st.number_input("Distancia (m)", value=50)
    
    st.header("🌍 Factores NOM")
    t_amb = st.select_slider("Temp. Ambiente (°C)", options=[30, 35, 40, 45, 50], value=30)
    agrup = st.number_input("Conductores en Charola", value=3)

# --- 3. PROCESO DE SELECCIÓN ---
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)

i_nom = (hp * 746) / (voltaje * 1.732 * 0.85 * 0.90)
i_dis = i_nom * 1.25

def motor_seleccion():
    for cal, d in DATOS_OKONITE.items():
        lim_term = d["60C"] if i_dis <= 100 else d["75C"]
        cap_corregida = d["90C"] * f_t * f_a
        
        if i_dis <= lim_term and i_dis <= cap_corregida:
            vd = (1.732 * i_nom * dist * RES_CU[cal]) / (voltaje * 10)
            if vd <= 3.0:
                return cal, d["cat"], round(vd, 2)
    return "500 kcmil", "571-31-3244", 0

calibre, cat_num, vd_final = motor_seleccion()

# --- 4. PANEL DE RESULTADOS ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Calibre Seleccionado", calibre)
    st.write(f"**N° Catálogo:** {cat_num}")
    st.write(f"**Configuración:** 3/C Cu + Tierra Simétrica")
with col2:
    st.metric("Corriente Diseño", f"{round(i_dis, 2)} A")
    st.write(f"**Caída de Tensión:** {vd_final}%")

if st.button("➕ Registrar en Schedule"):
    st.session_state.db.append({
        "TAG": tag, "CHAROLA": charola_id, "CALIBRE": calibre, 
        "CATÁLOGO": cat_num, "OD (mm)": DATOS_OKONITE[calibre]["od"],
        "ÁREA (mm2)": DATOS_OKONITE[calibre]["area"]
    })

# --- 5. LÓGICA DE CHAROLA (MONOCAPA NOM-001) ---
if st.session_state.db:
    df = pd.DataFrame(st.session_state.db)
    st.subheader("📊 Análisis de Trayectorias (Criterio de Diámetros)")
    
    for ch_name, group in df.groupby("CHAROLA"):
        # Separar por regla de calibre
        grandes = group[group["CALIBRE"].str.contains("kcmil|1/0|2/0|3/0|4/0")]
        pequenos = group[~group["CALIBRE"].str.contains("kcmil|1/0|2/0|3/0|4/0")]
        
        ancho_req_mm = grandes["OD (mm)"].sum()
        area_req_mm2 = pequenos["ÁREA (mm2)"].sum()
        
        # Validación de ancho físico
        st.write(f"**Charola: {ch_name}**")
        st.write(f"- Ancho ocupado por cables $\
