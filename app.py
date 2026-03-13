import streamlit as st
import pandas as pd
import math

# --- 1. BASE DE DATOS TÉCNICA OKONITE C-L-X ---
DATOS_OKONITE = {
    "14 AWG": {"60C": 15, "75C": 20, "90C": 25, "cat": "546-31-3403", "grd": "1x#14", "short_1s": 1.5, "od": 16.3},
    "12 AWG": {"60C": 20, "75C": 20, "90C": 30, "cat": "546-31-3453", "grd": "1x#12", "short_1s": 2.4, "od": 17.5},
    "10 AWG": {"60C": 30, "75C": 30, "90C": 40, "cat": "546-31-3503", "grd": "1x#10", "short_1s": 3.8, "od": 18.6},
    "8 AWG":  {"60C": 40, "75C": 50, "90C": 55, "cat": "571-31-3190", "grd": "3x#14", "short_1s": 6.1, "od": 20.6},
    "6 AWG":  {"60C": 55, "75C": 65, "90C": 75, "cat": "571-31-3191", "grd": "3x#12", "short_1s": 9.7, "od": 22.9},
    "4 AWG":  {"60C": 70, "75C": 85, "90C": 95, "cat": "571-31-3200", "grd": "3x#12", "short_1s": 15.4, "od": 25.1},
    "2 AWG":  {"60C": 95, "75C": 115, "90C": 130, "cat": "571-31-3204", "grd": "3x#10", "short_1s": 24.5, "od": 28.7},
    "1/0":    {"60C": 125, "75C": 150, "90C": 170, "cat": "571-31-3213", "grd": "3x#10", "short_1s": 39.0, "od": 35.6},
    "2/0":    {"60C": 145, "75C": 175, "90C": 195, "cat": "571-31-3216", "grd": "3x#10", "short_1s": 49.1, "od": 37.6},
    "3/0":    {"60C": 165, "75C": 200, "90C": 225, "cat": "571-31-3218", "grd": "3x#8", "short_1s": 62.0, "od": 40.1},
    "4/0":    {"60C": 195, "75C": 230, "90C": 260, "cat": "571-31-3224", "grd": "3x#8", "short_1s": 78.1, "od": 44.0},
    "250 kcmil": {"60C": 215, "75C": 255, "90C": 290, "cat": "571-31-3228", "grd": "3x#8", "short_1s": 92.4, "od": 47.5},
    "500 kcmil": {"60C": 320, "75C": 380, "90C": 430, "cat": "571-31-3244", "grd": "3x#4", "short_1s": 184.8, "od": 59.3}
}

ORDEN_CAL = list(DATOS_OKONITE.keys())
RES_CU = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "500 kcmil": 0.089}
ANCHOS_NOM = {152.4: "6 in", 228.6: "9 in", 304.8: "12 in", 457.2: "18 in", 609.6: "24 in", 762.0: "30 in", 914.4: "36 in"}
HP_NEMA = [0.5, 0.75, 1, 1.5, 2, 3, 5, 7.5, 10, 15, 20, 25, 30, 40, 50, 60, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]

st.set_page_config(page_title="SOCEMB: Ingeniería Maestra Integral", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []

# --- 2. ENTRADA DE DATOS (MANTENIENDO TODOS LOS CAMPOS) ---
with st.sidebar:
    st.header("🆔 Trazabilidad")
    tag, origen, destino, tray = st.text_input("Tag"), st.text_input("Origen"), st.text_input("Destino"), st.text_input("ID Trayectoria")
    
    st.header("⚙️ Carga Eléctrica")
    u_pot = st.selectbox("Unidad", ["HP (Motor NEMA)", "kW", "kVA"])
    p_val = st.selectbox("Valor (HP)", HP_NEMA, index=15) if u_pot == "HP (Motor NEMA)" else st.number_input("Valor", value=100.0)
    v_op = st.selectbox("Voltaje (V)", [440, 460, 480], index=1)
    
    st.header("🌍 Factores Ambientales")
    dist, i_sc, t_f = st.number_input("Distancia (m)", 50), st.number_input("Isc Red (kA)", 10.0), st.number_input("Tiempo falla (s)", 0.1)
    t_amb = st.select_slider("Temp Ambiente (°C)", options=[30, 35, 40, 45, 50], value=40)
    agrup = st.number_input("Cables en Charola", value=3)

# --- 3. LÓGICA DE INGENIERÍA INTEGRAL (LAS 3 LEYES) ---
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)
i_nom = (p_val * 746) / (v_op * 1.732 * 0.85 * 0.90) if "HP" in u_pot else (p_val * 1000) / (v_op * 1.732)
i_dis = i_nom * 1.25

def calcular_ingenieria():
    c_amp, c_vd, c_sc = None, None, None
    t_term = "60C" if i_dis <= 100 else "75C"
    
    for cal in ORDEN_CAL:
        d = DATOS_OKONITE[cal]
        # Ley 1: Ampacidad (Terminales + Derating sobre 90C)
        cap_corr_90 = d["90C"] * f_t * f_a
        if not c_amp and i_dis <= d[t_term] and i_dis <= cap_corr_90: c_amp = cal
        # Ley 2: Caída de Tensión (Límite 3%)
        if not c_vd and ((1.732 * i_nom * dist * RES_CU[cal])/(v_op * 10)) <= 3.0: c_vd = cal
        # Ley 3: Corto Circuito (Térmica 1s)
        if not c_sc and i_sc <= (d["short_1s"]/(t_f**0.5)): c_sc = cal

    if all([c_amp, c_vd, c_sc]):
        idxs = [ORDEN_CAL.index(c_amp), ORDEN_CAL.index(c_vd), ORDEN_CAL.index(c_sc)]
        cal_f = ORDEN_CAL[max(idxs)]
        d_f = DATOS_OKONITE[cal_f]
        return {
            "CAL_F": cal_f, "MIN_AMP": c_amp, "MIN_VD": c_vd, "MIN_SC": c_sc,
            "T_TERM": t_term, "F_CORR": round(f_t * f_a, 2), "OD": d_f["od"],
            "CATALOGO": d_f["cat"], "FORMACION": f"3x{cal_f} + {d_f['grd']} GND",
            "VD_REAL": round((1.732 * i_nom * dist * RES_CU[cal_f])/(v_op * 10), 2),
            "ISC_ADMIS": round(d_f["short_1s"]/(t_f**0.5), 2),
            "ES_GRANDE": True if "1/0" in cal_f or "kcmil" in cal_f else False
        }
    return None

res = calcular_ingenieria()

# --- 4. MEMORIA DE CÁLCULO IMPRESA ---
if res:
    st.subheader(f"✅ Memoria de Ingeniería SOCEMB: Circuito {tag}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Ley 1: Ampacidad", res["MIN_AMP"], f"Ref: {res['T_TERM']} / Derating {res['F_CORR']}")
    col2.metric("Ley 2: Caída Tensión", res["MIN_VD"], f"Real: {res['VD_REAL']}%")
    col3.metric("Ley 3: Corto Circuito", res["MIN_SC"], f"Admisible: {res['ISC_ADMIS']} kA")
    
    st.success(f"**MODELO SELECCIONADO:** Catálogo **{res['CATALOGO']}** | Formación: **{res['FORMACION']}**")

    if st.button("💾 Registrar en Cable Schedule"):
        st.session_state.db.append({
            "TAG": tag, "ORIGEN": origen, "DESTINO": destino, "TRAY": tray,
            "MODELO": res["CATALOGO"], "FORMACIÓN": res["FORMACION"],
            "CALIBRE": res["CAL_F"], "MIN_AMP": res["MIN_AMP"], "MIN_VD": res["MIN_VD"],
            "MIN_SC": res["MIN_SC"], "I_DIS": round(i_dis, 1), "VD%": res["VD_REAL"],
            "ISC_MAX": res["ISC_ADMIS"], "OD": res["OD"], "GRANDE": res["ES_GRANDE"]
        })

# --- 5. AUDITORÍA DE CHAROLAS POR NOM-001 ART. 392 ---
if st.session_state.db:
    df = pd.DataFrame(st.session_state.db)
    st.divider()
    st.subheader("📋 Cable Schedule y Auditoría de Trayectorias")
    st.dataframe(df[["TAG", "ORIGEN", "DESTINO", "CALIBRE", "MODELO", "FORMACIÓN", "VD%", "ISC_MAX", "MIN_AMP", "MIN_VD", "MIN_SC"]])
    
    for tray_id, group in df.groupby("TRAY"):
        g_grandes = group[group["GRANDE"] == True]
        g_peques = group[group["GRANDE"] == False]
        # Los 3 criterios de la NOM restaurados:
        sum_od_g = g_grandes["OD"].sum()
        sum_area_p = (g_peques["OD"]**2 * 0.7854).sum()
        ancho_req = sum_od_g + (sum_area_p / 25.4) # Criterio combinado NOM
        ancho_f = min([a for a in ANCHOS_NOM.keys() if a >= ancho_req], default=914.4)
        
        st.warning(f"**Trayectoria {tray_id}:** Ancho Sugerido NOM: **{ANCHOS_NOM[ancho_f]}** (Llenado: {round((ancho_req/ancho_f)*100,1)}%)")
