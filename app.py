import streamlit as st
import pandas as pd
import math
from io import BytesIO

# --- 1. BASE DE DATOS TÉCNICA (MAN-EA-2901-100001 APÉNDICE B) ---
# R y X en Ohm/km. Ampacidad @ 45°C Amb. SC para 1s.
DB_MANATEE = {
    "14":   {"AMP": 24,  "R": 2.86231, "X": 0.0668, "OD": 16.3, "CAT": "546-31-3403", "SC": 1.5},
    "12":   {"AMP": 29,  "R": 1.80336, "X": 0.0608, "OD": 17.5, "CAT": "546-31-3453", "SC": 2.4},
    "10":   {"AMP": 38,  "R": 1.13234, "X": 0.0553, "OD": 18.6, "CAT": "546-31-3503", "SC": 3.8},
    "8":    {"AMP": 48,  "R": 0.85031, "X": 0.0503, "OD": 20.6, "CAT": "571-31-3190", "SC": 6.1},
    "6":    {"AMP": 65,  "R": 0.53472, "X": 0.0457, "OD": 22.9, "CAT": "571-31-3191", "SC": 9.7},
    "4":    {"AMP": 83,  "R": 0.33656, "X": 0.0422, "OD": 25.1, "CAT": "571-31-3200", "SC": 15.4},
    "2":    {"AMP": 111, "R": 0.21179, "X": 0.0390, "OD": 28.7, "CAT": "571-31-3204", "SC": 24.5},
    "1":    {"AMP": 131, "R": 0.16775, "X": 0.0380, "OD": 31.0, "CAT": "571-31-3211", "SC": 31.0},
    "1/0":  {"AMP": 150, "R": 0.13316, "X": 0.0360, "OD": 35.6, "CAT": "571-31-3213", "SC": 39.0},
    "2/0":  {"AMP": 173, "R": 0.10589, "X": 0.0350, "OD": 37.6, "CAT": "571-31-3216", "SC": 49.1},
    "3/0":  {"AMP": 199, "R": 0.08399, "X": 0.0340, "OD": 40.1, "CAT": "571-31-3218", "SC": 62.0},
    "4/0":  {"AMP": 232, "R": 0.06666, "X": 0.0330, "OD": 44.0, "CAT": "571-31-3224", "SC": 78.1},
    "250":  {"AMP": 258, "R": 0.05672, "X": 0.0326, "OD": 47.5, "CAT": "571-31-3228", "SC": 92.4},
    "500":  {"AMP": 382, "R": 0.02964, "X": 0.0310, "OD": 59.3, "CAT": "571-31-3244", "SC": 184.8}
}

st.set_page_config(page_title="SOCEMB v5.2 - Manatee Edition", layout="wide")

if 'cable_db' not in st.session_state:
    st.session_state.cable_db = []

# --- 2. INTERFAZ DE USUARIO ---
st.title("🚢 SOCEMB: Power Cable Sizing (Project Manatee)")
st.markdown("---")

col_in1, col_in2, col_in3 = st.columns(3)

with col_in1:
    st.header("🆔 Trazabilidad")
    tag = st.text_input("Cable Tag", value="MAN-CBL-GT80001A")
    orig = st.text_input("From (Source)", value="MAN-SB-8002N01")
    dest = st.text_input("To (Load)", value="MAN-GT-80001")
    tray = st.text_input("Tray ID", value="TY-101")

with col_in2:
    st.header("⚡ Parámetros Eléctricos")
    p_unit = st.selectbox("Unidad", ["kW", "HP (NEMA)", "kVA"])
    p_val = st.number_input("Valor de Carga", value=119.0) # Basado en tu ejemplo de Microturbina
    volt = st.selectbox("Voltaje (V)", [480, 460, 440, 4160], index=0)
    dist_ft = st.number_input("Longitud (ft)", value=289.0)

with col_in3:
    st.header("🌍 Factores de Sitio")
    t_amb = st.slider("Temp. Ambiente (°C)", 30, 55, 45)
    agrup = st.number_input("Cables en Trayectoria", 1, 10, 3)
    i_sc_ka = st.number_input("Isc Red (kA)", value=35.0)

# --- 3. MOTOR DE CÁLCULO (LÓGICA MANATEE) ---
def realizar_calculo():
    # Conversiones
    dist_km = (dist_ft * 0.3048) / 1000
    cos_phi = 0.85 # PF Estándar del Proyecto
    sin_phi = 0.526
    
    # I Nominal y Diseño (125%)
    if p_unit == "kW": i_nom = (p_val * 1000) / (volt * 1.732 * cos_phi)
    elif p_unit == "HP (NEMA)": i_nom = (p_val * 746) / (volt * 1.732 * cos_phi * 0.90)
    else: i_nom = (p_val * 1000) / (volt * 1.732)
    
    i_dis = i_nom * 1.25
    
    # Factores de Derating API 14FZ
    f_t = 1.0 if t_amb <= 45 else (0.88 if t_amb <= 50 else 0.82)
    f_a = 1.0 if agrup <= 3 else 0.8
    
    res = None
    for cal in DB_MANATEE.keys():
        d = DB_MANATEE[cal]
        # 1. Ampacidad
        amp_ok = i_dis <= (d["AMP"] * f_t * f_a)
        # 2. Caída de Tensión (3%)
        z = (d["R"] * cos_phi + d["X"] * sin_phi)
        vd = (1.732 * i_nom * dist_km * z) / (volt / 100)
        vd_ok = vd <= 3.0
        # 3. Corto Circuito
        sc_ok = i_sc_ka <= d["SC"]
        
        if amp_ok and vd_ok and sc_ok:
            res = {
                "TAG": tag, "ORIGEN": orig, "DESTINO": dest, "TRAY": tray,
                "CALIBRE": cal, "MODELO": d["CAT"], "I_NOM": round(i_nom, 1),
                "I_DIS": round(i_dis, 1), "VD%": round(vd, 2), "OD": d["OD"],
                "ISC_ADM": d["SC"], "STATUS": "CUMPLE"
            }
            break
    return res

resultado = realizar_calculo()

# --- 4. VISUALIZACIÓN Y ACCIONES ---
if resultado:
    st.subheader("✅ Resultado de Ingeniería")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Calibre Seleccionado", resultado["CALIBRE"])
    c2.metric("Caída de Tensión", f"{resultado['VD%']}%")
    c3.metric("I Nominal", f"{resultado['I_NOM']} A")
    c4.metric("Catálogo Okonite", resultado["MODELO"])
    
    if st.button("💾 Registrar en Cable Schedule"):
        st.session_state.cable_db.append(resultado)
        st.success("Circuito registrado correctamente.")

# --- 5. REPORTE Y EXPORTACIÓN ---
if st.session_state.cable_db:
    st.divider()
    df = pd.DataFrame(st.session_state.cable_db)
    st.subheader("📋 Cable Schedule: Proyecto Manatee (MAN-EA-2901-100001)")
    st.dataframe(df)

    # Exportación a Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='CableSchedule')
    
    st.download_button(
        label="📥 Descargar Reporte Oficial (Excel)",
        data=output.getvalue(),
        file_name="MAN-EA-2901-100001_CableSchedule.xlsx",
        mime="application/vnd.ms-excel"
    )
