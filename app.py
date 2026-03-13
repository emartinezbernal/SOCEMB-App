import streamlit as st
import pandas as pd

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

RES_CU = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "500 kcmil": 0.089}
ORDEN = list(DATOS_OKONITE.keys())

st.set_page_config(page_title="SOCEMB: Memoria de Cálculo Profesional", layout="wide")
if 'db' not in st.session_state: st.session_state.db = []

st.title("⚡ SOCEMB: Memoria de Cálculo y Selección de Conductores")

# --- 2. ENTRADA DE DATOS ---
with st.sidebar:
    st.header("🆔 Identificación")
    tag, tray = st.text_input("Tag del Circuito", "M-101"), st.text_input("Trayectoria", "CH-01")
    st.header("⚙️ Datos de Carga")
    hp = st.number_input("Potencia (HP)", value=150.0)
    v = st.selectbox("Voltaje (V)", [440, 460, 480], index=1)
    dist, i_sc, t_f = st.number_input("Distancia (m)", 50), st.number_input("Isc Red (kA)", 10.0), st.number_input("Tiempo Falla (s)", 0.1)
    st.header("🌍 Factores Ambientales")
    t_amb = st.select_slider("Temp Ambiente (°C)", options=[30, 35, 40, 45, 50], value=40)
    agrup = st.number_input("No. Cables en Charola", value=3)

# --- 3. PROCESO DE CÁLCULO ---
f_t = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_a = 1.0 if agrup <= 3 else (0.8 if agrup <= 6 else 0.7)
i_nom = (hp * 746) / (v * 1.732 * 0.85 * 0.90)
i_dis = i_nom * 1.25

def generar_calculo():
    c_amp, c_vd, c_sc = None, None, None
    t_label = "60°C" if i_dis <= 100 else "75°C" # Criterio de terminales
    
    for cal in ORDEN:
        d = DATOS_OKONITE[cal]
        # 1. Ampacidad: Comparar I_dis contra columna de terminales y capacidad corregida de 90C
        cap_corr_90 = d["90C"] * f_t * f_a
        if not c_amp and i_dis <= d["60C" if t_label=="60°C" else "75C"] and i_dis <= cap_corr_90:
            c_amp = cal
        # 2. Caída de Tensión
        if not c_vd and ((1.732 * i_nom * dist * RES_CU[cal])/(v*10)) <= 3.0:
            c_vd = cal
        # 3. Corto Circuito
        if not c_sc and i_sc <= (d["short_1s"]/(t_f**0.5)):
            c_sc = cal

    if all([c_amp, c_vd, c_sc]):
        idxs = [ORDEN.index(c_amp), ORDEN.index(c_vd), ORDEN.index(c_sc)]
        cal_f = ORDEN[max(idxs)]
        d_f = DATOS_OKONITE[cal_f]
        return {
            "cal_f": cal_f, "amp": c_amp, "vd": c_vd, "sc": c_sc, 
            "t_term": t_label, "f_corr": round(f_t * f_a, 2),
            "cap_f": round(d_f["90C"] * f_t * f_a, 1),
            "vd_r": round((1.732 * i_nom * dist * RES_CU[cal_f])/(v*10), 2),
            "isc_r": round(d_f["short_1s"]/(t_f**0.5), 2),
            "cat": d_f["cat"], "grd": d_f["grd"], "od": d_f["od_mm"]
        }
    return None

res = generar_calculo()

if res:
    # --- 4. IMPRESIÓN DE MEMORIA DE CÁLCULO (UI) ---
    st.subheader(f"📄 Memoria de Cálculo: Circuito {tag}")
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.write("**1. Criterio de Ampacidad**")
        st.write(f"- $I_{{nom}}$: {round(i_nom,1)} A | $I_{{dis}}$: {round(i_dis,1)} A")
        st.write(f"- Temp. Terminales: {res['t_term']}")
        st.write(f"- Calibre Mínimo: **{res['amp']}**")
    with m2:
        st.write("**2. Criterio de Caída de Tensión**")
        st.write(f"- Límite: 3.0% | Distancia: {dist}m")
        st.write(f"- Calibre Mínimo: **{res['vd']}**")
    with m3:
        st.write("**3. Criterio de Corto Circuito**")
        st.write(f"- $I_{{sc}}$ Red: {i_sc} kA | Tiempo: {t_f}s")
        st.write(f"- Calibre Mínimo: **{res['sc']}**")
    
    st.markdown(f"**RESULTADO FINAL:** Se selecciona cable **{res['cat']}** configurado como **3x{res['cal_f']} + {res['grd']}**.")
    
    if st.button("💾 Registrar en Cable Schedule"):
        st.session_state.db.append({
            "TAG": tag, "MODELO": res["cat"], "FORMACIÓN": f"3x{res['cal_f']}+{res['grd']}",
            "I_DIS": round(i_dis, 1), "DERATING": res["f_corr"], "TABLA": res["t_term"],
            "CAL_F": res["cal_f"], "VD_REAL": f"{res['vd_r']}%", "ISC_MAX": f"{res['isc_r']} kA", "TRAY": tray, "OD": res["od"]
        })

# --- 5. TABLA RESUMEN ---
if st.session_state.db:
    st.divider()
    st.subheader("📋 Cable Schedule Generado")
    df = pd.DataFrame(st.session_state.db)
    st.dataframe(df[["TAG", "MODELO", "FORMACIÓN", "I_DIS", "DERATING", "TABLA", "CAL_F", "VD_REAL", "ISC_MAX"]])
