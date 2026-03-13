import streamlit as st
import pandas as pd

# --- 1. BASE DE DATOS TÉCNICA INVARIABLE (OKONITE C-L-X) ---
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

st.set_page_config(page_title="SOCEMB: Memoria de Cálculo", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []

st.title("⚡ SOCEMB: Memoria de Cálculo de Conductores")

# --- 2. SIDEBAR: ENTRADA TÉCNICA COMPLETA ---
with st.sidebar:
    st.header("🆔 Identificación del Proyecto")
    tag = st.text_input("Tag del Circuito", "M-101")
    origen = st.text_input("Origen (MCC/Panel)", "MCC-01")
    destino = st.text_input("Destino (Equipo)", "Motor-A")
    trayectoria = st.text_input("ID Trayectoria (Tray)", "CH-01")
    
    st.header("⚙️ Parámetros de Diseño")
    hp = st.selectbox("Potencia de Carga (HP)", options=HP_STANDARD, index=19) # 150 HP
    v = st.selectbox("Voltaje Nominal (V)", [440, 460, 480], index=1)
    dist = st.number_input("Longitud de Trayectoria (m)", value=50)
    i_sc = st.number_input("Corriente Corto Circuito Red (kA)", value=10.0)
    t_falla = st.number_input("Tiempo de Despeje de Falla (s)", value=0.1)
    
    st.header("🌍 Factores de Corrección")
    t_amb = st.select_slider("Temperatura Ambiente (°C)", options=[30, 35, 40, 45, 50], value=40)
    agrup = st.number_input("No. Conductores Agrupados", value=3)

# --- 3. CÁLCULOS DE INGENIERÍA (MEMORIA INTERNA) ---
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)
i_nom = (hp * 746) / (v * 1.732 * 0.85 * 0.90)
i_dis = i_nom * 1.25

def ejecutar_memoria():
    c_amp, c_vd, c_sc = None, None, None
    for cal in ORDEN_CALIBRES:
        d = DATOS_OKONITE[cal]
        # Criterio 1: Ampacidad (NOM terminales)
        t_ref = "60C" if i_dis <= 100 else "75C"
        cap_corr = d["90C"] * f_t * f_a
        if not c_amp and i_dis <= d[t_ref] and i_dis <= cap_corr: c_amp = cal
        # Criterio 2: Caída de Tensión (Límite 3%)
        vd = (1.732 * i_nom * dist * RES_CU_METRICO[cal]) / (v * 10)
        if not c_vd and vd <= 3.0: c_vd = cal
        # Criterio 3: Corto Circuito
        isc_lim = d["short_1s"] / (t_falla ** 0.5)
        if not c_sc and i_sc <= isc_lim: c_sc = cal

    if all([c_amp, c_vd, c_sc]):
        idxs = [ORDEN_CALIBRES.index(c_amp), ORDEN_CALIBRES.index(c_vd), ORDEN_CALIBRES.index(c_sc)]
        idx_f = max(idxs)
        cal_f = ORDEN_CALIBRES[idx_f]
        d_f = DATOS_OKONITE[cal_f]
        gob = "Ampacidad" if idx_f == idxs[0] else ("Caída Tensión" if idx_f == idxs[1] else "Corto Circuito")
        return {
            "final": cal_f, "amp": c_amp, "vd": c_vd, "sc": c_sc, "gob": gob,
            "vd_r": round((1.732 * i_nom * dist * RES_CU_METRICO[cal_f])/(v*10), 2),
            "isc_r": round(d_f["short_1s"]/(t_falla**0.5), 2), "od": d_f["od_mm"], "grd": d_f["grd"]
        }
    return None

res = ejecutar_memoria()

if res:
    st.success(f"Selección Óptima: {res['final']} | Factor Limitante: {res['gob']}")
    if st.button("➕ Registrar en Memoria de Cálculo"):
        st.session_state.db.append({
            "TAG": tag, "ORIGEN": origen, "DESTINO": destino, "HP": hp, "I_DIS (A)": round(i_dis, 2),
            "MIN_AMP": res["amp"], "MIN_VD": res["vd"], "MIN_SC": res["sc"], 
            "GOBERNADO": res["gob"], "CALIBRE_FINAL": res["final"], "VD_REAL%": f"{res['vd_r']}%",
            "ISC_MAX_KA": res["isc_r"], "GROUND": res["grd"], "OD_MM": res["od"], "TRAY": trayectoria
        })

# --- 4. DATAFRAME: RESUMEN DE MEMORIA DE CÁLCULO ---
if st.session_state.db:
    df = pd.DataFrame(st.session_state.db)
    st.subheader("📋 Resumen Ejecutivo de Memoria de Cálculo")
    # Este DataFrame es el juicio técnico que solicitaste
    cols_finales = ["TAG", "I_DIS (A)", "MIN_AMP", "MIN_VD", "MIN_SC", "GOBERNADO", "CALIBRE_FINAL", "VD_REAL%", "ISC_MAX_KA", "GROUND"]
    st.dataframe(df[cols_finales])
    
    st.subheader("📊 Análisis de Llenado de Trayectorias")
    for tray, gp in df.groupby("TRAY"):
        suma_od = gp["OD_MM"].sum()
        ancho = next((a for a in ANCHOS_CHAROLA_MM if a >= suma_od), 914.4)
        st.write(f"**Trayectoria {tray}:** Suma OD: {round(suma_od,1)}mm | Sugerida: {ANCHOS_CHAROLA_MM[ancho]} | Llenado: {round((suma_od/ancho)*100, 1)}%")
