import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date, time
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import io

# =========================================================
# 1. CONEXIÓN Y PERSISTENCIA (GREENMOVIL)
# =========================================================
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///movilgo_local.db")
engine = create_engine(DATABASE_URL)

def cargar_tabla(nombre_tabla):
    try:
        return pd.read_sql(f"SELECT * FROM {nombre_tabla}", engine)
    except Exception:
        return pd.DataFrame()

def guardar_tabla(df, nombre_tabla):
    try:
        df.to_sql(nombre_tabla, engine, if_exists="replace", index=False)
        return True
    except Exception as e:
        st.error(f"Error guardando en BD: {e}")
        return False

# =========================================================
# 2. PANEL DE PERSONAL Y CARGOS DINÁMICOS
# =========================================================
def pantalla_personal_green():
    st.markdown("## 👥 Personal y Cargos (Greenmovil)")
    st.info("💡 **Configuración Dinámica:** Aquí puedes crear cualquier cargo, grupo o rol que necesite la empresa.")
    
    # Cargar o inicializar personal
    df_pers = cargar_tabla("green_personal")
    if df_pers.empty:
        df_pers = pd.DataFrame({"Nombre": [""], "Cargo": [""], "Grupo": [""]})
        
    st.markdown("### 📝 Editor de Empleados")
    df_edit = st.data_editor(
        df_pers, 
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Nombre": st.column_config.TextColumn("👤 Nombre Completo", required=True),
            "Cargo": st.column_config.TextColumn("💼 Cargo / Rol", required=True),
            "Grupo": st.column_config.TextColumn("📦 Grupo de Trabajo", required=True)
        },
        key="edit_pers_green"
    )
    
    if st.button("💾 Guardar Personal", key="btn_guar_pers_green"):
        # Limpiar filas vacías
        df_edit = df_edit[df_edit["Nombre"].str.strip() != ""]
        guardar_tabla(df_edit, "green_personal")
        st.success(f"✅ ¡{len(df_edit)} empleados registrados exitosamente!")

# =========================================================
# 3. MOTOR Y PANEL DE PROGRAMACIÓN DINÁMICA
# =========================================================
def calcular_horas_y_recargos(ini_str, fin_str):
    if ini_str == "OFF" or fin_str == "OFF": return 0.0, 0.0, 0.0
    try:
        t_ini = datetime.strptime(ini_str, "%H:%M")
        t_fin = datetime.strptime(fin_str, "%H:%M")
    except: return 0.0, 0.0, 0.0
    
    min_ini = t_ini.hour * 60 + t_ini.minute
    min_fin = t_fin.hour * 60 + t_fin.minute
    
    minutos_totales = (min_fin - min_ini) if min_fin >= min_ini else ((1440 - min_ini) + min_fin)
    total_horas = minutos_totales / 60.0
    
    # REFORMA LABORAL: Turno de 7h netas (exceso es extra)
    horas_extras = max(0.0, total_horas - 7.0)
    
    minutos_nocturnos = 0
    m_actual = min_ini
    for _ in range(minutos_totales):
        min_ciclo = m_actual % 1440
        if min_ciclo >= 1140 or min_ciclo < 360: minutos_nocturnos += 1  # 19:00 a 06:00
        m_actual += 1
        
    return round(total_horas, 2), round(horas_extras, 2), round(minutos_nocturnos / 60.0, 2)

def evaluar_fatiga(turno_ayer_fin, turno_hoy_ini):
    if turno_ayer_fin == "OFF" or turno_hoy_ini == "OFF": return True
    t_fin = datetime.strptime(turno_ayer_fin, "%H:%M")
    t_ini = datetime.strptime(turno_hoy_ini, "%H:%M")
    
    m_fin = t_fin.hour * 60 + t_fin.minute
    m_ini = t_ini.hour * 60 + t_ini.minute
    
    # Tiempo de descanso (si hoy entra al día siguiente)
    descanso = (1440 - m_fin) + m_ini
    return descanso >= 480  # Mínimo 8 horas (480 minutos) de sueño

def generar_malla_dinamica(inicio, fin, df_personal, df_turnos, d_descansos):
    filas = []
    # Ordenar turnos por hora de inicio para la rotación ascendente
    df_turnos['min_ini'] = df_turnos['Inicio'].apply(lambda x: datetime.strptime(x, "%H:%M").hour * 60)
    turnos_ordenados = df_turnos.sort_values('min_ini')['Nombre'].tolist()
    
    historia_fase = {row["Grupo"]: idx % len(turnos_ordenados) for idx, row in df_personal.drop_duplicates("Grupo").iterrows()}
    ayer_fin = {row["Grupo"]: "OFF" for _, row in df_personal.iterrows()}
    
    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    
    for fecha in pd.date_range(inicio, fin):
        dia_n = dias_semana[fecha.weekday()]
        
        for _, p in df_personal.iterrows():
            nombre, grupo = p["Nombre"], p["Grupo"]
            turno_hoy = "DESCANSO"
            ini_hoy, fin_hoy = "OFF", "OFF"
            
            # 1. Verificar si es su día de descanso
            if d_descansos.get(grupo) == dia_n:
                turno_hoy = "DESCANSO"
                # Al descansar, avanza a la siguiente fase de rotación
                historia_fase[grupo] = (historia_fase[grupo] + 1) % len(turnos_ordenados)
            else:
                # 2. Asignar turno de su fase actual
                turno_propuesto = turnos_ordenados[historia_fase[grupo]]
                datos_t = df_turnos[df_turnos["Nombre"] == turno_propuesto].iloc[0]
                ini_prop = datos_t["Inicio"]
                
                # 3. Control estricto de Fatiga
                if evaluar_fatiga(ayer_fin[grupo], ini_prop):
                    turno_hoy = turno_propuesto
                    ini_hoy, fin_hoy = ini_prop, datos_t["Fin"]
                else:
                    turno_hoy = "RELEVO FATIGA"
                    ini_hoy, fin_hoy = "08:00", "15:00" # Turno seguro por defecto
            
            h_tot, h_ext, h_noc = calcular_horas_y_recargos(ini_hoy, fin_hoy)
            ayer_fin[grupo] = fin_hoy
            
            filas.append({
                "Fecha": fecha.strftime('%Y-%m-%d'), "Nombre": nombre, "Grupo": grupo, "Cargo": p["Cargo"],
                "Turno": turno_hoy, "Inicio": ini_hoy, "Fin": fin_hoy,
                "Hrs Prog": h_tot, "Hrs Extras": h_ext, "Recargos Noct": h_noc
            })
            
    return pd.DataFrame(filas)

def pantalla_programador_green():
    st.markdown("## 🔧 Generador de Mallas (Greenmovil)")
    
    # --- GESTIÓN DINÁMICA DE TURNOS ---
    st.markdown("### 🕒 Creador de Turnos Dinámicos")
    df_turnos = cargar_tabla("green_turnos")
    if df_turnos.empty:
        df_turnos = pd.DataFrame({"Nombre": ["Mañana", "Tarde", "Noche"], "Inicio": ["06:00", "13:00", "20:00"], "Fin": ["13:00", "20:00", "06:00"]})
        
    df_edit_t = st.data_editor(
        df_turnos, num_rows="dynamic", use_container_width=True,
        column_config={
            "Nombre": st.column_config.TextColumn("Etiqueta del Turno", required=True),
            "Inicio": st.column_config.TextColumn("Hora Inicio (HH:MM)", required=True),
            "Fin": st.column_config.TextColumn("Hora Fin (HH:MM)", required=True)
        }, key="edit_turnos_green"
    )
    if st.button("💾 Guardar Catálogo de Turnos", key="btn_guar_t_green"):
        guardar_tabla(df_edit_t, "green_turnos")
        st.success("✅ Turnos personalizados guardados.")
        
    st.write("---")
    df_pers = cargar_tabla("green_personal")
    if df_pers.empty:
        st.warning("⚠️ Primero debes ir a '👥 Personal' y registrar empleados para generar la malla.")
        return
        
    grupos_unicos = df_pers["Grupo"].unique()
    
    st.markdown("### 📅 Configuración de Malla y Descansos")
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Inicio", date(2026, 7, 1), key="i_grn")
    fin = c2.date_input("Fin", date(2026, 12, 31), key="f_grn")
    
    st.markdown("**Asignar Día de Descanso por Grupo:**")
    cols = st.columns(min(len(grupos_unicos), 6))
    d_desc = {}
    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    for i, g in enumerate(grupos_unicos):
        d_desc[g] = cols[i % 6].selectbox(f"Descanso {g}", dias_semana, index=i % 7, key=f"d_grn_{g}")
        
    if st.button("🚀 GENERAR MALLA INTELIGENTE", key="btn_gen_grn"):
        df_malla = generar_malla_dinamica(inicio, fin, df_pers, df_edit_t, d_desc)
        
        st.write("---")
        st.subheader("📋 Malla Dinámica Generada")
        pivot = df_malla.pivot(index=["Grupo", "Cargo", "Nombre"], columns="Fecha", values="Turno").fillna("DESCANSO")
        st.dataframe(pivot, use_container_width=True)
        
        st.subheader("💰 Resumen de Nómina y Reforma Laboral (7h)")
        resumen = df_malla.groupby(["Nombre", "Cargo", "Grupo"])[["Hrs Prog", "Hrs Extras", "Recargos Noct"]].sum().reset_index()
        st.dataframe(resumen, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer: 
            df_malla.to_excel(writer, sheet_name="Detalle", index=False)
            resumen.to_excel(writer, sheet_name="Nómina", index=False)
        st.download_button("📥 Descargar Reporte Completo (.xlsx)", output.getvalue(), f"Nomina_Greenmovil_{date.today()}.xlsx", key="dw_grn")
