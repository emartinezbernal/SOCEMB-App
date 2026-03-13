import streamlit as st
import pandas as pd
import io

# --- 1. BASE DE DATOS TÉCNICA OKONITE C-L-X (3/C + TIERRA VFD) ---
DATOS_OKONITE = {
    "14 AWG": {"60C": 15, "75C": 20, "90C": 25, "area_mm2": 206, "od_mm": 16.3, "cat": "546-31-3403", "grd": "1x#14", "short_1s": 1.5},
    "12 AWG": {"60C": 20, "75C": 20, "90C": 30, "area_mm2": 239, "od_mm": 17.5, "cat": "546-31-3453", "grd": "1x#12", "short_1s": 2.4},
    "10 AWG": {"60C": 30, "75C": 30, "90C": 40, "area_mm2": 271, "od_mm": 18.6, "cat": "546-31-3503", "grd": "1x#10", "short_1s": 3.8},
    "8 AWG":  {"60C": 40, "75C": 50, "90C": 55, "area_mm2": 329, "od_mm": 20.6, "cat": "571-31-3190", "grd": "3x#14", "short_1s": 6.1},
    "6 AWG":  {"60C": 55, "75C": 65, "90C": 75, "area_mm2": 413, "od_mm": 22.9, "cat": "571-31-3191", "grd": "3x#12", "short_1s": 9.7},
    "4 AWG":  {"60C": 70, "75C": 85, "90C": 95, "area_mm2": 497, "od_mm": 25.1, "cat": "571-31-3200", "grd": "3x#12", "short_1s": 15.4},
    "2 AWG":  {"60C": 95, "75C": 115, "90C": 130, "area_mm2": 645, "od_mm": 28.7, "cat": "571-31-3204", "grd": "3x#10", "short_1s": 24.5},
    "1/0":    {"60C": 125, "75C": 150, "90C": 170, "area_mm2": 994, "od_mm": 35.6, "cat": "571-31-3213", "grd": "3x#10", "short_1s": 39.0},
    "2/0":    {"60C": 145, "75C": 175, "90C": 195, "area_mm2": 1103, "od_mm": 37.6, "cat": "571-31-3216", "grd": "3x#10", "short_1s": 49.1},
    "3/0":    {"60C": 165, "75C": 200, "90C": 225, "area_mm2": 1265, "od_mm": 40.1, "cat": "571-31-3218", "grd": "3x#8", "short_1s": 62.0},
    "4/0":    {"60C": 195, "75C": 230, "90C": 260, "area_mm2": 1516, "od_mm": 44.0, "cat": "571-31-3224", "grd": "3x#8", "short_1s": 78.1},
    "250 kcmil": {"60C": 215, "75C": 255, "90C": 290, "area_mm2": 1774, "od_mm": 47.5, "cat": "571-31-3228", "grd": "3x#8", "short_1s": 92.4},
    "350 kcmil": {"60C": 260, "75C": 310, "90C": 350, "area_mm2": 2213, "od_mm": 53.0, "cat": "571-31-3236", "short_1s": 129.4},
    "500 kcmil": {"60C": 320, "75C": 380, "90C": 430, "area_mm2": 2761, "od_mm": 59.3, "cat": "571-31-3244", "grd": "3x#4", "short_1s": 184.8}
}

# Resistencia en Ohm/km para Caída de Tensión (Cobre)
RES_CU_METRICO = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "350 kcmil": 0.13, "500 kcmil": 0.089}
ANCHOS_CHAROLA_MM = {152.4: "6 in", 228.6: "9 in", 304.8: "12 in", 457.2: "18 in", 609.6: "24 in", 762.0: "30 in", 914.4: "36 in"}

st.set_page_config(page_title="SOCEMB vFinal", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []

st.title("⚡ SOCEMB: Ingeniería de Cables (Versión Final Unificada)")

# --- 2. ENTRADA DE DATOS (SIDEBAR) ---
with st.sidebar:
    st.header("📋 Identificación")
    tag = st.text_input("Tag del Circuito", "M-101")
    origen = st.text_input("Origen", "MCC-A")
    destino = st.text_input("Destino", "Bomba-01")
    trayectoria = st.text_input("ID Trayectoria (Charola)", "CH-01")
    
    st.header("⚙️ Parámetros Eléctricos")
    hp = st.number_input("Potencia (HP)", value=150.0)
    v = st.selectbox("Voltaje (V)", [440, 460, 480], index=1)
    dist = st.number_input("Distancia (m)", value=50)
    i_sc = st.number_input("I Corto Circuito (kA)", value=10.0)
    t_falla = st.number_input("Tiempo de Falla (s)", value=0.1)
    
    st.header("🌍 Factores")
    t_amb = st.select_slider("Temp. Ambiente (°C)", options=[30, 35, 40, 45, 50], value=40)
    agrup = st.number_input("Conductores en Grupo", value=3)

# --- 3. CÁLCULOS TÉCNICOS ---
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)
i_nom = (hp * 746) / (v * 1.732 * 0.85 * 0.90)
i_dis = i_nom * 1.25

def seleccionar_cable():
    for cal, d in DATOS_OKONITE.items():
        lim_term = d["60C"] if i_dis <= 100 else d["75C"]
        cap_adj = d["90C"] * f_t * f_a
        vd = (1.732 * i_nom * dist * RES_CU_METRICO[cal]) / (v * 10)
        isc_cable = d["short_1s"] / (t_falla ** 0.5)
        
        if i_dis <= lim_term and i_dis <= cap_adj and vd <= 3.0 and i_sc <= isc_cable:
            return cal, d["cat"], d["grd"], round(vd, 2), d["od_mm"], round(isc_cable, 2), d["area_mm2"]
    return "N/A", "N/A", "N/A", 0, 0, 0, 0

calibre, cat, grd, vd_res, od_m, isc_c, area_m = seleccionar_cable()

# --- 4. VISUALIZACIÓN DE CÁLCULO ACTUAL ---
col1, col2, col3 = st.columns(3)
with col1: st.metric("Ampacidad Diseño", f"{round(i_dis, 2)} A")
with col2: st.metric("Modelo Seleccionado", calibre)
with col3: st.metric("Caída de Tensión", f"{vd_res}%")

st.info(f"**Referencia Catálogo:** Okonite C-L-X MC-HL #{cat}")

if st.button("➕ Agregar al Cable Schedule"):
    st.session_state.db.append({
        "TAG": tag, "ORIGEN": origen, "DESTINO": destino, "TRAYECTORIA": trayectoria,
        "I_DIS (A)": round(i_dis, 2), "CALIBRE": calibre, "CATÁLOGO": cat,
        "OD_MM": od_m, "AREA_MM2": area_m, "VD_PORC": vd_res, "ISC_KA": isc_c
    })

# --- 5. REPORTES CONSOLIDADOS ---
if st.session_state.db:
    df = pd.DataFrame(st.session_state.db)
    
    st.subheader("📋 Cable Schedule")
    st.dataframe(df)
    
    st.subheader("📊 Llenado de Charolas (Unidad Principal: mm)")
    res_charolas = []
    for tray, gp in df.groupby("TRAYECTORIA"):
        # Regla Combinada: Suma de diámetros para asegurar monocapa
        od_sum = gp["OD_MM"].sum()
        ancho_sug = next((a for a in ANCHOS_CHAROLA_MM if a >= od_sum), 914.4)
        
        res_charolas.append({
            "CHAROLA": tray,
            "Ancho Requerido (mm)": round(od_sum, 2),
            "Ancho Sugerido": f"{ANCHOS_CHAROLA_MM[ancho_sug]} ({ancho_sug} mm)"
        })
    st.table(res_charolas)

    towrite = io.BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    st.download_button("📥 Descargar Reporte Excel", towrite.getvalue(), file_name="SOCEMB_Final.xlsx")
