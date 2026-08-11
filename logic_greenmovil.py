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
# 2. PANEL DE PERSONAL Y CARGOS DINÁMICOS
# =========================================================
def pantalla_personal_green():
    st.markdown("## 👥 Personal de Operaciones (Greenmovil)")
    st.info("💡 **Configuración Dinámica:** Registra a tu equipo. El 'Grupo de Trabajo' es clave porque determinará cómo rotan.")
    
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
# 3. PARAMETRIZADOR (TURNOS, SECUENCIAS Y NOVEDADES)
# =========================================================
def pantalla_parametrizador_green():
    st.markdown("## ⚙️ Parametrizador Operativo (Greenmovil)")
    st.info("Configura los turnos, cómo rotan tus grupos, y controla los requerimientos de personal.")
    
    t_turnos, t_rotaciones, t_novedades, t_diagnostico = st.tabs([
        "🕒 Turnos y Requeridos", 
        "🔄 Secuencias de Rotación", 
        "🌴 Novedades", 
        "⚖️ Diagnóstico"
    ])
    
    # --- PESTAÑA 1: TURNOS ---
    with t_turnos:
        st.markdown("### 🕒 Configuración de Turnos")
        st.caption("Crea los turnos y define cuántas personas requieres diariamente en cada uno.")
        
        df_turnos = cargar_tabla("green_turnos")
        if not df_turnos.empty and "Requeridos" not in df_turnos.columns:
            df_turnos["Requeridos"] = 1
            
        if df_turnos.empty:
            df_turnos = pd.DataFrame({
                "Nombre": ["TC1", "TC2", "TC3"], 
                "Inicio": ["06:00", "14:00", "22:00"], 
                "Fin": ["14:00", "22:00", "06:00"],
                "Cargo Aplicable": ["Técnicos de Control", "Técnicos de Control", "Técnicos de Control"],
                "Requeridos": [2, 2, 2]
            })
            
        df_edit_t = st.data_editor(
            df_turnos, num_rows="dynamic", use_container_width=True,
            column_config={
                "Nombre": st.column_config.TextColumn("Etiqueta del Turno", required=True),
                "Inicio": st.column_config.TextColumn("Hora Inicio (HH:MM)", required=True),
                "Fin": st.column_config.TextColumn("Hora Fin (HH:MM)", required=True),
                "Cargo Aplicable": st.column_config.TextColumn("Aplica para (Cargo)", required=True),
                "Requeridos": st.column_config.NumberColumn("Meta Cobertura (Requeridos)", min_value=1, default=1, required=True)
            }, key="edit_turnos_green"
        )
        if st.button("💾 Guardar Catálogo de Turnos", key="btn_guar_t_green"):
            guardar_tabla(df_edit_t, "green_turnos")
            st.success("✅ Turnos y requerimientos guardados correctamente.")

    # --- PESTAÑA 2: ROTACIONES Y PATRONES ---
    with t_rotaciones:
        st.markdown("### 🔄 Patrones de Rotación por Grupo")
        st.caption("Escribe los turnos separados por coma. Ejemplo: **TC3, TC2, TC1, DESCANSO**.")
        
        df_pers_rot = cargar_tabla("green_personal")
        grupos_existentes = df_pers_rot["Grupo"].unique() if not df_pers_rot.empty else []
        
        df_rot = cargar_tabla("green_rotaciones")
        rot_data = []
        for g in grupos_existentes:
            match = df_rot[df_rot["Grupo"] == g] if not df_rot.empty else pd.DataFrame()
            if not match.empty:
                rot_data.append({
                    "Grupo": g,
                    "Patrón de Rotación": match.iloc[0]["Patrón de Rotación"],
                    "Fase Inicio (Día)": match.iloc[0]["Fase Inicio (Día)"]
                })
            else:
                rot_data.append({"Grupo": g, "Patrón de Rotación": "TC3, TC2, TC1, DESCANSO", "Fase Inicio (Día)": 1})
                
        if not rot_data:
            st.warning("No hay grupos registrados. Ve a la pestaña 'Personal' primero.")
        else:
            df_rot_show = pd.DataFrame(rot_data)
            df_edit_rot = st.data_editor(
                df_rot_show, use_container_width=True, hide_index=True,
                column_config={
                    "Grupo": st.column_config.TextColumn("Grupo de Trabajo", disabled=True),
                    "Patrón de Rotación": st.column_config.TextColumn("Secuencia (Separada por comas)", required=True),
                    "Fase Inicio (Día)": st.column_config.NumberColumn("Día de arranque (Ej: 1, 2, 3...)", min_value=1, required=True)
                }, key="edit_rot_green"
            )
            if st.button("💾 Guardar Patrones de Rotación", key="btn_guar_rot_green"):
                guardar_tabla(df_edit_rot, "green_rotaciones")
                st.success("✅ Secuencias de rotación guardadas exitosamente.")

    # --- PESTAÑA 3: NOVEDADES ---
    with t_novedades:
        st.markdown("### 🌴 Registro de Novedades (Ausentismos)")
        st.caption("Registra vacaciones, licencias o incapacidades.")
        
        df_pers_nov = cargar_tabla("green_personal")
        nombres_lista = df_pers_nov["Nombre"].tolist() if not df_pers_nov.empty else ["No hay personal"]
        
        df_nov = cargar_tabla("green_novedades")
        if df_nov.empty:
            df_nov = pd.DataFrame({
                "Nombre": [nombres_lista[0] if nombres_lista else ""], 
                "Tipo Novedad": ["Vacaciones"], 
                "Inicio": [date.today()], "Fin": [date.today()]
            })
        else:
            df_nov["Inicio"] = pd.to_datetime(df_nov["Inicio"]).dt.date
            df_nov["Fin"] = pd.to_datetime(df_nov["Fin"]).dt.date
            
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
            df_edit_n["Inicio"] = df_edit_n["Inicio"].astype(str)
            df_edit_n["Fin"] = df_edit_n["Fin"].astype(str)
            guardar_tabla(df_edit_n, "green_novedades")
            st.success("✅ Novedades registradas exitosamente.")

    # --- PESTAÑA 4: DIAGNÓSTICO ---
    with t_diagnostico:
        st.markdown("### ⚖️ Diagnóstico Matemático de Capacidad Operativa")
        df_pers_diag = cargar_tabla("green_personal")
        df_turnos_diag = cargar_tabla("green_turnos")
        
        if not df_turnos_diag.empty and "Requeridos" not in df_turnos_diag.columns: df_turnos_diag["Requeridos"] = 1
        
        if df_pers_diag.empty or df_turnos_diag.empty:
            st.info("💡 Registra personal y configura los turnos para ver el diagnóstico matemático de tu planta.")
        else:
            diagnostico = []
            for cargo in df_turnos_diag["Cargo Aplicable"].unique():
                req_diario = df_turnos_diag[df_turnos_diag["Cargo Aplicable"] == cargo]["Requeridos"].sum()
                if str(cargo).strip().upper() == "TODOS": planta_actual = len(df_pers_diag)
                else: planta_actual = len(df_pers_diag[df_pers_diag["Cargo"].str.contains(str(cargo), case=False, na=False)])
                    
                planta_minima_saludable = math.ceil(req_diario * (7/6))
                estado = "✅ ÓPTIMO"
                if planta_actual < req_diario: estado = "🚨 DÉFICIT CRÍTICO"
                elif planta_actual < planta_minima_saludable: estado = "⚠️ DÉFICIT MODERADO"
                    
                diagnostico.append({
                    "Cargo / Rol": cargo, "Requiere x Día": req_diario,
                    "Planta Mínima (Con Descansos)": planta_minima_saludable,
                    "Personal Registrado Real": planta_actual, "Estado de Cobertura": estado
                })
                
            df_diag = pd.DataFrame(diagnostico)
            st.dataframe(df_diag, use_container_width=True)
            
            alertas_lanzadas = 0
            for _, row in df_diag.iterrows():
                if "CRÍTICO" in row["Estado de Cobertura"]:
                    st.error(f"🚨 **Crítico en {row['Cargo / Rol']}:** Tienes **{row['Personal Registrado Real']}** empleados, exiges **{row['Requiere x Día']}**. Operación imposible.")
                    alertas_lanzadas += 1
                elif "MODERADO" in row["Estado de Cobertura"]:
                    st.warning(f"⚠️ **Preventiva en {row['Cargo / Rol']}:** Tienes **{row['Personal Registrado Real']}** empleados. Alcanza exacto, pero no soportarás los días de descanso. Lo ideal es **{row['Planta Mínima (Con Descansos)']}**.")
                    alertas_lanzadas += 1
            if alertas_lanzadas == 0:
                st.success("🎉 **¡Estructura Perfecta!** Tu planta cubre turnos y descansos sin problema.")


# =========================================================
# 4. MOTOR DE ASIGNACIÓN DINÁMICA POR PATRONES
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
    
    horas_extras = max(0.0, total_horas - 7.0) # Reforma 7h
    
    minutos_nocturnos = 0
    m_actual = min_ini
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
    ayer_fin = {row["Grupo"]: "OFF" for _, row in df_personal.iterrows()}
    
    # Procesar diccionario de rotaciones
    dict_rot = {}
    if not df_rotaciones.empty:
        for _, row in df_rotaciones.iterrows():
            patron = [x.strip() for x in str(row["Patrón de Rotación"]).split(",")]
            fase = int(row["Fase Inicio (Día)"]) - 1
            dict_rot[row["Grupo"]] = {"patron": patron, "fase": fase}
    
    for fecha in pd.date_range(inicio, fin):
        fecha_str = fecha.strftime('%Y-%m-%d')
        delta_dias = (fecha - pd.to_datetime(inicio)).days
        
        for _, p in df_personal.iterrows():
            cedula, nombre, grupo, cargo = p.get("Cedula", "N/A"), p["Nombre"], p["Grupo"], p["Cargo"]
            turno_hoy, ini_hoy, fin_hoy = "DESCANSO", "OFF", "OFF"
            
            # --- EVALUACIÓN DE NOVEDADES ---
            novedad_activa = None
            if not df_novedades.empty:
                for _, nov in df_novedades[df_novedades["Nombre"] == nombre].iterrows():
                    try:
                        if pd.to_datetime(nov["Inicio"]) <= fecha <= pd.to_datetime(nov["Fin"]):
                            novedad_activa = f"⚠️ {nov['Tipo Novedad']}"
                            break
                    except: pass

            # --- LÓGICA DE ASIGNACIÓN POR PATRÓN ---
            if novedad_activa:
                turno_hoy = novedad_activa
            else:
                if grupo in dict_rot and len(dict_rot[grupo]["patron"]) > 0:
                    patron = dict_rot[grupo]["patron"]
                    fase_ini = dict_rot[grupo]["fase"]
                    # Matemática cíclica del patrón
                    idx_hoy = (delta_dias + fase_ini) % len(patron)
                    turno_propuesto = patron[idx_hoy]
                    
                    if turno_propuesto.upper() == "DESCANSO":
                        turno_hoy = "DESCANSO"
                    elif turno_propuesto in df_turnos["Nombre"].values:
                        datos_t = df_turnos[df_turnos["Nombre"] == turno_propuesto].iloc[0]
                        ini_prop = datos_t["Inicio"]
                        
                        if evaluar_fatiga(ayer_fin[grupo], ini_prop):
                            turno_hoy, ini_hoy, fin_hoy = turno_propuesto, ini_prop, datos_t["Fin"]
                        else:
                            turno_hoy, ini_hoy, fin_hoy = "RELEVO FATIGA", "08:00", "15:00"
                    else:
                        turno_hoy = f"⚠️ {turno_propuesto} (No existe)"
                else:
                    turno_hoy = "SIN ROTACIÓN"
            
            # --- EDITOR MANUAL (SOBREESCRIBE) ---
            if "ajustes_manuales_grn" in st.session_state and (nombre, fecha_str) in st.session_state.ajustes_manuales_grn:
                turno_manual = st.session_state.ajustes_manuales_grn[(nombre, fecha_str)]
                turno_hoy = turno_manual
                if turno_manual not in ["DESCANSO", "RELEVO FATIGA", "SIN ROTACIÓN"] and not turno_manual.startswith("⚠️"):
                    if turno_manual in df_turnos["Nombre"].values:
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
            elif "⚠️" in val: bg, txt = "#E67E22", "white" 
            elif val == "RELEVO FATIGA": bg, txt = "#E74C3C", "white" 
            elif val == "SIN ROTACIÓN": bg, txt = "#F39C12", "white"
            else: bg, txt = "#D6EAF8", "#17202A" 
            
            styles.at[idx, col] = f'background-color: {bg}; color: {txt}; font-weight: 700; border: 0.5px solid #D5DBDB;'
    return df_pivot.style.apply(lambda _: styles, axis=None)

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
    st.info("Generación de turnos basada en patrones de rotación con validación de ausentismos y coberturas.")
    
    df_pers = cargar_tabla("green_personal")
    df_turnos = cargar_tabla("green_turnos")
    df_nov = cargar_tabla("green_novedades")
    df_rot = cargar_tabla("green_rotaciones")
    
    if not df_turnos.empty and "Requeridos" not in df_turnos.columns: df_turnos["Requeridos"] = 1
    
    if df_pers.empty or df_turnos.empty or df_rot.empty:
        st.warning("⚠️ Asegúrate de registrar personal, configurar turnos y crear los Patrones de Rotación en el Parametrizador.")
        return
        
    st.markdown("### ⚙️ Configuración de Generación")
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Inicio", date(2026, 7, 1), key="i_grn_m")
    fin = c2.date_input("Fin", date(2026, 12, 31), key="f_grn_m")
        
    if st.button("🚀 GENERAR MALLA CON PATRONES", key="btn_gen_grn_m"):
        st.session_state.m_base_grn = generar_malla_dinamica(inicio, fin, df_pers, df_turnos, df_rot, df_nov)
        
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
        
        st.write("---")
        st.subheader("🛠️ Gestor de Coberturas Manuales")
        st.caption("Usa este panel para asignar reemplazos cuando la auditoría muestre faltantes por novedades.")
        with st.expander("🔍 Forzar cambio o cobertura en Malla", expanded=False):
            c_f1, c_f2 = st.columns(2)
            f_libre_sel = c_f1.selectbox("Seleccione la Fecha:", list(pivot.columns), key="f_libre_dropdown_grn")
            if c_f2.button("⚙️ Abrir Gestor de Turnos", use_container_width=True, key="btn_gestor_grn"):
                popup_forzar_ajuste_fecha_grn(f_libre_sel, sorted(list(df_malla["Nombre"].unique())), df_turnos["Nombre"].tolist())

        st.write("---")
        st.subheader("📊 Auditoría de Cobertura vs. Requeridos")
        
        auditoria = df_vista.groupby(["Fecha", "Turno"]).size().unstack(fill_value=0)
        
        if vista_sel == "General (Toda la Planta)":
            alertas_cobertura = 0
            for col in auditoria.columns:
                if col in df_turnos["Nombre"].values:
                    requerido = df_turnos[df_turnos["Nombre"] == col]["Requeridos"].values[0]
                    dias_deficit = auditoria[auditoria[col] < requerido].index
                    if not dias_deficit.empty:
                        st.warning(f"📉 **Déficit en Turno '{col}':** La meta es {requerido} personas, pero hay falta de personal en {len(dias_deficit)} días (Novedades o Descansos simultáneos).")
                        alertas_cobertura += 1
            if alertas_cobertura == 0:
                st.success("✅ **Cobertura Perfecta:** Todos los turnos cumplen con la meta de personal requerido.")

        auditoria.index = [p for p in auditoria.index]
        st.dataframe(auditoria, use_container_width=True)

        st.write("---")
        st.subheader("💰 Resumen de Nómina y Reforma Laboral (7h)")
        resumen = df_vista.groupby(["Cargo", "Grupo", "Cedula", "Nombre"])[["Hrs Prog", "Hrs Extras", "Recargos Noct"]].sum().reset_index()
        st.dataframe(resumen, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer: 
            df_vista.to_excel(writer, sheet_name="Detalle_Operacion", index=False)
            resumen.to_excel(writer, sheet_name="Nomina_Consolidada", index=False)
        st.download_button("📥 Descargar Reporte de la Vista Actual (.xlsx)", output.getvalue(), f"Reporte_{vista_sel}_{date.today()}.xlsx", key="dw_grn_m")
