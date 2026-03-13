import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- 1. BASES DE DATOS TÉCNICAS (NOM-001-SEDE / NEMA) ---
TABLA_NEMA_3F_460V = {1.0: 1.8, 2.0: 3.4, 3.0: 4.8, 5.0: 7.6, 7.5: 11.0, 10.0: 14.0, 15.0: 21.0, 20.0: 27.0, 25.0: 34.0, 30.0: 40.0, 40.0: 52.0, 50.0: 65.0, 60.0: 77.0, 75.0: 96.0, 100.0: 124.0, 125.0: 156.0, 150.0: 180.0}
TABLA_COBRE_75 = {"14 AWG": 15, "12 AWG": 20, "10 AWG": 30, "8 AWG": 50, "6 AWG": 65, "4 AWG": 85, "2 AWG": 115, "1/0": 150, "2/0": 175, "3/0": 200, "4/0": 230, "250 kcmil": 255, "300 kcmil": 285, "350 kcmil": 310, "400 kcmil": 335, "500 kcmil": 380}
ORDEN_CALIBRES = list(TABLA_COBRE_75.keys())
RES_OHM_KM = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "300 kcmil": 0.15, "350 kcmil": 0.13, "400 kcmil": 0.11, "500 kcmil": 0.089}

st.set_page_config(page_title="SOCEMB Engineering Pro", layout="wide")

if 'lista_circuitos' not in st.session_state:
    st.session_state.lista_circuitos = []

st.title("⚡ SOCEMB: Ingeniería Eléctrica Integral")

# --- 2. ENTRADAS LATERALES ---
with st.sidebar:
    st.header("📋 Identificación del Proyecto")
    c_tag = st.text_input("Tag del Circuito / No.", "M-101")
    c_desc = st.text_input("Descripción del Equipo", "Motor de Proceso")
    c_origen = st.text_input("Origen (DE:)", "CCM-01")
    c_destino = st.text_input("Destino (A:)", "Área de Bombas")
    
    st.header("⚙️ Parámetros de Diseño")
    tipo_p = st.selectbox("Unidad de Potencia", ["HP (NEMA)", "kW", "kVA"])
    val_p = st.selectbox("Valor HP", sorted(TABLA_NEMA_3F_460V.keys()), index=5) if tipo_p == "HP (NEMA)" else st.number_input("Valor", value=10.0)
    v = st.selectbox("Voltaje (V)", [220, 440, 460, 480], index=2)
    dist = st.number_input("Distancia / Longitud (m)", value=50)
    tipo_canal = st.radio("Método de Soporte", ["Tubo Conduit", "Charola"])

# --- 3. PROCESO DE CÁLCULO ---
# Corriente Nominal
if tipo_p == "HP (NEMA)":
    i_nom = TABLA_NEMA_3F_460V[val_p] * (460 / v)
else:
    fp_std = 0.85
    pkva = val_p / fp_std if tipo_p == "kW" else val_p
    i_nom = (pkva * 1000) / (v * 1.732)

# Corriente de Diseño y Ajuste
f_ajuste = 0.85 if tipo_canal == "Charola" else 0.80
i_dis = (i_nom * 1.25) / f_ajuste

# Selección por Ampacidad y Caída de Tensión
cal_base = next((c for c in ORDEN_CALIBRES if i_dis <= TABLA_COBRE_75[c]), "500 kcmil")
cal_final = cal_base
for cal in ORDEN_CALIBRES[ORDEN_CALIBRES.index(cal_base):]:
    r = RES_OHM_KM.get(cal, 0.089)
    vd = (1.732 * i_nom * dist * r) / (v * 10)
    cal_final = cal
    if vd <= 3.0: break
vd_final = (1.732 * i_nom * dist * RES_OHM_KM.get(cal_final, 0.089)) / (v * 10)

# --- 4. DISPLAY DE RESULTADOS ---
st.info(f"Circuito Actual: **{c_tag}** | {c_desc}")
c1, c2, c3 = st.columns(3)
c1.metric("FLC (Corriente)", f"{round(i_nom,2)} A")
c2.metric("Calibre Seleccionado", cal_final)
c3.metric("Caída de Tensión", f"{round(vd_final,2)} %")

if st.button("➕ Agregar al Cable Schedule"):
    st.session_state.lista_circuitos.append({
        "TAG": c_tag, "DESCRIPCIÓN": c_desc, "ORIGEN": c_origen, "DESTINO": c_destino,
        "POTENCIA": f"{val_p} {tipo_p}", "VOLTAJE": v, "LONGITUD (m)": dist,
        "I NOM (A)": round(i_nom, 2), "CALIBRE": cal_final, "VD (%)": round(vd_final, 2), "SOPORTE": tipo_canal
    })
    st.success(f"Registro {c_tag} guardado.")

# --- 5. EXPORTACIÓN ---
if st.session_state.lista_circuitos:
    df = pd.DataFrame(st.session_state.lista_circuitos)
    st.markdown("---")
    st.dataframe(df)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='CableSchedule')
    
    st.download_button("📥 Descargar Excel para Master Template", output.getvalue(), 
                       file_name=f"SOCEMB_Schedule_{datetime.now().strftime('%Y%m%d')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if st.button("🗑️ Reiniciar Lista"):
        st.session_state.lista_circuitos = []
        st.rerun()
