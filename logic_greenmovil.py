import streamlit as st
import pandas as pd
from datetime import datetime, date
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
    st.markdown("## 👥 Personal de Operaciones (Greenmovil)")
    st.info("💡 **Configuración Dinámica:** Registra a los Técnicos de Control, Auxiliares de Ejecución de la operación e Inspectores de Seguridad Operacional.")
    
    st.markdown("### 📥 Carga Masiva desde Excel")
    st.caption("Asegúrate de que tu archivo tenga en la primera fila las columnas: **Cedula**, **Nombre** y **Cargo**.")
    archivo_personal = st.file_uploader("Sube tu plantilla de personal (.xlsx o .xls):", type=["xlsx", "xls"], key="up_pers_grn")
    
    if archivo_personal is not None:
        if st.button("🔄 Importar y Guardar Plantilla", key="btn_imp_pers_grn"):
            try:
                df_cargado = pd.read_excel(archivo_personal)
                cols_esperadas = ["Cedula", "Nombre", "Cargo"]
                cols_missing = [c for c in cols_esperadas if c not in df_cargado.columns]
                
                if cols_missing:
                    st.error(f"❌ Faltan las siguientes columnas en el Excel: {', '.join(cols_missing)}")
                else:
                    df_cargado["Cedula"] = df_cargado["Cedula"].fillna(0).astype(int).astype(str)
                    if "Grupo" not in df_cargado.columns: df_cargado["Grupo"] = "Sin Grupo"
                    else: df_cargado["Grupo"] = df_cargado["Grupo"].fillna("Sin Grupo").astype(str)
                        
                    df_limpio = df_cargado[["Cedula", "Nombre", "Cargo", "Grupo"]]
                    guardar_tabla(df_limpio, "green_personal")
                    st.success("✅ ¡Personal cargado y guardado en la base de datos con éxito!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al leer el archivo: {str(e)}")

    st.write("---")
    df_pers = cargar_tabla("green_personal")
    if df_pers.empty:
        df_pers = pd.DataFrame({"Cedula": [""], "Nombre": [""], "Cargo": [""], "Grupo": [""]})
        
    st.markdown("### 📝 Editor de Empleados y Grupos")
    df_edit = st.data_editor(
        df_pers, num_rows="dynamic", use_container_width=True,
        column_config={
            "Cedula": st.column_config.TextColumn("🆔 Cédula", required=True),
            "Nombre": st.column_config.TextColumn("👤 Nombre Completo", required=True),
            "Cargo": st.column_config.TextColumn("💼 Cargo", required=True),
            "Grupo": st.column_config.TextColumn("📦 Grupo de Trabajo", required=True)
        }, key="edit_pers_green"
    )
    
    if st.button("💾 Guardar Cambios en Personal", key="btn_guar_pers_grn2"):
        df_edit = df_edit[df_edit["Nombre"].str.strip() != ""]
        guardar_tabla(df_edit, "green_personal")
        st.success(f"✅ ¡{len(df_edit)} empleados registrados exitosamente!")


# =========================================================
# 3. PARAMETRIZADOR (TURNOS Y REGLAS)
# =========================================================
def pantalla_parametrizador_green():
    st.markdown("## ⚙️ Parametrizador Operativo (Greenmovil)")
    st.info("Aquí defines los catálogos base que el motor de mallas utilizará para rotar a tu personal.")
    
    st.markdown("### 🕒 Catálogo de Turnos por Cargo")
    st.caption("Vincula cada turno al Cargo correspondiente. Usa la palabra **Todos** si un turno aplica para cualquier empleado.")
    
    df_turnos = cargar_tabla("green_turnos")
    if df_turnos.empty:
        df_turnos = pd.DataFrame({
            "Nombre": ["Mañana Control", "Tarde Auxiliar", "Oficina Inspector"], 
            "Inicio": ["06:00", "14:00", "08:00"], 
            "Fin": ["13:00", "21:00", "16:00"],
            "Cargo Aplicable": ["Técnicos de Control", "Auxiliares de Ejecución de la operación", "Inspectores de Seguridad Operacional"]
        })
        
    df_edit_t = st.data_editor(
        df_turnos, num_rows="dynamic", use_container_width=True,
        column_config={
            "Nombre": st.column_config.TextColumn("Etiqueta del Turno", required=True),
            "Inicio": st.column_config.TextColumn("Hora Inicio (HH:MM)", required=True),
            "Fin": st.column_config.TextColumn("Hora Fin (HH:MM)", required=True),
            "Cargo Aplicable": st.column_config.TextColumn("Aplica para (Escribe el Cargo)", required=True)
        }, key="edit_turnos_green"
    )
    if st.button("💾 Guardar Catálogo de Turnos", key="btn_guar_t_green"):
        guardar_tabla(df_edit_t, "green_turnos")
        st.success("✅ Turnos especializados guardados correctamente.")


# =========================================================
# 4. MOTOR Y PANEL DE MALLAS DE OPERACIONES
# =========================================================
def calcular_horas_y_recargos(ini_str, fin_str):
    if ini_str == "OFF" or fin_str == "OFF": return 0.0, 0.0, 0.0
    try:
        t_ini, t_fin = datetime.strptime(ini_str, "%H:%M"), datetime.strptime(fin_str, "%H:%M")
    except: return 0.0, 0.0, 0.0
    
    min_ini = t_ini.hour * 60 + t_ini.minute
    min_fin = t_fin.hour * 60 + t_fin.minute
    minutos_totales = (min_fin - min_ini) if min_fin >= min_ini else ((1440 - min_ini) + min_fin)
    total_horas = minutos_totales / 60.0
    
    horas_extras = max(0.0, total_horas - 7.0)
    
    minutos_nocturnos = 0
    m_actual = min_ini
    for _ in range(int(minutos_totales)):
        min_ciclo = m_actual % 1440
        if min_ciclo >= 1140 or min_ciclo < 360: minutos_nocturnos += 1
        m_actual += 1
        
    return round(total_horas, 2), round(horas_extras, 2), round(minutos_nocturnos / 60.0, 2)

def evaluar_fatiga(turno_ayer_fin, turno_hoy_ini):
    if turno_ayer_fin == "OFF" or turno_hoy_ini == "OFF": return True
    t_fin, t_ini = datetime.strptime(turno_ayer_fin, "%H:%M"), datetime.strptime(turno_hoy_ini, "%H:%M")
    m_fin = t_fin.hour * 60 + t_fin.minute
    m_ini = t_ini.hour * 60 + t_ini.minute
    descanso = (1440 - m_fin) + m_ini
    return descanso >= 480

def generar_malla_dinamica(inicio, fin, df_personal, df_turnos, d_descansos):
    filas = []
    df_turnos = df_turnos.copy()
    df_turnos['min_ini'] = df_turnos['Inicio'].apply(lambda x: datetime.strptime(x, "%H:%M").hour * 60 if x != "OFF" else 0)
    
    historia_fase = {row["Grupo"]: 0 for _, row in df_personal.drop_duplicates("Grupo").iterrows()}
    ayer_fin = {row["Grupo"]: "OFF" for _, row in df_personal.iterrows()}
    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    
    for fecha in pd.date_range(inicio, fin):
        dia_n = dias_semana[fecha.weekday()]
        
        for _, p in df_personal.iterrows():
            cedula, nombre, grupo, cargo = p.get("Cedula", "N/A"), p["Nombre"], p["Grupo"], p["Cargo"]
            turno_hoy, ini_hoy, fin_hoy = "DESCANSO", "OFF", "OFF"
            
            turnos_validos_cargo = df_turnos[
                (df_turnos["Cargo Aplicable"].str.contains(str(cargo), case=False, na=False)) | 
                (df_turnos["Cargo Aplicable"].str.strip().str.upper() == "TODOS")
            ].sort_values('min_ini')
            lista_nombres_turnos = turnos_validos_cargo['Nombre'].tolist()
            
            if d_descansos.get(grupo) == dia_n:
                turno_hoy = "DESCANSO"
                if len(lista_nombres_turnos) > 0: historia_fase[grupo] = (historia_fase[grupo] + 1) % len(lista_nombres_turnos)
            else:
                if len(lista_nombres_turnos) > 0:
                    idx_fase = historia_fase[grupo] % len(lista_nombres_turnos)
                    turno_propuesto = lista_nombres_turnos[idx_fase]
                    datos_t = turnos_validos_cargo.iloc[idx_fase]
                    ini_prop = datos_t["Inicio"]
                    
                    if evaluar_fatiga(ayer_fin[grupo], ini_prop):
                        turno_hoy, ini_hoy, fin_hoy = turno_propuesto, ini_prop, datos_t["Fin"]
                    else:
                        turno_hoy, ini_hoy, fin_hoy = "RELEVO FATIGA", "08:00", "15:00"
                else:
                    turno_hoy = "SIN TURNO CONFIGURADO"
            
            h_tot, h_ext, h_noc = calcular_horas_y_recargos(ini_hoy, fin_hoy)
            ayer_fin[grupo] = fin_hoy
            
            filas.append({
                "Fecha": fecha.strftime('%Y-%m-%d'), "Cedula": cedula, "Nombre": nombre, "Grupo": grupo, "Cargo": cargo,
                "Turno": turno_hoy, "Inicio": ini_hoy, "Fin": fin_hoy,
                "Hrs Prog": h_tot, "Hrs Extras": h_ext, "Recargos Noct": h_noc
            })
    return pd.DataFrame(filas)

def style_malla_green(df_pivot):
    styles = pd.DataFrame('', index=df_pivot.index, columns=df_pivot.columns)
    for col in df_pivot.columns:
        for idx in df_pivot.index:
            val = str(df_pivot.at[idx, col]).strip()
            if val == "DESCANSO": bg, txt = "#1B2631", "white"
            elif val == "RELEVO FATIGA": bg, txt = "#E74C3C", "white"
            elif val == "SIN TURNO CONFIGURADO": bg, txt = "#F39C12", "white"
            else: bg, txt = "#D6EAF8", "#17202A" # Color base para turnos
            
            styles.at[idx, col] = f'background-color: {bg}; color: {txt}; font-weight: 700; border: 0.5px solid #D5DBDB;'
    return df_pivot.style.apply(lambda _: styles, axis=None)

def pantalla_mallas_green():
    st.markdown("## 📅 Mallas de Operaciones (Greenmovil)")
    st.info("Generación de turnos adaptativa con filtro por áreas de operación.")
    
    df_pers = cargar_tabla("green_personal")
    df_turnos = cargar_tabla("green_turnos")
    
    if df_pers.empty or df_turnos.empty:
        st.warning("⚠️ Asegúrate de registrar personal y configurar turnos en el Parametrizador antes de generar la malla.")
        return
        
    grupos_unicos = df_pers["Grupo"].unique()
    
    st.markdown("### ⚙️ Configuración de Generación")
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Inicio", date(2026, 7, 1), key="i_grn_m")
    fin = c2.date_input("Fin", date(2026, 12, 31), key="f_grn_m")
    
    st.markdown("**Asignar Día de Descanso por Grupo:**")
    cols = st.columns(min(len(grupos_unicos), 6) if len(grupos_unicos) > 0 else 1)
    d_desc = {}
    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    for i, g in enumerate(grupos_unicos):
        d_desc[g] = cols[i % 6].selectbox(f"Descanso {g}", dias_semana, index=i % 7, key=f"d_grn_m_{g}")
        
    if st.button("🚀 GENERAR MALLA INTELIGENTE", key="btn_gen_grn_m"):
        st.session_state.m_base_grn = generar_malla_dinamica(inicio, fin, df_pers, df_turnos, d_desc)
        
    if 'm_base_grn' in st.session_state and not st.session_state.m_base_grn.empty:
        df_malla = st.session_state.m_base_grn
        
        st.write("---")
        st.subheader("📋 Explorador de Mallas Operativas")
        
        # --- FILTRO DINÁMICO POR CARGO ---
        cargos_presentes = ["General (Toda la Planta)"] + sorted(list(df_malla["Cargo"].unique()))
        vista_sel = st.selectbox("👁️ Filtrar Vista de Malla por Cargo:", cargos_presentes)
        
        if vista_sel == "General (Toda la Planta)": df_vista = df_malla
        else: df_vista = df_malla[df_malla["Cargo"] == vista_sel]
            
        pivot = df_vista.pivot(index=["Cargo", "Grupo", "Cedula", "Nombre"], columns="Fecha", values="Turno").fillna("DESCANSO")
        st.dataframe(style_malla_green(pivot), use_container_width=True)
        
        st.write("---")
        st.subheader("💰 Resumen de Nómina y Reforma Laboral (7h)")
        resumen = df_vista.groupby(["Cargo", "Grupo", "Cedula", "Nombre"])[["Hrs Prog", "Hrs Extras", "Recargos Noct"]].sum().reset_index()
        st.dataframe(resumen, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer: 
            df_vista.to_excel(writer, sheet_name="Detalle_Operacion", index=False)
            resumen.to_excel(writer, sheet_name="Nomina_Consolidada", index=False)
        st.download_button("📥 Descargar Reporte de la Vista Actual (.xlsx)", output.getvalue(), f"Reporte_{vista_sel}_{date.today()}.xlsx", key="dw_grn_m")
