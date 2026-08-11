import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
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
# 3. PARAMETRIZADOR (TURNOS, REGLAS Y NOVEDADES)
# =========================================================
def pantalla_parametrizador_green():
    st.markdown("## ⚙️ Parametrizador Operativo (Greenmovil)")
    st.info("Aquí defines los catálogos base que el motor de mallas utilizará para rotar a tu personal y controlar la cobertura.")
    
    t_turnos, t_novedades = st.tabs(["🕒 Catálogo de Turnos", "🌴 Gestor de Novedades (Ausentismos)"])
    
    with t_turnos:
        st.markdown("### 🕒 Configuración de Turnos y Requeridos")
        st.caption("Vincula cada turno al Cargo correspondiente y define la meta de cobertura diaria.")
        
        df_turnos = cargar_tabla("green_turnos")
        if df_turnos.empty:
            df_turnos = pd.DataFrame({
                "Nombre": ["Mañana Control", "Tarde Auxiliar", "Oficina Inspector"], 
                "Inicio": ["06:00", "14:00", "08:00"], 
                "Fin": ["13:00", "21:00", "16:00"],
                "Cargo Aplicable": ["Técnicos de Control", "Auxiliares de Ejecución de la operación", "Inspectores de Seguridad Operacional"],
                "Requeridos": [2, 4, 1]
            })
            
        df_edit_t = st.data_editor(
            df_turnos, num_rows="dynamic", use_container_width=True,
            column_config={
                "Nombre": st.column_config.TextColumn("Etiqueta del Turno", required=True),
                "Inicio": st.column_config.TextColumn("Hora Inicio (HH:MM)", required=True),
                "Fin": st.column_config.TextColumn("Hora Fin (HH:MM)", required=True),
                "Cargo Aplicable": st.column_config.TextColumn("Aplica para (Escribe el Cargo)", required=True),
                "Requeridos": st.column_config.NumberColumn("Meta Cobertura", min_value=1, default=1, required=True)
            }, key="edit_turnos_green"
        )
        if st.button("💾 Guardar Catálogo de Turnos", key="btn_guar_t_green"):
            guardar_tabla(df_edit_t, "green_turnos")
            st.success("✅ Turnos y requerimientos guardados correctamente.")

    with t_novedades:
        st.markdown("### 🌴 Registro de Novedades")
        st.caption("Registra vacaciones, licencias o incapacidades. El sistema bloqueará los turnos en estas fechas y alertará sobre la falta de cobertura.")
        
        df_pers_nov = cargar_tabla("green_personal")
        nombres_lista = df_pers_nov["Nombre"].tolist() if not df_pers_nov.empty else ["No hay personal"]
        
        df_nov = cargar_tabla("green_novedades")
        if df_nov.empty:
            df_nov = pd.DataFrame({"Nombre": [""], "Tipo Novedad": [""], "Inicio": [date.today().strftime('%Y-%m-%d')], "Fin": [date.today().strftime('%Y-%m-%d')]})
            
        df_edit_n = st.data_editor(
            df_nov, num_rows="dynamic", use_container_width=True,
            column_config={
                "Nombre": st.column_config.SelectboxColumn("👤 Empleado", options=nombres_lista, required=True),
                "Tipo Novedad": st.column_config.SelectboxColumn("⚠️ Tipo de Novedad", options=["Vacaciones", "Incapacidad", "Licencia", "Permiso"], required=True),
                "Inicio": st.column_config.DateColumn("📅 Fecha Inicio", format="YYYY-MM-DD", required=True),
                "Fin": st.column_config.DateColumn("📅 Fecha Fin", format="YYYY-MM-DD", required=True)
            }, key="edit_nov_green"
        )
        if st.button("💾 Guardar Novedades", key="btn_guar_nov_green"):
            df_edit_n = df_edit_n[df_edit_n["Nombre"].str.strip() != ""]
            guardar_tabla(df_edit_n, "green_novedades")
            st.success("✅ Novedades registradas exitosamente.")

# =========================================================
# 4. MOTOR DE ASIGNACIÓN DINÁMICA (CON NOVEDADES)
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

def generar_malla_dinamica(inicio, fin, df_personal, df_turnos, d_descansos, df_novedades):
    filas = []
    df_turnos = df_turnos.copy()
    df_turnos['min_ini'] = df_turnos['Inicio'].apply(lambda x: datetime.strptime(x, "%H:%M").hour * 60 if x != "OFF" else 0)
    
    historia_fase = {row["Grupo"]: 0 for _, row in df_personal.drop_duplicates("Grupo").iterrows()}
    ayer_fin = {row["Grupo"]: "OFF" for _, row in df_personal.iterrows()}
    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    
    for fecha in pd.date_range(inicio, fin):
        dia_n = dias_semana[fecha.weekday()]
        fecha_str = fecha.strftime('%Y-%m-%d')
        
        for _, p in df_personal.iterrows():
            cedula, nombre, grupo, cargo = p.get("Cedula", "N/A"), p["Nombre"], p["Grupo"], p["Cargo"]
            turno_hoy, ini_hoy, fin_hoy = "DESCANSO", "OFF", "OFF"
            
            # --- EVALUACIÓN DE NOVEDADES ---
            novedad_activa = None
            if not df_novedades.empty:
                for _, nov in df_novedades[df_novedades["Nombre"] == nombre].iterrows():
                    try:
                        dt_ini = pd.to_datetime(nov["Inicio"])
                        dt_fin = pd.to_datetime(nov["Fin"])
                        if dt_ini <= fecha <= dt_fin:
                            novedad_activa = f"⚠️ {nov['Tipo Novedad']}"
                            break
                    except: pass

            turnos_validos_cargo = df_turnos[
                (df_turnos["Cargo Aplicable"].str.contains(str(cargo), case=False, na=False)) | 
                (df_turnos["Cargo Aplicable"].str.strip().str.upper() == "TODOS")
            ].sort_values('min_ini')
            lista_nombres_turnos = turnos_validos_cargo['Nombre'].tolist()
            
            # --- LÓGICA DE ASIGNACIÓN ---
            if novedad_activa:
                turno_hoy = novedad_activa
            elif d_descansos.get(grupo) == dia_n:
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
                    turno_hoy = "SIN TURNO"
            
            # --- EDITOR MANUAL (SOBREESCRIBE CUALQUIER COSA) ---
            if "ajustes_manuales_grn" in st.session_state and (nombre, fecha_str) in st.session_state.ajustes_manuales_grn:
                turno_manual = st.session_state.ajustes_manuales_grn[(nombre, fecha_str)]
                turno_hoy = turno_manual
                if turno_manual not in ["DESCANSO", "RELEVO FATIGA", "SIN TURNO"] and not turno_manual.startswith("⚠️"):
                    datos_t = df_turnos[df_turnos["Nombre"] == turno_manual].iloc[0]
                    ini_hoy, fin_hoy = datos_t["Inicio"], datos_t["Fin"]
                else:
                    ini_hoy, fin_hoy = "OFF", "OFF"
            
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
            elif "⚠️" in val: bg, txt = "#E67E22", "white" # Naranja para Novedades
            elif val == "RELEVO FATIGA": bg, txt = "#E74C3C", "white" # Rojo
            elif val == "SIN TURNO": bg, txt = "#F39C12", "white"
            else: bg, txt = "#D6EAF8", "#17202A" # Color base azul
            
            styles.at[idx, col] = f'background-color: {bg}; color: {txt}; font-weight: 700; border: 0.5px solid #D5DBDB;'
    return df_pivot.style.apply(lambda _: styles, axis=None)

# --- POP-UP GESTOR MANUAL ---
@st.dialog("🛠️ Forzar Cobertura / Turno (Greenmovil)", width="small")
def popup_forzar_ajuste_fecha_grn(fecha_solicitada, opciones_sujetos, opciones_turnos):
    st.markdown(f"📅 **Fecha:** `{fecha_solicitada}`")
    sujeto_sel = st.selectbox("🎯 Empleado a reasignar:", opciones_sujetos, key="sel_suj_grn_pu")
    
    opciones_totales = ["DESCANSO", "RELEVO FATIGA"] + opciones_turnos
    nuevo_turno = st.selectbox("🆕 Turno o Cobertura:", opciones_totales, index=0, key="sel_tur_grn_pu")
    
    if st.button("💾 Guardar y Re-calcular Malla", key="btn_guar_grn_pu"):
        st.session_state.ajustes_manuales_grn[(sujeto_sel, fecha_solicitada)] = nuevo_turno
        st.success("¡Asignación guardada!")
        st.rerun()

# =========================================================
# 5. PANEL DE MALLAS Y AUDITORÍA
# =========================================================
def pantalla_mallas_green():
    if "ajustes_manuales_grn" not in st.session_state: st.session_state.ajustes_manuales_grn = {}
    
    st.markdown("## 📅 Mallas de Operaciones (Greenmovil)")
    st.info("Generación de turnos adaptativa con validación automática de ausentismos y coberturas.")
    
    df_pers = cargar_tabla("green_personal")
    df_turnos = cargar_tabla("green_turnos")
    df_nov = cargar_tabla("green_novedades")
    
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
        st.session_state.m_base_grn = generar_malla_dinamica(inicio, fin, df_pers, df_turnos, d_desc, df_nov)
        
    if 'm_base_grn' in st.session_state and not st.session_state.m_base_grn.empty:
        df_malla = st.session_state.m_base_grn
        
        st.write("---")
        st.subheader("📋 Explorador de Mallas Operativas")
        
        cargos_presentes = ["General (Toda la Planta)"] + sorted(list(df_malla["Cargo"].unique()))
        vista_sel = st.selectbox("👁️ Filtrar Vista de Malla por Cargo:", cargos_presentes)
        
        if vista_sel == "General (Toda la Planta)": df_vista = df_malla
        else: df_vista = df_malla[df_malla["Cargo"] == vista_sel]
            
        pivot = df_vista.pivot(index=["Cargo", "Grupo", "Cedula", "Nombre"], columns="Fecha", values="Turno").fillna("DESCANSO")
        st.dataframe(style_malla_green(pivot), use_container_width=True)
        
        # --- GESTOR DE COBERTURA MANUAL ---
        st.write("---")
        st.subheader("🛠️ Gestor de Coberturas Manuales")
        st.caption("Usa este panel para asignar reemplazos cuando la auditoría muestre faltantes por novedades.")
        with st.expander("🔍 Forzar cambio o cobertura en Malla", expanded=False):
            c_f1, c_f2 = st.columns(2)
            f_libre_sel = c_f1.selectbox("Seleccione la Fecha:", list(pivot.columns), key="f_libre_dropdown_grn")
            if c_f2.button("⚙️ Abrir Gestor de Turnos", use_container_width=True, key="btn_gestor_grn"):
                popup_forzar_ajuste_fecha_grn(f_libre_sel, sorted(list(df_malla["Nombre"].unique())), df_turnos["Nombre"].tolist())

        # --- AUDITORÍA DE COBERTURA ---
        st.write("---")
        st.subheader("📊 Auditoría de Cobertura vs. Requeridos")
        
        # Cruzar turnos asignados vs turnos requeridos
        auditoria = df_vista.groupby(["Fecha", "Turno"]).size().unstack(fill_value=0)
        
        # Si estamos en la vista General, podemos evaluar todos los turnos.
        if vista_sel == "General (Toda la Planta)":
            alertas_cobertura = 0
            for col in auditoria.columns:
                if col in df_turnos["Nombre"].values:
                    requerido = df_turnos[df_turnos["Nombre"] == col]["Requeridos"].values[0]
                    # Identificamos los días que no cumplen
                    dias_deficit = auditoria[auditoria[col] < requerido].index
                    if not dias_deficit.empty:
                        st.warning(f"📉 **Déficit en Turno '{col}':** La meta es {requerido} personas, pero hay falta de personal en {len(dias_deficit)} días (Posibles Novedades).")
                        alertas_cobertura += 1
            if alertas_cobertura == 0:
                st.success("✅ **Cobertura Perfecta:** Todos los turnos cumplen con la meta de personal requerido.")

        auditoria.index = [p for p in auditoria.index]
        st.dataframe(auditoria, use_container_width=True)

        # --- REPORTE DE NÓMINA ---
        st.write("---")
        st.subheader("💰 Resumen de Nómina y Reforma Laboral (7h)")
        resumen = df_vista.groupby(["Cargo", "Grupo", "Cedula", "Nombre"])[["Hrs Prog", "Hrs Extras", "Recargos Noct"]].sum().reset_index()
        st.dataframe(resumen, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer: 
            df_vista.to_excel(writer, sheet_name="Detalle_Operacion", index=False)
            resumen.to_excel(writer, sheet_name="Nomina_Consolidada", index=False)
        st.download_button("📥 Descargar Reporte de la Vista Actual (.xlsx)", output.getvalue(), f"Reporte_{vista_sel}_{date.today()}.xlsx", key="dw_grn_m")
