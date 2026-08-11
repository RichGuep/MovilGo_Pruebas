import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date

# --- IMPORTACIÓN DE MOTORES LÓGICOS ---
try:
    from logic_greenmovil import pantalla_personal_green, pantalla_parametrizador_green, pantalla_mallas_green
except ImportError:
    st.error("⚠️ No se encontró 'logic_greenmovil.py'.")

try:
    from logic_programador import pantalla_programador, pantalla_personal, cargar_excel, pantalla_abordaje
except ImportError:
    st.error("⚠️ No se encontró 'logic_programador.py' (Motor de Cablemovil).")

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

# --- INICIALIZACIÓN DE VARIABLES DE SESIÓN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'empresa_seleccionada' not in st.session_state: st.session_state.empresa_seleccionada = None

def cargar_configuracion():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        default_config = {
            "Técnicos": {
                "descripcion": "Operación 24/7",
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

# --- 2. TEMATIZACIÓN DINÁMICA (CABLEMOVIL VS GREENMOVIL) ---
empresa_actual = st.session_state.empresa_seleccionada

if empresa_actual == "Greenmovil SAS":
    # 🟢 TEMA GREENMOVIL (Verde Corporativo Institucional)
    PRIMARY_COLOR = "#145a4f"
    SIDEBAR_BG = "#145a4f"
    SIDEBAR_TEXT = "#FFFFFF" 
    APP_BG = "#F2FBF7"       
    BTN_GRADIENT = "linear-gradient(135deg, #0d3d35 0%, #145a4f 100%)" 
    BTN_SHADOW = "rgba(20, 90, 79, 0.4)"
    CARD_GRADIENT = "linear-gradient(135deg, #0d3d35 0%, #145a4f 100%)"
else:
    # 🔵 TEMA CABLEMOVIL / GENÉRICO (Blanco y Azul Marino)
    PRIMARY_COLOR = "#1E3D59"
    SIDEBAR_BG = "#FFFFFF"
    SIDEBAR_TEXT = "#1E3D59"
    APP_BG = "#F4F7F6"
    BTN_GRADIENT = "linear-gradient(135deg, #1E3D59 0%, #3a6073 100%)"
    BTN_SHADOW = "rgba(30, 61, 89, 0.4)"
    CARD_GRADIENT = "linear-gradient(135deg, #1E3D59 0%, #3a6073 100%)"

st.markdown(f"""
    <style>
    /* Fondo general de la aplicación */
    .stApp {{ background-color: {APP_BG}; transition: 0.5s ease; }}
    
    /* Barra Lateral */
    [data-testid="stSidebar"] {{ 
        background-color: {SIDEBAR_BG} !important; 
        border-right: 1px solid #E5E7EB; 
        transition: 0.5s ease;
    }}
    
    /* Textos en Barra Lateral */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3, 
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] div[data-baseweb="radio"] div {{
        color: {SIDEBAR_TEXT} !important;
        font-weight: 600;
    }}
    
    /* Caja de subida de archivos adaptada al tema */
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {{
        background-color: rgba(255, 255, 255, 0.05) !important;
        padding: 15px;
        border-radius: 12px;
        border: 2px dashed {SIDEBAR_TEXT} !important;
        margin-bottom: 15px;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"] section * {{
        color: {SIDEBAR_TEXT} !important; 
    }}
    
    /* Botones Globales con Contraste */
    .stButton>button {{ 
        width: 100%; 
        border-radius: 12px; 
        font-weight: 700; 
        height: 3.2em; 
        transition: all 0.3s ease; 
        border: none; 
        background: {BTN_GRADIENT} !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
    }}
    .stButton>button:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 15px {BTN_SHADOW};
    }}
    .stButton>button * {{
        color: #FFFFFF !important;
    }}

    /* Inputs de texto */
    .stTextInput>div>div>input {{
        border-radius: 10px;
        border: 1.5px solid #d1d5db;
        padding: 12px 15px;
        color: #17202A !important;
    }}
    .stTextInput>div>div>input:focus {{
        border-color: {PRIMARY_COLOR};
        box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.1);
    }}

    /* Botones Grandes Selección Empresa */
    .btn-empresa>button {{
        height: 8em !important;
        font-size: 1.5rem !important;
        background: white !important;
        color: #1E3D59 !important; /* Siempre azul para que se lean bien */
        border: 2px solid #1E3D59 !important;
    }}
    .btn-empresa>button:hover {{
        background: #1E3D59 !important;
        color: white !important;
    }}

    /* Tarjeta Bienvenida */
    .welcome-card {{
        background: {CARD_GRADIENT};
        color: white; 
        padding: 3rem; 
        border-radius: 20px; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.15); 
        margin-bottom: 2.5rem;
        text-align: center;
        transition: 0.5s ease;
    }}
    
    /* Estilos del Login */
    .login-title {{
        text-align: center;
        color: {PRIMARY_COLOR};
        font-weight: 900;
        margin-top: 15px;
        margin-bottom: 5px;
        font-size: 3.2rem;
    }}
    .login-subtitle {{
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        font-weight: 500;
        margin-bottom: 30px;
    }}
    </style>
    """, unsafe_allow_html=True)

def modulo_inicio():
    st.markdown(f'''
        <div class="welcome-card">
            <h1 style="font-size: 2.5rem; font-weight: 800; color: white;">👋 ¡Bienvenido al Panel de {st.session_state.empresa_seleccionada}!</h1>
            <p style="font-size: 1.3rem; opacity: 0.9; margin-top: 10px; color: white;">
                Inteligencia Operativa y Sistematización de Turnos.
            </p>
        </div>
    ''', unsafe_allow_html=True)
    
    if st.session_state.empresa_seleccionada == "Cablemovil SAS":
        try:
            df_p = cargar_excel("empleados_grupos.xlsx") 
            total_emp = len(df_p) if not df_p.empty else "0"
        except:
            total_emp = "0"
    else:
        total_emp = "Módulo Dinámico"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👷 Personal Registrado", total_emp)
    c2.metric("📂 Modelos Activos", len(st.session_state.config_personal))
    c3.metric("⚖️ Deuda Global", "0 días")
    c4.metric("📡 Estado de BD", "Conectado", delta="Estable")

    st.divider()
    st.subheader("🇨🇴 Contexto Legal Global: Reforma Laboral 2026")
    st.info("📉 **Reducción de la Jornada Semanal:** Para el año 2026 la jornada ordinaria máxima es de 42 horas semanales.")

# --- PANTALLA 1: LOGIN (Directo, sin Splash) ---
if not st.session_state.logged_in:
    _, login_center, _ = st.columns([1.5, 2, 1.5])
    with login_center:
        st.write(""); st.write(""); st.write("")
        with st.container():
            # Agrandamos la columna central para el logo
            _, img_login, _ = st.columns([1, 1.8, 1])
            with img_login: st.image(LOGO_MÓVILGO, use_container_width=True)
            
            st.markdown("<h1 class='login-title'>Optimizer Pro 2026</h1>", unsafe_allow_html=True)
            st.markdown("<p class='login-subtitle'>Software para la gestión de turnos</p>", unsafe_allow_html=True)
            
            u = st.text_input("👤 Nombre de Usuario", placeholder="Ej: admin")
            p = st.text_input("🔒 Contraseña", type="password", placeholder="••••••••")
            
            st.write("")
            if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
                if u == "admin" and p == "movilgo2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Por favor, intenta de nuevo.")

# --- PANTALLA 2: SELECCIÓN DE EMPRESA ---
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

# --- PANTALLA 3: INTERIOR DE LA APLICACIÓN (SEGÚN EMPRESA) ---
else:
    with st.sidebar:
        st.write("")
        st.image(LOGO_MÓVILGO, use_container_width=True)
        st.markdown(f"<h4 style='text-align:center; color: {SIDEBAR_TEXT};'>{st.session_state.empresa_seleccionada}</h4>", unsafe_allow_html=True)
        st.divider()
        
        # --- MENÚ DINÁMICO SEGÚN LA EMPRESA ---
        if st.session_state.empresa_seleccionada == "Cablemovil SAS":
            opciones_menu = ["🏠 Inicio", "👥 Personal", "🔧 Prog. Técnicos", "🚀 Prog. Abordaje"]
        elif st.session_state.empresa_seleccionada == "Greenmovil SAS":
            opciones_menu = ["🏠 Inicio", "👥 Personal", "⚙️ Parametrizador", "📅 Mallas Operaciones"]
        else:
            opciones_menu = ["🏠 Inicio"]
            
        menu = st.radio("Navegación del Sistema", opciones_menu)
        
        st.divider()
        if st.button("🔄 Cambiar de Empresa"):
            st.session_state.empresa_seleccionada = None
            st.rerun()
            
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.logged_in = False
            st.session_state.empresa_seleccionada = None
            st.rerun()

    # --- RUTEO DE LÓGICA SEGÚN EMPRESA Y MENÚ ---
    
    if menu == "🏠 Inicio": 
        modulo_inicio()
        
    # --- CABLEMOVIL SAS ---
    elif st.session_state.empresa_seleccionada == "Cablemovil SAS":
        if menu == "👥 Personal": pantalla_personal()
        elif menu == "🔧 Prog. Técnicos": pantalla_programador()
        elif menu == "🚀 Prog. Abordaje": pantalla_abordaje()
            
    # --- GREENMOVIL SAS ---
    elif st.session_state.empresa_seleccionada == "Greenmovil SAS":
        if menu == "👥 Personal": pantalla_personal_green()
        elif menu == "⚙️ Parametrizador": pantalla_parametrizador_green()
        elif menu == "📅 Mallas Operaciones": pantalla_mallas_green()
