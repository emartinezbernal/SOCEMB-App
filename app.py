import streamlit as st
import pandas as pd
from datetime import datetime
import io
import math

# --- 1. BASES DE DATOS INTEGRADAS (NOM-001-SEDE / IPCEA) ---
TABLA_NEMA_3F_460V = {1.0: 1.8, 2.0: 3.4, 3.0: 4.8, 5.0: 7.6, 7.5: 11.0, 10.0: 14.0, 15.0: 21.0, 20.0: 27.0, 25.0: 34.0, 30.0: 40.0, 40.0: 52.0, 50.0: 65.0, 60.0: 77.0, 75.0: 96.0, 100.0: 124.0, 125.0: 156.0, 150.0: 180.0}
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
RES_OHM_KM = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "300 kcmil": 0.15, "350 kcmil": 0.13, "400 kcmil": 0.11, "500 kcmil": 0.089}
AREAS_MM2_CC = {"1/0": 53.49, "2/0": 67.43, "3/0": 85.01, "4/0": 107.2, "250 kcmil": 126.7, "300 kcmil": 152.0, "350 kcmil": 177.3, "400 kcmil": 202.7, "500 kcmil": 253.4}
AREAS_EXT_NOM = {"14 AWG": 8.9, "12 AWG": 11.6, "10 AWG": 15.6, "8 AWG": 28.1, "6 AWG": 46.9, "4 AWG": 62.7, "2 AWG": 85.9, "1/0": 143.4, "2/0": 175.4, "3/0": 214.3, "4/0": 263.4, "250 kcmil": 320.5, "500 kcmil": 582.4}

# Peralte 4" (101.6 mm). Anchos en pulgadas: mm2 de área total interna
ANCHOS_CHAROLA_4IN = {6: 15484, 9: 23226, 12: 30968, 18: 46451, 24: 61935, 30: 77419, 36: 92903}

st.set_page_config(page_title="SOCEMB Engineering Pro", layout="wide")

if 'lista_circuitos' not in st.session_state:
    st.session_state.lista_circuitos = []

st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

# --- 2. CAPTURA DE DATOS ---
with st.sidebar:
    st.header("📋 Identificación")
    c_tag = st.text_input("Tag del Circuito", "M-101")
    c_charola = st.text_input("ID Charola Origen", "CH-A-01")
    c_desc = st.text_input("Descripción", "Motor de Proceso")
    
    st.header("⚙️ Parámetros de Carga")
    tipo_p = st.selectbox("Unidad", ["HP (NEMA)", "kW", "kVA"])
    if tipo_p == "HP (NEMA)":
        val_p = st.selectbox("Valor HP", sorted(TABLA_NEMA_3F_460V.keys()), index=5)
        i_nom = TABLA_NEMA_3F_460V[val_p] * (460/460) # Ajuste base 460V
    else:
        val_p = st.number_input("Valor", value=10.0)
        v_sel = st.selectbox("Voltaje (V)", [220, 440, 460, 480], index=2)
        i_nom = (val_p * 1000) / (v_sel * 1.732) if tipo_p == "kVA" else (val_p * 1000) / (v_sel * 1.732 * 0.85)

    v_final = 460 if tipo_p == "HP (NEMA)" else v_sel
    dist = st.number_input("Longitud (m)", value=50)

    st.header("🛡️ Corto Circuito")
    i_falla = st.number_input("I de Falla (kA)", value=10.0)
    t_falla = st.number_input("Tiempo (seg)", value=0.016, format="%.3f")

# --- 3. PROCESO DE CÁLCULO ---
i_dis = (i_nom * 1.25) / 0.85 # Factor Charola
cal_base = next((c for c in list(TABLA_COBRE_75.keys()) if i_dis <= TABLA_COBRE_75[c]), "500 kcmil")

# Caída de Tensión
cal_final = cal_base
for cal in list(TABLA_COBRE_75.keys())[list(TABLA_COBRE_75.keys()).index(cal_base):]:
    vd = (1.732 * i_nom * dist * RES_OHM_KM.get(cal, 0.089)) / (v_final * 10)
    cal_final = cal
    if vd <= 3.0: break

# Corto Circuito (1/0 en adelante)
status_cc = "N/A"
if cal_final in AREAS_MM2_CC:
    i_soporta = (0.094 * AREAS_MM2_CC[cal_final]) / math.sqrt(t_falla)
    if i_falla > i_soporta:
        for c_cc in list(TABLA_COBRE_75.keys())[list(TABLA_COBRE_75.keys()).index(cal_final):]:
            if c_cc in AREAS_MM2_CC:
                if ((0.094 * AREAS_MM2_CC[c_cc]) / math.sqrt(t_falla)) >= i_falla:
                    cal_final = c_cc
                    status_cc = "✅ Ajustado por CC"
                    break
    else: status_cc = "✅ OK"

area_cable = AREAS_EXT_NOM.get(cal_final, 500) * 4 # 3F + T

# --- 4. RESULTADOS Y ACCIONES ---
st.info(f"Análisis: **{c_tag}** | {c_desc}")
col_res = st.columns(3)
col_res[0].metric("Calibre", cal_final)
col_res[1].metric("VD %", f"{round(vd, 2)}%")
col_res[2].metric("CC Status", status_cc)

if st.button("➕ Agregar al Cable Schedule"):
    st.session_state.lista_circuitos.append({
        "TAG": c_tag, "CHAROLA": c_charola, "DESCRIPCIÓN": c_desc,
        "CALIBRE": cal_final, "I NOM": round(i_nom, 2), "VD%": round(vd, 2),
        "CC STATUS": status_cc, "ÁREA (mm2)": round(area_cable, 2)
    })

# --- 5. REPORTES ---
if st.session_state.lista_circuitos:
    df = pd.DataFrame(st.session_state.lista_circuitos)
    st.subheader("📊 Memoria de Charolas (Peralte 4\")")
    rep = df.groupby("CHAROLA")["ÁREA (mm2)"].sum().reset_index()
    
    def nom_check(a):
        for pulg, a_max in ANCHOS_CHAROLA_4IN.items():
            if a <= (a_max * 0.40): return f"{pulg}\" ({pulg*25.4} mm)", f"{round((a/(a_max*0.4))*100,1)}%"
        return "SOBRESATURADA", "100%+"

    rep[['Ancho Sugerido', 'Llenado %']] = rep['ÁREA (mm2)'].apply(lambda x: pd.Series(nom_check(x)))
    st.table(rep)
    st.dataframe(df)

    # Excel Download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='CableSchedule')
        rep.to_excel(writer, index=False, sheet_name='MemoriaCharolas')
    st.download_button("📥 Descargar Excel SOCEMB", output.getvalue(), file_name="Reporte_SOCEMB.xlsx")
