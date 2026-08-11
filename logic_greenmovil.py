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
            # 🛠️ CORRECCIÓN: Usar objetos date() en lugar de strings
            df_nov = pd.DataFrame({
                "Nombre": [nombres_lista[0] if nombres_lista else ""], 
                "Tipo Novedad": ["Vacaciones"], 
                "Inicio": [date.today()], 
                "Fin": [date.today()]
            })
        else:
            # 🛠️ CORRECCIÓN: Convertir el texto de la BD a formato fecha
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
            # Volver a string para guardar en la BD sin problemas
            df_edit_n["Inicio"] = df_edit_n["Inicio"].astype(str)
            df_edit_n["Fin"] = df_edit_n["Fin"].astype(str)
            guardar_tabla(df_edit_n, "green_novedades")
            st.success("✅ Novedades registradas exitosamente.")
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
