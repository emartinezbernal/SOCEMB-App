import streamlit as st
import pandas as pd
import io

# --- 1. BASE DE DATOS TÉCNICA OKONITE C-L-X (3/C + TIERRA INTEGRADA) ---
DATOS_OKONITE = {
    "14 AWG": {"60C": 15, "75C": 20, "90C": 25, "area": 206, "od_mm": 16.3, "od_in": 0.64, "cat": "546-31-3403", "grd": "1x#14"},
    "12 AWG": {"60C": 20, "75C": 20, "90C": 30, "area": 239, "od_mm": 17.5, "od_in": 0.69, "cat": "546-31-3453", "grd": "1x#12"},
    "10 AWG": {"60C": 30, "75C": 30, "90C": 40, "area": 271, "od_mm": 18.6, "od_in": 0.73, "cat": "546-31-3503", "grd": "1x#10"},
    "8 AWG":  {"60C": 40, "75C": 50, "90C": 55, "area": 329, "od_mm": 20.6, "od_in": 0.81, "cat": "571-31-3190", "grd": "3x#14"},
    "6 AWG":  {"60C": 55, "75C": 65, "90C": 75, "area": 413, "od_mm": 22.9, "od_in": 0.90, "cat": "571-31-3191", "grd": "3x#12"},
    "4 AWG":  {"60C": 70, "75C": 85, "90C": 95, "area": 497, "od_mm": 25.1, "od_in": 0.99, "cat": "571-31-3200", "grd": "3x#12"},
    "2 AWG":  {"60C": 95, "75C": 115, "90C": 130, "area": 645, "od_mm": 28.7, "od_in": 1.13, "cat": "571-31-3204", "grd": "3x#10"},
    "1/0":    {"60C": 125, "75C": 150, "90C": 170, "area": 994, "od_mm": 35.6, "od_in": 1.40, "cat": "571-31-3213", "grd": "3x#10"},
    "2/0":    {"60C": 145, "75C": 175, "90C": 195, "area": 1103, "od_mm": 37.6, "od_in": 1.48, "cat": "571-31-3216", "grd": "3x#10"},
    "3/0":    {"60C": 165, "75C": 200, "90C": 225, "area": 1265, "od_mm": 40.1, "od_in": 1.58, "cat": "571-31-3218", "grd": "3x#10"},
    "4/0":    {"60C": 195, "75C": 230, "90C": 260, "area": 1516, "od_mm": 44.0, "od_in": 1.73, "cat": "571-31-3224", "grd": "3x#8"},
    "250 kcmil": {"60C": 215, "75C": 255, "90C": 290, "area": 1774, "od_mm": 47.5, "od_in": 1.87, "cat": "571-31-3228", "grd": "3x #8"},
    "500 kcmil": {"60C": 320, "75C": 380, "90C": 430, "area": 2761, "od_mm": 59.3, "od_in": 2.34, "cat": "571-31-3244", "grd": "3x #4"}
}

RES_CU_METRICO = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "500 kcmil": 0.089}

st.set_page_config(page_title="SOCEMB: Ingeniería de Cables", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []

st.title("⚡ SOCEMB: Selección de Cables Multiconductores con Tierra")

# --- 2. ENTRADA DE DATOS ---
with st.sidebar:
    st.header("🆔 Identificación")
    tag = st.text_input("Tag del Equipo", "M-101")
    origen = st.text_input("Origen", "MCC-A")
    destino = st.text_input("Destino", "Bomba B-01")
    ch_id = st.text_input("ID Trayectoria", "CH-01")
    
    st.header("⚡ Parámetros Eléctricos")
    hp = st.number_input("Potencia (HP)", value=100.0)
    v = st.selectbox("Voltaje (V)", [440, 460, 480], index=1)
    dist = st.number_input("Distancia (m)", value=60)
    
    st.header("🌍 Condiciones")
    t_amb = st.select_slider("Temp. Ambiente (°C)", options=[30, 35, 40, 45, 50], value=40)
    agrup = st.number_input("Cables en grupo", value=3)

# --- 3. SELECCIÓN ---
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)
i_nom = (hp * 746) / (v * 1.732 * 0.85 * 0.90)
i_dis = i_nom * 1.25

def obtener_cable():
    for cal, d in DATOS_OKONITE.items():
        lim_term = d["60C"] if i_dis <= 100 else d["75C"]
        cap_adj = d["90C"] * f_t * f_a
        vd = (1.732 * i_nom * dist * RES_CU_METRICO[cal]) / (v * 10)
        
        if i_dis <= lim_term and i_dis <= cap_adj and vd <= 3.0:
            return cal, d["cat"], d["grd"], round(vd, 2), d["od_mm"], d["od_in"]
    return "N/A", "N/A", "N/A", 0, 0, 0

calibre, cat, tierra, vd_f, od_m, od_i = obtener_cable()

# --- 4. REGISTRO ---
desc_completa = f"Okonite C-L-X MC-HL (3/C Cu + {tierra} GRD)"

if st.button("➕ Registrar en Schedule"):
    st.session_state.db.append({
        "TAG": tag, "ORIGEN": origen, "DESTINO": destino, "TRAYECTORIA": ch_id,
        "HP": hp, "I_DIS (A)": round(i_dis, 2), "CABLE": desc_completa,
        "CALIBRE": calibre, "CATÁLOGO": cat, "OD (mm)": od_m, "VD (%)": vd_f
    })

# --- 5. VISUALIZACIÓN ---
if st.session_state.db:
    df = pd.DataFrame(st.session_state.db)
    st.subheader("📋 Cable Schedule Consolidado (Métrico)")
    st.dataframe(df)
    
    # Análisis Monocapa
    st.subheader("📊 Llenado de Charolas (Unidad Principal: mm)")
    for tray, gp in df.groupby("TRAYECTORIA"):
        od_sum = gp[gp["CALIBRE"].str.contains("kcmil|1/0|2/0|3/0|4/0")]["OD (mm)"].sum()
        st.write(f"**Trayectoria {tray}:** {round(od_sum, 2)} mm ocupados por cables de potencia.")
