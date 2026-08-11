import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import io
import math

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
# 2. PANEL DE PERSONAL DINÁMICO (SIN GRUPOS FIJOS)
# =========================================================
def pantalla_personal_green():
    st.markdown("## 👥 Personal de Operaciones (Greenmovil)")
    st.info("💡 **Programación Individual:** Cada empleado tiene su propia zona y día de descanso base (El algoritmo ajustará el descanso si hacen turnos especiales).")
    
    st.markdown("### 📥 Carga Masiva desde Excel")
    archivo_personal = st.file_uploader("Sube tu plantilla (.xlsx). Columnas: Cedula, Nombre, Cargo, Zona", type=["xlsx", "xls"], key="up_pers_grn")
    
    if archivo_personal is not None:
        if st.button("🔄 Importar Plantilla", key="btn_imp_pers_grn"):
            df_cargado = pd.read_excel(archivo_personal)
            if "Nombre" in df_cargado.columns and "Cargo" in df_cargado.columns:
                if "Cedula" not in df_cargado.columns: df_cargado["Cedula"] = "0"
                if "Zona" not in df_cargado.columns: df_cargado["Zona"] = "ZMO III"
                df_cargado["Cedula"] = df_cargado["Cedula"].fillna(0).astype(int).astype(str)
                df_cargado["Descanso Base"] = "Domingo" # Descanso por contrato
                guardar_tabla(df_cargado[["Cedula", "Nombre", "Cargo", "Zona", "Descanso Base"]], "green_personal")
                st.success("✅ ¡Personal cargado exitosamente!")
                st.rerun()
            else:
                st.error("Faltan las columnas 'Nombre' o 'Cargo'.")

    st.write("---")
    df_pers = cargar_tabla("green_personal")
    
    # 🛠️ PARCHE DE COMPATIBILIDAD DE TIPOS
    if not df_pers.empty:
        if "Descanso Base" not in df_pers.columns: 
            df_pers["Descanso Base"] = "Domingo"
        # Forzamos la cédula a ser texto SIEMPRE, para que no choque con el editor
        df_pers["Cedula"] = df_pers["Cedula"].fillna("").astype(str)
        # Limpiamos los decimales .0 si SQLite los convirtió a Float
        df_pers["Cedula"] = df_pers["Cedula"].apply(lambda x: x.split('.')[0] if '.' in x else x)
        
    if df_pers.empty:
        df_pers = pd.DataFrame({"Cedula": [""], "Nombre": [""], "Cargo": [""], "Zona": ["ZMO III"], "Descanso Base": ["Domingo"]})
        
    st.markdown("### 📝 Editor Individual de Empleados")
    df_edit = st.data_editor(
        df_pers, num_rows="dynamic", use_container_width=True,
        column_config={
            "Cedula": st.column_config.TextColumn("🆔 Cédula", required=True),
            "Nombre": st.column_config.TextColumn("👤 Nombre Completo", required=True),
            "Cargo": st.column_config.TextColumn("💼 Cargo (Ej. Técnico de Patio, Operador Senior)", required=True),
            "Zona": st.column_config.TextColumn("📍 Zona (Ej. ZMO III)", required=True),
            "Descanso Base": st.column_config.SelectboxColumn("🛌 Descanso Contrato", options=["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"], required=True)
        }, key="edit_pers_green"
    )
    
    if st.button("💾 Guardar Cambios en Personal", key="btn_guar_pers_grn2"):
        df_edit = df_edit[df_edit["Nombre"].str.strip() != ""]
        guardar_tabla(df_edit, "green_personal")
        st.success(f"✅ ¡{len(df_edit)} empleados registrados exitosamente!")

# =========================================================
# 3. PARAMETRIZADOR INDIVIDUAL (TURNOS Y ROTACIONES)
# =========================================================
def pantalla_parametrizador_green():
    st.markdown("## ⚙️ Parametrizador Operativo (Greenmovil)")
    st.info("Define las métricas operativas. La rotación ahora es **100% individual**, permitiendo que las parejas se mezclen naturalmente.")
    
    t_turnos, t_rotaciones, t_novedades, t_diagnostico = st.tabs([
        "🕒 Turnos y Zonas", 
        "🔄 Rotación Individual", 
        "🌴 Gestor de Novedades", 
        "⚖️ Diagnóstico"
    ])
    
    with t_turnos:
        st.markdown("### 🕒 Configuración de Turnos")
        df_turnos = cargar_tabla("green_turnos")
        if not df_turnos.empty and "Requeridos" not in df_turnos.columns: df_turnos["Requeridos"] = 1
        if not df_turnos.empty and "Zona" not in df_turnos.columns: df_turnos.insert(4, "Zona", "General")
            
        if df_turnos.empty:
            df_turnos = pd.DataFrame({
                "Nombre": ["TC1", "TC2", "TC3", "Inspector Electromovilidad", "Apoyo FDS Patio"], 
                "Inicio": ["06:00", "14:00", "22:00", "08:00", "06:00"], 
                "Fin": ["14:00", "22:00", "06:00", "16:00", "14:00"],
                "Cargo Aplicable": ["Técnicos de Control", "Técnicos de Control", "Técnicos de Control", "Técnicos de Control", "Operador SENIOR"],
                "Zona": ["ZMO III", "ZMO III", "ZMO III", "ZMO III", "ZMO III"],
                "Requeridos": [2, 2, 2, 1, 2]
            })
            
        df_edit_t = st.data_editor(
            df_turnos, num_rows="dynamic", use_container_width=True,
            column_config={
                "Nombre": st.column_config.TextColumn("Etiqueta del Turno", required=True),
                "Inicio": st.column_config.TextColumn("Hora Inicio (HH:MM)", required=True),
                "Fin": st.column_config.TextColumn("Hora Fin (HH:MM)", required=True),
                "Cargo Aplicable": st.column_config.TextColumn("Aplica para (Cargo)", required=True),
                "Zona": st.column_config.TextColumn("📍 Zona Operativa", required=True),
                "Requeridos": st.column_config.NumberColumn("Meta Cobertura", min_value=1, default=1, required=True)
            }, key="edit_turnos_green"
        )
        if st.button("💾 Guardar Catálogo de Turnos", key="btn_guar_t_green"):
            guardar_tabla(df_edit_t, "green_turnos")
            st.success("✅ Turnos guardados.")

    with t_rotaciones:
        st.markdown("### 🔄 Patrones de Rotación por INDIVIDUO")
        st.caption("Asigna secuencias únicas a cada persona. Si desfasas las semanas de inicio, nunca tendrán el mismo turno. **Ej: TC3, TC2, TC1, Inspector Electromovilidad**")
        
        df_pers_rot = cargar_tabla("green_personal")
        nombres_existentes = df_pers_rot["Nombre"].tolist() if not df_pers_rot.empty else []
        
        df_rot = cargar_tabla("green_rotaciones_ind")
        if not df_rot.empty and "Fase Inicio (Semana)" not in df_rot.columns: 
            df_rot["Fase Inicio (Semana)"] = df_rot.get("Fase Inicio (Día)", 1)
            
        rot_data = []
        for n in nombres_existentes:
            cargo_p = df_pers_rot[df_pers_rot["Nombre"]==n].iloc[0]["Cargo"]
            match = df_rot[df_rot["Nombre"] == n] if not df_rot.empty else pd.DataFrame()
            if not match.empty:
                rot_data.append({"Nombre": n, "Cargo": cargo_p, "Patrón de Rotación Semanal": match.iloc[0]["Patrón de Rotación Semanal"], "Fase Inicio (Semana)": match.iloc[0]["Fase Inicio (Semana)"]})
            else:
                patron_def = "TC3, TC2, TC1, Inspector Electromovilidad" if "Tecnico" in str(cargo_p) else "Fijo"
                rot_data.append({"Nombre": n, "Cargo": cargo_p, "Patrón de Rotación Semanal": patron_def, "Fase Inicio (Semana)": 1})
                
        if not rot_data:
            st.warning("No hay personal registrado.")
        else:
            df_rot_show = pd.DataFrame(rot_data)
            df_edit_rot = st.data_editor(
                df_rot_show, use_container_width=True, hide_index=True,
                column_config={
                    "Nombre": st.column_config.TextColumn("Empleado", disabled=True),
                    "Cargo": st.column_config.TextColumn("Cargo", disabled=True),
                    "Patrón de Rotación Semanal": st.column_config.TextColumn("Secuencia (Turnos por comas)", required=True),
                    "Fase Inicio (Semana)": st.column_config.NumberColumn("Semana de arranque (Ej: 1, 2, 3)", min_value=1, required=True)
                }, key="edit_rot_ind_green"
            )
            if st.button("💾 Guardar Patrones Individuales", key="btn_guar_rot_ind"):
                guardar_tabla(df_edit_rot, "green_rotaciones_ind")
                st.success("✅ Secuencias individuales guardadas.")

    with t_novedades:
        st.markdown("### 🌴 Registro de Novedades (Ausentismos)")
        df_pers_nov = cargar_tabla("green_personal")
        nombres_lista = df_pers_nov["Nombre"].tolist() if not df_pers_nov.empty else ["No hay personal"]
        df_nov = cargar_tabla("green_novedades")
        if df_nov.empty:
            df_nov = pd.DataFrame({"Nombre": [nombres_lista[0] if nombres_lista else ""], "Tipo Novedad": ["Vacaciones"], "Inicio": [date.today()], "Fin": [date.today()]})
        else:
            df_nov["Inicio"] = pd.to_datetime(df_nov["Inicio"]).dt.date; df_nov["Fin"] = pd.to_datetime(df_nov["Fin"]).dt.date
            
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
            df_edit_n["Inicio"] = df_edit_n["Inicio"].astype(str); df_edit_n["Fin"] = df_edit_n["Fin"].astype(str)
            guardar_tabla(df_edit_n, "green_novedades")
            st.success("✅ Novedades registradas exitosamente.")

    with t_diagnostico:
        st.markdown("### ⚖️ Diagnóstico de Capacidad por Zona y Cargo")
        df_pers_diag = cargar_tabla("green_personal")
        df_turnos_diag = cargar_tabla("green_turnos")
        
        if not df_turnos_diag.empty and "Zona" not in df_turnos_diag.columns: df_turnos_diag.insert(4, "Zona", "General")
        if not df_turnos_diag.empty and "Requeridos" not in df_turnos_diag.columns: df_turnos_diag["Requeridos"] = 1
        
        if df_pers_diag.empty or df_turnos_diag.empty:
            st.info("💡 Registra personal y configura los turnos para ver el diagnóstico.")
        else:
            diagnostico = []
            for zona in df_turnos_diag["Zona"].unique():
                turnos_zona = df_turnos_diag[df_turnos_diag["Zona"] == zona]
                for cargo in turnos_zona["Cargo Aplicable"].unique():
                    req_diario = turnos_zona[turnos_zona["Cargo Aplicable"] == cargo]["Requeridos"].sum()
                    planta_actual = len(df_pers_diag[(df_pers_diag["Cargo"].str.contains(str(cargo), case=False, na=False)) & (df_pers_diag["Zona"] == zona)])
                        
                    planta_minima_saludable = math.ceil(req_diario * (7/6))
                    estado = "✅ ÓPTIMO"
                    if planta_actual < req_diario: estado = "🚨 DÉFICIT CRÍTICO"
                    elif planta_actual < planta_minima_saludable: estado = "⚠️ DÉFICIT MODERADO"
                        
                    diagnostico.append({"📍 Zona": zona, "💼 Cargo / Rol": cargo, "Requiere x Día": req_diario, "Planta Mínima (Con Descansos)": planta_minima_saludable, "Personal Real": planta_actual, "Estado": estado})
                    
            st.dataframe(pd.DataFrame(diagnostico), use_container_width=True)

# =========================================================
# 4. MOTOR MATEMÁTICO INDIVIDUAL Y DE DESCANSOS INTELIGENTES
# =========================================================
def calcular_horas_y_recargos(ini_str, fin_str):
    if ini_str == "OFF" or fin_str == "OFF": return 0.0, 0.0, 0.0
    try:
        t_ini, t_fin = datetime.strptime(ini_str, "%H:%M"), datetime.strptime(fin_str, "%H:%M")
    except: return 0.0, 0.0, 0.0
    
    m_ini, m_fin = t_ini.hour * 60 + t_ini.minute, t_fin.hour * 60 + t_fin.minute
    minutos_totales = (m_fin - m_ini) if m_fin >= m_ini else ((1440 - m_ini) + m_fin)
    total_horas = minutos_totales / 60.0
    horas_extras = max(0.0, total_horas - 7.0)
    
    minutos_nocturnos, m_actual = 0, m_ini
    for _ in range(int(minutos_totales)):
        if (m_actual % 1440) >= 1140 or (m_actual % 1440) < 360: minutos_nocturnos += 1
        m_actual += 1
    return round(total_horas, 2), round(horas_extras, 2), round(minutos_nocturnos / 60.0, 2)

def evaluar_fatiga(turno_ayer_fin, turno_hoy_ini):
    if turno_ayer_fin == "OFF" or turno_hoy_ini == "OFF": return True
    t_fin, t_ini = datetime.strptime(turno_ayer_fin, "%H:%M"), datetime.strptime(turno_hoy_ini, "%H:%M")
    m_fin = t_fin.hour * 60 + t_fin.minute
    m_ini = t_ini.hour * 60 + t_ini.minute
    descanso = (1440 - m_fin) + m_ini
    return descanso >= 480

def generar_malla_dinamica(inicio, fin, df_personal, df_turnos, df_rotaciones, df_novedades):
    filas = []
    
    dict_rot = {}
    if not df_rotaciones.empty:
        for _, row in df_rotaciones.iterrows():
            patron = [x.strip() for x in str(row["Patrón de Rotación Semanal"]).split(",")]
            fase = int(row.get("Fase Inicio (Semana)", 1)) - 1
            dict_rot[row["Nombre"]] = {"patron": patron, "fase": fase}
            
    for _, p in df_personal.iterrows():
        if p["Nombre"] not in dict_rot: dict_rot[p["Nombre"]] = {"patron": ["Fijo"], "fase": 0}
    
    dias_semana = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    fecha_inicio_dt = pd.to_datetime(inicio)
    
    for fecha in pd.date_range(inicio, fin):
        dia_n = dias_semana[fecha.weekday()]
        fecha_str = fecha.strftime('%Y-%m-%d')
        # Calculamos en qué semana del plan estamos para hacer la rotación semanal
        delta_semanas = (fecha - fecha_inicio_dt).days // 7
        
        for _, p in df_personal.iterrows():
            cedula, nombre, cargo = p.get("Cedula", "N/A"), p["Nombre"], p["Cargo"]
            zona, descanso_base = p.get("Zona", "General"), p.get("Descanso Base", "Domingo")
            turno_hoy, ini_hoy, fin_hoy = "DESCANSO", "OFF", "OFF"
            
            novedad_activa = None
            if not df_novedades.empty:
                for _, nov in df_novedades[df_novedades["Nombre"] == nombre].iterrows():
                    try:
                        if pd.to_datetime(nov["Inicio"]).date() <= fecha.date() <= pd.to_datetime(nov["Fin"]).date():
                            novedad_activa = f"⚠️ {nov['Tipo Novedad']}"
                            break
                    except: pass

            patron = dict_rot[nombre]["patron"]

            if novedad_activa:
                turno_hoy = novedad_activa
            else:
                if len(patron) > 0:
                    fase_actual = (delta_semanas + dict_rot[nombre]["fase"]) % len(patron)
                    turno_semana = patron[fase_actual]
                    
                    # 🌟 INTELIGENCIA DE DESCANSOS: Si el turno es Inspector, descansa el Sábado
                    descanso_hoy = "Sábado" if "Inspector" in turno_semana else descanso_base
                    
                    if dia_n == descanso_hoy:
                        turno_hoy = "DESCANSO"
                    else:
                        if turno_semana in df_turnos["Nombre"].values:
                            turno_hoy = turno_semana
                            datos_t = df_turnos[df_turnos["Nombre"] == turno_semana].iloc[0]
                            ini_hoy, fin_hoy = datos_t["Inicio"], datos_t["Fin"]
                        else:
                            turno_hoy = f"⚠️ {turno_semana} (No configurado)"
                else:
                    turno_hoy = "SIN ROTACIÓN"
            
            # --- EDITOR MANUAL ---
            if "ajustes_manuales_grn" in st.session_state and (nombre, fecha_str) in st.session_state.ajustes_manuales_grn:
                turno_manual = st.session_state.ajustes_manuales_grn[(nombre, fecha_str)]
                turno_hoy = turno_manual
                if turno_manual not in ["DESCANSO", "SIN ROTACIÓN"] and not turno_manual.startswith("⚠️"):
                    if turno_manual in df_turnos["Nombre"].values:
                        datos_t = df_turnos[df_turnos["Nombre"] == turno_manual].iloc[0]
                        ini_hoy, fin_hoy = datos_t["Inicio"], datos_t["Fin"]
                else:
                    ini_hoy, fin_hoy = "OFF", "OFF"
            
            h_tot, h_ext, h_noc = calcular_horas_y_recargos(ini_hoy, fin_hoy)
            filas.append({
                "Fecha": fecha.strftime('%Y-%m-%d'), "Cedula": cedula, "Nombre": nombre, "Zona": zona, "Cargo": cargo,
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
            elif "⚠️" in val: bg, txt = "#E67E22", "white" 
            elif val == "SIN ROTACIÓN": bg, txt = "#F39C12", "white"
            else: bg, txt = "#D6EAF8", "#17202A" 
            styles.at[idx, col] = f'background-color: {bg}; color: {txt}; font-weight: 700; border: 0.5px solid #D5DBDB;'
    return df_pivot.style.apply(lambda _: styles, axis=None)

@st.dialog("🛠️ Forzar Cobertura / Turno (Greenmovil)", width="small")
def popup_forzar_ajuste_fecha_grn(fecha_solicitada, opciones_sujetos, opciones_turnos):
    st.markdown(f"📅 **Fecha:** `{fecha_solicitada}`")
    sujeto_sel = st.selectbox("🎯 Empleado a reasignar:", opciones_sujetos, key="sel_suj_grn_pu")
    nuevo_turno = st.selectbox("🆕 Turno o Cobertura:", ["DESCANSO"] + opciones_turnos, index=0, key="sel_tur_grn_pu")
    
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
    st.info("Generación automatizada por Individuo. El sistema cruza Patrones Semanales, Zonas y Ausentismos automáticamente.")
    
    df_pers = cargar_tabla("green_personal")
    df_turnos = cargar_tabla("green_turnos")
    df_nov = cargar_tabla("green_novedades")
    df_rot = cargar_tabla("green_rotaciones_ind")
    
    if df_pers.empty or df_turnos.empty or df_rot.empty:
        st.warning("⚠️ Asegúrate de registrar personal, configurar turnos y crear los Patrones de Rotación en el Parametrizador.")
        return
        
    st.markdown("### ⚙️ Configuración de Generación")
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Inicio", date(2026, 7, 1), key="i_grn_m")
    fin = c2.date_input("Fin", date(2026, 12, 31), key="f_grn_m")
        
    if st.button("🚀 GENERAR MALLA INDIVIDUAL", key="btn_gen_grn_m"):
        st.session_state.m_base_grn = generar_malla_dinamica(inicio, fin, df_pers, df_turnos, df_rot, df_nov)
        
    if 'm_base_grn' in st.session_state and not st.session_state.m_base_grn.empty:
        df_malla = st.session_state.m_base_grn
        
        st.write("---")
        st.subheader("📋 Explorador de Mallas Operativas")
        
        c1_filtro, c2_filtro = st.columns(2)
        zonas_presentes = ["Todas las Zonas"] + sorted(list(df_malla["Zona"].unique()))
        cargos_presentes = ["Todos los Cargos"] + sorted(list(df_malla["Cargo"].unique()))
        zona_sel = c1_filtro.selectbox("📍 Filtrar por Zona:", zonas_presentes)
        cargo_sel = c2_filtro.selectbox("💼 Filtrar por Cargo:", cargos_presentes)
        
        df_vista = df_malla.copy()
        if zona_sel != "Todas las Zonas": df_vista = df_vista[df_vista["Zona"] == zona_sel]
        if cargo_sel != "Todos los Cargos": df_vista = df_vista[df_vista["Cargo"] == cargo_sel]
            
        pivot = df_vista.pivot(index=["Zona", "Cargo", "Nombre"], columns="Fecha", values="Turno").fillna("DESCANSO")
        st.dataframe(style_malla_green(pivot), use_container_width=True)
        
        st.write("---")
        st.subheader("🛠️ Gestor de Coberturas Manuales (Para Operadores SENIOR y Reemplazos)")
        st.caption("Usa este panel los fines de semana para que los Operadores SENIOR cubran a los Técnicos de Patio o Control en descanso.")
        with st.expander("🔍 Forzar cambio o cobertura en Malla", expanded=False):
            c_f1, c_f2 = st.columns(2)
            f_libre_sel = c_f1.selectbox("Seleccione la Fecha:", list(pivot.columns), key="f_libre_dropdown_grn")
            if c_f2.button("⚙️ Abrir Gestor de Turnos", use_container_width=True, key="btn_gestor_grn"):
                popup_forzar_ajuste_fecha_grn(f_libre_sel, sorted(list(df_malla["Nombre"].unique())), df_turnos["Nombre"].tolist())

        st.write("---")
        st.subheader("📊 Auditoría de Cobertura vs. Requeridos")
        auditoria = df_vista.groupby(["Fecha", "Turno"]).size().unstack(fill_value=0)
        
        if zona_sel == "Todas las Zonas" and cargo_sel == "Todos los Cargos":
            alertas_cobertura = 0
            for col in auditoria.columns:
                if col in df_turnos["Nombre"].values:
                    requerido = df_turnos[df_turnos["Nombre"] == col]["Requeridos"].sum()
                    dias_deficit = auditoria[auditoria[col] < requerido].index
                    if not dias_deficit.empty:
                        st.warning(f"📉 **Déficit en Turno '{col}':** Meta {requerido} pax. Faltantes en {len(dias_deficit)} días (Domingos/Novedades). ¡Recuerda asignar a un Operador SENIOR!")
                        alertas_cobertura += 1
            if alertas_cobertura == 0: st.success("✅ **Cobertura Perfecta:** Todos los turnos cumplen con la meta requerida.")

        st.dataframe(auditoria, use_container_width=True)

        st.write("---")
        st.subheader("💰 Resumen de Nómina (Reforma 7h)")
        resumen = df_vista.groupby(["Zona", "Cargo", "Cedula", "Nombre"])[["Hrs Prog", "Hrs Extras", "Recargos Noct"]].sum().reset_index()
        st.dataframe(resumen, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer: 
            df_vista.to_excel(writer, sheet_name="Detalle_Operacion", index=False)
            resumen.to_excel(writer, sheet_name="Nomina_Consolidada", index=False)
        st.download_button("📥 Descargar Reporte de la Vista Actual (.xlsx)", output.getvalue(), f"Reporte_{vista_sel}_{date.today()}.xlsx", key="dw_grn_m")
