import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date

# --- IMPORTACIÓN DE MOTORES LÓGICOS ---
# Aquí importaremos los motores de cada empresa
try:
    from logic_programador import pantalla_programador, pantalla_personal, cargar_excel
except ImportError:
    st.error("⚠️ No se encontró 'logic_programador.py' (Motor de Cablemovil).")

# NOTA: Cuando crees la lógica de Greenmovil, la importarás aquí:
# from logic_greenmovil import pantalla_programador_green, pantalla_personal_green

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="MovilGo - Hub Corporativo", 
    page_icon="🏢",
    layout="wide", 
    initial_sidebar_state="expanded"
)

URL_BASE = "https://raw.githubusercontent.com/RichGuep/movilgo/main/"
LOGO_MÓVILGO = f"{URL_BASE}MovilGo.png"
CONFIG_FILE = "config_estructural.json"

def cargar_configuracion():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        default_config = {
            "Técnicos": {
                "descripcion": "Operación de soporte técnico en campo 24/7 por bloques organizados.",
                "extension_turno": 7,
                "grupos": ["Grupo 1", "Grupo 2", "Grupo 3", "Grupo 4"],
                "rotacion": "Determinista por Grupos"
            }
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        return default_config

if 'config_personal' not in st.session_state:
    st.session_state.config_personal = cargar_configuracion()

# --- 2. ESTILOS CSS AVANZADOS ---
PRIMARY_COLOR = "#1E3D59" 
st.markdown(f"""
    <style>
    .stApp {{ background-color: #F4F7F6; }}
    
    [data-testid="stSidebar"] {{ 
        background-color: {PRIMARY_COLOR}; 
        border-right: 1px solid #ffffff22; 
    }}
    [data-testid="stSidebar"] * {{ color: white !important; font-weight: 500; }}
    
    .stTextInput>div>div>input {{
        border-radius: 10px;
        border: 1.5px solid #d1d5db;
        padding: 12px 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        font-size: 1rem;
    }}
    .stTextInput>div>div>input:focus {{
        border-color: {PRIMARY_COLOR};
        box-shadow: 0 0 0 2px rgba(30, 61, 89, 0.2);
    }}
    
    .stButton>button {{ 
        width: 100%; 
        border-radius: 12px; 
        font-weight: 700; 
        height: 3.2em; 
        transition: all 0.3s ease; 
        border: none; 
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #3a6073 100%);
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
    }}
    .stButton>button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.2);
        color: #f8f9fa;
    }}
    
    /* Botones de Selección de Empresa */
    .btn-empresa>button {{
        height: 8em !important;
        font-size: 1.5rem !important;
        background: white !important;
        color: {PRIMARY_COLOR} !important;
        border: 2px solid {PRIMARY_COLOR} !important;
    }}
    .btn-empresa>button:hover {{
        background: {PRIMARY_COLOR} !important;
        color: white !important;
    }}

    .welcome-card {{
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #3a6073 100%);
        color: white; 
        padding: 3rem; 
        border-radius: 20px; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.15); 
        margin-bottom: 2.5rem;
        text-align: center;
    }}
    
    .login-title {{
        text-align: center;
        color: {PRIMARY_COLOR};
        font-weight: 800;
        margin-top: 15px;
        margin-bottom: 5px;
        font-size: 2.2rem;
    }}
    </style>
    """, unsafe_allow_html=True)

def modulo_inicio():
    st.markdown(f'''
        <div class="welcome-card">
            <h1 style="font-size: 2.5rem; font-weight: 800;">👋 ¡Bienvenido al Panel de {st.session_state.empresa_seleccionada}!</h1>
            <p style="font-size: 1.3rem; opacity: 0.9; margin-top: 10px;">
                Inteligencia Operativa y Sistematización de Turnos.
            </p>
        </div>
    ''', unsafe_allow_html=True)
    
    # Solo mostramos esto para Cablemovil por ahora, ya que requiere cargar_excel
    if st.session_state.empresa_seleccionada == "Cablemovil SAS":
        try:
            df_p = cargar_excel("empleados_grupos.xlsx") 
            total_emp = len(df_p) if not df_p.empty else "0"
        except:
            total_emp = "0"
    else:
        total_emp = "Pendiente Configurar BD"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👷 Personal Registrado", total_emp)
    c2.metric("📂 Modelos Activos", len(st.session_state.config_personal))
    c3.metric("⚖️ Deuda Global", "0 días")
    c4.metric("📡 Estado de BD", "Conectado", delta="Estable")

    st.divider()
    st.subheader("🇨🇴 Contexto Legal Global: Reforma Laboral 2026")
    st.info("📉 **Reducción de la Jornada Semanal:** Para el año 2026 la jornada ordinaria máxima es de 42 horas semanales.")


# --- VARIABLES DE SESIÓN ---
if 'splash_done' not in st.session_state: st.session_state.splash_done = False
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'empresa_seleccionada' not in st.session_state: st.session_state.empresa_seleccionada = None

# --- PANTALLA 1: SPLASH (BIENVENIDA) ---
if not st.session_state.splash_done:
    _, splash_center, _ = st.columns([1, 2, 1])
    with splash_center:
        st.markdown('<div style="text-align:center; margin-top:10vh;">', unsafe_allow_html=True)
        _, img_splash, _ = st.columns([1, 1.5, 1])
        with img_splash: st.image(LOGO_MÓVILGO, use_container_width=True)
        st.markdown("<h1 style='color:#1E3D59; font-size: 3.5rem; font-weight: 900; margin-top: 20px;'>Optimizer Pro 2026</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.3rem; color: #666; margin-bottom: 40px;'>Hub Operativo Corporativo</p>", unsafe_allow_html=True)
        
        if st.button("INGRESAR AL PORTAL", use_container_width=True):
            st.session_state.splash_done = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- PANTALLA 2: LOGIN ---
elif not st.session_state.logged_in:
    _, login_center, _ = st.columns([1.5, 2, 1.5])
    with login_center:
        st.write(""); st.write(""); st.write(""); st.write("")
        with st.container():
            _, img_login, _ = st.columns([1, 1.2, 1])
            with img_login: st.image(LOGO_MÓVILGO, use_container_width=True)
            st.markdown("<h2 class='login-title'>Acceso Seguro</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#666; margin-bottom: 25px;'>Ingresa tus credenciales administrativas</p>", unsafe_allow_html=True)
            
            u = st.text_input("👤 Nombre de Usuario", placeholder="Ej: admin")
            p = st.text_input("🔒 Contraseña", type="password", placeholder="••••••••")
            
            st.write("")
            if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
                if u == "admin" and p == "movilgo2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Por favor, intenta de nuevo.")

# --- PANTALLA 3: SELECCIÓN DE EMPRESA ---
elif st.session_state.empresa_seleccionada is None:
    st.markdown("<h2 class='login-title' style='margin-top: 5vh; font-size: 3rem;'>🏢 Seleccione el Entorno Operativo</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#666; margin-bottom: 50px; font-size: 1.2rem;'>¿Qué operación desea gestionar hoy?</p>", unsafe_allow_html=True)
    
    _, col1, col2, _ = st.columns([1, 2, 2, 1])
    
    with col1:
        st.markdown('<div class="btn-empresa">', unsafe_allow_html=True)
        if st.button("🟠 Cablemovil SAS", use_container_width=True):
            st.session_state.empresa_seleccionada = "Cablemovil SAS"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="btn-empresa">', unsafe_allow_html=True)
        if st.button("🟢 Greenmovil SAS", use_container_width=True):
            st.session_state.empresa_seleccionada = "Greenmovil SAS"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- PANTALLA 4: INTERIOR DE LA APLICACIÓN (SEGÚN EMPRESA) ---
else:
    with st.sidebar:
        st.write("")
        st.image(LOGO_MÓVILGO, use_container_width=True)
        st.markdown(f"<h4 style='text-align:center; color:white;'>{st.session_state.empresa_seleccionada}</h4>", unsafe_allow_html=True)
        st.divider()
        menu = st.radio("Navegación del Sistema", ["🏠 Inicio", "👥 Personal", "📅 Programación"])
        st.divider()
        
        # Nuevo botón para cambiar de empresa sin cerrar sesión
        if st.button("🔄 Cambiar de Empresa"):
            st.session_state.empresa_seleccionada = None
            st.rerun()
            
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.logged_in = False
            st.session_state.splash_done = False
            st.session_state.empresa_seleccionada = None
            st.rerun()

    # --- RUTEO DE LÓGICA SEGÚN EMPRESA ---
    if menu == "🏠 Inicio": 
        modulo_inicio()
        
    elif menu == "👥 Personal": 
        if st.session_state.empresa_seleccionada == "Cablemovil SAS":
            pantalla_personal()
        elif st.session_state.empresa_seleccionada == "Greenmovil SAS":
            st.info("🛠️ El módulo de personal para Greenmovil SAS está en construcción. Aquí conectaremos 'logic_greenmovil.py' próximamente.")
            
    elif menu == "📅 Programación": 
        if st.session_state.empresa_seleccionada == "Cablemovil SAS":
            pantalla_programador()
        elif st.session_state.empresa_seleccionada == "Greenmovil SAS":
            st.warning("🛠️ El módulo de programación para Greenmovil SAS está en desarrollo.")
