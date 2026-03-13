import streamlit as st
import pandas as pd
import io

# --- 1. BASE DE DATOS TÉCNICA OKONITE C-L-X ---
DATOS_OKONITE = {
    "14 AWG": {"60C": 15, "75C": 20, "90C": 25, "area_mm2": 2.08, "od_mm": 16.3, "cat": "546-31-3403", "grd": "1x#14", "short_1s": 1.5},
    "12 AWG": {"60C": 20, "75C": 20, "90C": 30, "area_mm2": 3.31, "od_mm": 17.5, "cat": "546-31-3453", "grd": "1x#12", "short_1s": 2.4},
    "10 AWG": {"60C": 30, "75C": 30, "90C": 40, "area_mm2": 5.26, "od_mm": 18.6, "cat": "546-31-3503", "grd": "1x#10", "short_1s": 3.8},
    "8 AWG":  {"60C": 40, "75C": 50, "90C": 55, "area_mm2": 8.37, "od_mm": 20.6, "cat": "571-31-3190", "grd": "3x#14", "short_1s": 6.1},
    "6 AWG":  {"60C": 55, "75C": 65, "90C": 75, "area_mm2": 13.3, "od_mm": 22.9, "cat": "571-31-3191", "grd": "3x#12", "short_1s": 9.7},
    "4 AWG":  {"60C": 70, "75C": 85, "90C": 95, "area_mm2": 21.1, "od_mm": 25.1, "cat": "571-31-3200", "grd": "3x#12", "short_1s": 15.4},
    "2 AWG":  {"60C": 95, "75C": 115, "90C": 130, "area_mm2": 33.6, "od_mm": 28.7, "cat": "571-31-3204", "grd": "3x#10", "short_1s": 24.5},
    "1/0":    {"60C": 125, "75C": 150, "90C": 170, "area_mm2": 53.5, "od_mm": 35.6, "cat": "571-31-3213", "grd": "3x#10", "short_1s": 39.0},
    "2/0":    {"60C": 145, "75C": 175, "90C": 195, "area_mm2": 67.4, "od_mm": 37.6, "cat": "571-31-3216", "grd": "3x#10", "short_1s": 49.1},
    "3/0":    {"60C": 165, "75C": 200, "90C": 225, "area_mm2": 85.0, "od_mm": 40.1, "cat": "571-31-3218", "grd": "3x#8", "short_1s": 62.0},
    "4/0":    {"60C": 195, "75C": 230, "90C": 260, "area_mm2": 107, "od_mm": 44.0, "cat": "571-31-3224", "grd": "3x#8", "short_1s": 78.1},
    "250 kcmil": {"60C": 215, "75C": 255, "90C": 290, "area_mm2": 127, "od_mm": 47.5, "cat": "571-31-3228", "grd": "3x#8", "short_1s": 92.4},
    "500 kcmil": {"60C": 320, "75C": 380, "90C": 430, "area_mm2": 253, "od_mm": 59.3, "cat": "571-31-3244", "grd": "3x#4", "short_1s": 184.8}
}

ORDEN_CALIBRES = list(DATOS_OKONITE.keys())
RES_CU_METRICO = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "500 kcmil": 0.089}
ANCHOS_CHAROLA_MM = {152.4: "6 in", 228.6: "9 in", 304.8: "12 in", 457.2: "18 in", 609.6: "24 in", 762.0: "30 in", 914.4: "36 in"}
HP_STANDARD = [0.5, 0.75, 1, 1.5, 2, 3, 5, 7.5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]

st.set_page_config(page_title="SOCEMB vFinal", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []

st.title("⚡ SOCEMB: Ingeniería de Cables")

# --- 2. ENTRADA DE DATOS (SIDEBAR) ---
with st.sidebar:
    st.header("🆔 Identificación")
    tag = st.text_input("Tag del Circuito", "M-101")
    origen = st.text_input("Origen", "MCC-01")
    destino = st.text_input("Destino", "Motor-A")
    trayectoria = st.text_input("ID Trayectoria", "CH-01")
    tipo_cable_ui = st.radio("Tipo de Conductor", ["Multiconductor (Okonite)", "Monopolar (NOM)"])
    
    st.header("⚙️ Parámetros de Carga")
    hp = st.selectbox("HP Estándar (NEMA)", options=HP_STANDARD, index=19) # Default 150 HP
    v = st.selectbox("Voltaje (V)", [440, 460, 480], index=1)
    dist = st.number_input("Longitud Trayectoria (m)", value=50)
    i_sc = st.number_input("Nivel I Corto Circuito (kA)", value=10.0)
    t_falla = st.number_input("Tiempo de Duración Falla (s)", value=0.1)
    
    st.header("🌍 Factores de Ajuste")
    t_amb = st.select_slider("Temp. Ambiente (°C)", options=[30, 35, 40, 45, 50], value=40)
    agrup = st.number_input("Conductores Portadores en Grupo", value=3)

# --- 3. LÓGICA DE SELECCIÓN POR CALIBRE MAYOR ---
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)
i_nom = (hp * 746) / (v * 1.732 * 0.85 * 0.90)
i_dis = i_nom * 1.25

def realizar_ingenieria():
    cal_amp, cal_vd, cal_sc = None, None, None
    
    for cal in ORDEN_CALIBRES:
        d = DATOS_OKONITE[cal]
        # A. Criterio Ampacidad (Deratings + Terminales)
        t_ref = "60C" if i_dis <= 100 else "75C"
        cap_corregida = d["90C"] * f_t * f_a
        if not cal_amp and i_dis <= d[t_ref] and i_dis <= cap_corregida:
            cal_amp = cal
            
        # B. Criterio Caída de Tensión (Máximo 3%)
        vd = (1.732 * i_nom * dist * RES_CU_METRICO[cal]) / (v * 10)
        if not cal_vd and vd <= 3.0:
            cal_vd = cal
            
        # C. Criterio Corto Circuito (Capacidad vs Nivel Falla)
        isc_cable = d["short_1s"] / (t_falla ** 0.5)
        if not cal_sc and i_sc <= isc_cable:
            cal_sc = cal

    if cal_amp and cal_vd and cal_sc:
        idxs = [ORDEN_CALIBRES.index(cal_amp), ORDEN_CALIBRES.index(cal_vd), ORDEN_CALIBRES.index(cal_sc)]
        idx_final = max(idxs)
        cal_final = ORDEN_CALIBRES[idx_final]
        
        # Determinar criterio gobernante
        gob = "Ampacidad" if idx_final == idxs[0] else ("Caída Tensión" if idx_final == idxs[1] else "Corto Circuito")
        d_f = DATOS_OKONITE[cal_final]
        
        return {
            "final": cal_final, "c_amp": cal_amp, "c_vd": cal_vd, "c_sc": cal_sc, "gobernante": gob,
            "vd_f": round((1.732 * i_nom * dist * RES_CU_METRICO[cal_final]) / (v * 10), 2),
            "isc_f": round(d_f["short_1s"] / (t_falla ** 0.5), 2), "od": d_f["od_mm"]
        }
    return None

res = realizar_ingenieria()

if res:
    st.success(f"Calibre Final: {res['final']} (Gobernado por {res['gobernante']})")
    if st.button("➕ Registrar en Cable Schedule"):
        st.session_state.db.append({
            "TAG": tag, "ORIGEN": origen, "DESTINO": destino, "TRAYECTORIA": trayectoria,
            "I_DIS (A)": round(i_dis, 2), "MIN_AMP": res["c_amp"], "MIN_VD": res["c_vd"], 
            "MIN_SC": res["c_sc"], "CRITERIO_GOB": res["gobernante"], "SELECCIÓN_FINAL": res["final"],
            "VD%": res["vd_f"], "ISC_KA": res["isc_f"], "OD_MM": res["od"]
        })

# --- 4. REPORTES Y LLENADO ---
if st.session_state.db:
    df = pd.DataFrame(st.session_state.db)
    st.subheader("📋 Resumen de Selección y Auditoría")
    cols = ["TAG", "I_DIS (A)", "MIN_AMP", "MIN_VD", "MIN_SC", "CRITERIO_GOB", "SELECCIÓN_FINAL", "VD%", "ISC_KA"]
    st.dataframe(df[cols])
    
    st.subheader("📊 Análisis de Llenado de Trayectorias")
    res_tray = []
    for tray, gp in df.groupby("TRAYECTORIA"):
        od_sum = gp["OD_MM"].sum()
        ancho_mm = next((a for a in ANCHOS_CHAROLA_MM if a >= od_sum), 914.4)
        res_tray.append({
            "CHAROLA": tray, "Ancho Req (mm)": round(od_sum, 2), 
            "Sugerencia": ANCHOS_CHAROLA_MM[ancho_mm], "% Llenado": f"{round((od_sum/ancho_mm)*100, 2)}%"
        })
    st.table(res_tray)
