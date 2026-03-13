import streamlit as st
import pandas as pd
import io

# --- 1. BASE DE DATOS TÉCNICA OKONITE C-L-X (MODELO MC-HL) ---
# Configuración: 3 Conductores de Cobre + Tierras Simétricas. Aislamiento X-Olene (XHHW-2) 90°C.
# Datos extraídos de la Tabla de Product Data Section 4: Sheet 1.
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

# Resistencias Ohm/km (Cobre @ 75°C)
RES_CU = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "350 kcmil": 0.13, "500 kcmil": 0.089}

# Configuración de Charolas Peralte 4" (Límite NOM 40% Área / 100% Diámetro Monocapa)
ANCHOS_CHAROLA_4IN = {6: 15484, 9: 23226, 12: 30968, 18: 46451, 24: 61935, 30: 77419, 36: 92903}

st.set_page_config(page_title="SOCEMB: Okonite Selection Pro", layout="wide")

if 'db' not in st.session_state:
    st.session_state.db = []

st.title("⚡ SOCEMB: Selección de Cables Okonite C-L-X")
st.info("Configuración: Tipo MC-HL, 3-Cond, VFD, 600/1000V, Armadura Corrugada de Aluminio")

# --- 2. INTERFAZ DE USUARIO ---
with st.sidebar:
    st.header("📋 Datos del Circuito")
    tag = st.text_input("Tag del Circuito", "M-101")
    ch_id = st.text_input("ID Charola", "CH-A-01")
    hp = st.number_input("Potencia (HP)", value=10.0)
    v = st.selectbox("Voltaje (V)", [220, 440, 460, 480], index=2)
    dist = st.number_input("Longitud (m)", value=50)
    
    st.header("🌍 Factores de Ajuste")
    t_amb = st.select_slider("Temp. Ambiente (°C)", options=[30, 35, 40, 45, 50], value=30)
    agrup = st.number_input("Conductores Portadores", value=3)

# --- 3. LÓGICA DE SELECCIÓN ---
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)

i_nom = (hp * 746) / (v * 1.732 * 0.85 * 0.90)
i_dis = i_nom * 1.25

def seleccionar_cable():
    for cal, d in DATOS_OKONITE.items():
        # Regla NOM Terminales (60C si <= 100A, 75C si > 100A)
        lim_term = d["60C"] if i_dis <= 100 else d["75C"]
        # Capacidad Corregida (90C x Factores)
        cap_adj = d["90C"] * f_t * f_a
        
        if i_dis <= lim_term and i_dis <= cap_adj:
            vd = (1.732 * i_nom * dist * RES_CU[cal]) / (v * 10)
            if vd <= 3.0:
                return cal, d["cat"], round(vd, 2), lim_term, round(cap_adj, 2)
    return "N/A", "N/A", 0, 0, 0

calibre, cat, vd_val, l_term, c_adj = seleccionar_cable()

# --- 4. VISUALIZACIÓN ---
c1, c2, c3 = st.columns(3)
c1.metric("Ampacidad Diseño", f"{round(i_dis, 2)} A")
c2.metric("Modelo Seleccionado", calibre)
c3.metric("Caída de Tensión", f"{vd_val}%")

st.success(f"**Referencia Catálogo:** Okonite C-L-X MC-HL #{cat}")

if st.button("➕ Registrar en Schedule"):
    st.session_state.db.append({
        "TAG": tag, "CHAROLA": ch_id, "HP": hp, "CALIBRE": calibre, 
        "CATÁLOGO": cat, "OD (mm)": DATOS_OKONITE[calibre]["od"],
        "ÁREA (mm2)": DATOS_OKONITE[calibre]["area"]
    })

# --- 5. REPORTE DE CHAROLAS (LÓGICA MONOCAPA) ---
if st.session_state.db:
    df = pd.DataFrame(st.session_state.db)
    st.subheader("📊 Análisis de Llenado (Criterio Diámetro para >= 1/0)")
    
    res = []
    for ch, group in df.groupby("CHAROLA"):
        # Suma de diámetros para cables grandes
        grandes = group[group["CALIBRE"].str.contains("kcmil|1/0|2/0|3/0|4/0")]
        ancho_req = grandes["OD (mm)"].sum()
        
        # Sugerir ancho de charola (en pulgadas)
        ancho_sug = next((a for a in [6, 9, 12, 18, 24, 30, 36] if (a * 25.4) >= ancho_req), "MAYOR A 36")
        res.append({"Charola": ch, "Ancho Requerido (mm)": round(ancho_req, 2), "Ancho Sugerido": f"{ancho_sug} in"})
    
    st.table(res)
    st.dataframe(df)
