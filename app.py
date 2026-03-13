import streamlit as st
import pandas as pd
import io
import math

# --- 1. BASE DE DATOS TÉCNICA OKONITE C-L-X (CU/AL MC-HL) ---
# Datos extraídos del catálogo: Ampacidad (60/75/90°C), Área (mm2) y Diámetro (mm)
DATOS_OKONITE = {
    "14 AWG": {"60C": 15, "75C": 20, "90C": 25, "area": 206, "od": 16.3},
    "12 AWG": {"60C": 20, "75C": 20, "90C": 30, "area": 239, "od": 17.5},
    "10 AWG": {"60C": 30, "75C": 30, "90C": 40, "area": 271, "od": 18.6},
    "8 AWG":  {"60C": 40, "75C": 50, "90C": 55, "area": 329, "od": 20.6},
    "6 AWG":  {"60C": 55, "75C": 65, "90C": 75, "area": 413, "od": 22.9},
    "4 AWG":  {"60C": 70, "75C": 85, "90C": 95, "area": 497, "od": 25.1},
    "2 AWG":  {"60C": 95, "75C": 115, "90C": 130, "area": 645, "od": 28.7},
    "1/0":    {"60C": 125, "75C": 150, "90C": 170, "area": 994, "od": 35.6},
    "2/0":    {"60C": 145, "75C": 175, "90C": 195, "area": 1103, "od": 37.6},
    "3/0":    {"60C": 165, "75C": 200, "90C": 225, "area": 1265, "od": 40.1},
    "4/0":    {"60C": 195, "75C": 230, "90C": 260, "area": 1516, "od": 44.0},
    "250 kcmil": {"60C": 215, "75C": 255, "90C": 290, "area": 1774, "od": 47.5},
    "350 kcmil": {"60C": 260, "75C": 310, "90C": 350, "area": 2213, "od": 53.0},
    "500 kcmil": {"60C": 320, "75C": 380, "90C": 430, "area": 2761, "od": 59.3}
}

# Resistencia para Caída de Tensión (Cobre @ 75°C)
RES_CU = {"14 AWG": 10.2, "12 AWG": 6.6, "10 AWG": 3.9, "8 AWG": 2.5, "6 AWG": 1.6, "4 AWG": 1.0, "2 AWG": 0.62, "1/0": 0.39, "2/0": 0.31, "3/0": 0.25, "4/0": 0.20, "250 kcmil": 0.17, "350 kcmil": 0.13, "500 kcmil": 0.089}

# Áreas útiles charolas Peralte 4" (101.6 mm) para límite NOM del 40%
ANCHOS_CHAROLA_4IN = {6: 15484, 9: 23226, 12: 30968, 18: 46451, 24: 61935, 30: 77419, 36: 92903}

st.set_page_config(page_title="SOCEMB: Ingeniería Eléctrica Pro", layout="wide")

if 'schedule' not in st.session_state:
    st.session_state.schedule = []

st.title("⚡ SOCEMB: Ingeniería de Cables y Charolas")
st.markdown("---")

# --- 2. ENTRADA DE DATOS ---
with st.sidebar:
    st.header("📋 Identificación del Circuito")
    tag = st.text_input("Tag del Circuito (e.g. M-101)", "M-101")
    desc = st.text_input("Descripción", "Motor de Proceso")
    charola = st.text_input("ID de Charola", "CH-A-01")
    
    st.header("⚙️ Parámetros de Carga")
    potencia = st.number_input("Potencia (HP)", value=10.0, step=0.5)
    voltaje = st.selectbox("Voltaje de Operación (V)", [220, 440, 460, 480], index=2)
    distancia = st.number_input("Longitud de Trayectoria (m)", value=50)
    
    st.header("🌍 Factores de Ajuste (NOM 310-15)")
    t_amb = st.select_slider("Temp. Ambiente (°C)", options=[30, 35, 40, 45, 50], value=30)
    num_cond = st.number_input("Conductores Portadores en Grupo", value=3, min_value=1)

# --- 3. LÓGICA DE CÁLCULO Y VALIDACIÓN NOM ---
# Factores de corrección
f_temp = {30: 1.0, 35: 0.94, 40: 0.88, 45: 0.82, 50: 0.75}.get(t_amb, 1.0)
f_agrup = 1.0 if num_cond <= 3 else (0.8 if num_cond <= 6 else 0.7)

# Corriente de Diseño (I_nom * 1.25)
i_nom = (potencia * 746) / (voltaje * 1.732 * 0.85 * 0.90)
i_diseno = i_nom * 1.25

def motor_seleccion_socemb(i_target):
    for cal, d in DATOS_OKONITE.items():
        # Validar Terminal (NOM 110-14c): 60°C si I <= 100A, sino 75°C
        lim_term = d["60C"] if i_target <= 100 else d["75C"]
        
        # Validar Derating (Sobre 90°C del C-L-X)
        cap_corregida = d["90C"] * f_temp * f_agrup
        
        if i_target <= lim_term and i_target <= cap_corregida:
            # Validar Caída de Tensión (Límite 3%)
            v_drop = (1.732 * i_nom * distancia * RES_CU[cal]) / (voltaje * 10)
            if v_drop <= 3.0:
                return cal, round(v_drop, 2), lim_term, round(cap_corregida, 2)
    return "500 kcmil", 0, 0, 0

calibre_final, vd_final, cap_term, cap_adj = motor_seleccion_socemb(i_diseno)

# --- 4. PANEL DE CONTROL Y REGISTRO ---
c1, c2, c3 = st.columns(3)
c1.metric("Ampacidad de Diseño", f"{round(i_diseno, 2)} A")
c2.metric("Calibre Seleccionado", calibre_final)
c3.metric("Caída de Tensión", f"{vd_final}%")

with st.expander("Detalles Técnicos de Cumplimiento"):
    st.info(f"Capacidad de Terminal aplicada: {cap_term} A")
    st.info(f"Ampacidad Corregida por Derating (Ft: {f_temp}, Fa: {f_agrup}): {cap_adj} A")

if st.button("➕ Agregar al Cable Schedule"):
    st.session_state.schedule.append({
        "TAG": tag, "DESCRIPCIÓN": desc, "CHAROLA": charola,
        "POTENCIA (HP)": potencia, "V": voltaje, "I DIS (A)": round(i_diseno, 2),
        "CALIBRE": calibre_final, "VD %": vd_final, 
        "ÁREA (mm2)": DATOS_OKONITE[calibre_final]["area"]
    })
    st.toast(f"Circuito {tag} registrado con éxito.")

# --- 5. REPORTE DE LLENADO DE CHAROLAS ---
if st.session_state.schedule:
    df = pd.DataFrame(st.session_state.schedule)
    st.subheader("📊 Análisis de Llenado de Charolas (NOM-001-SEDE Art. 392)")
    
    # Agrupar áreas por charola
    res_tray = df.groupby("CHAROLA")["ÁREA (mm2)"].sum().reset_index()
    
    def sizing_tray(area_total):
        for ancho, area_util in ANCHOS_CHAROLA_4IN.items():
            if area_total <= (area_util * 0.40):
                return f"{ancho}\" ({ancho*25.4} mm)", f"{round((area_total/(area_util * 0.4))*100, 1)}%"
        return "SOBRESATURADA", "100%+"

    res_tray[['Ancho Sugerido', 'Llenado (%)']] = res_tray['ÁREA (mm2)'].apply(lambda x: pd.Series(sizing_tray(x)))
    st.table(res_tray)
    
    st.subheader("📝 Cable Schedule SOCEMB")
    st.dataframe(df)

    # Exportación a Excel
    towrite = io.BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    st.download_button("📥 Descargar Excel", towrite.getvalue(), file_name="SOCEMB_Schedule.xlsx")
