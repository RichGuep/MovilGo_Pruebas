import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date

# --- IMPORTACIÓN DEL MOTOR DE LÓGICA ---
from logic_programador import pantalla_programador, pantalla_personal, cargar_excel

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="MovilGo - Gestión Operativa", 
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
            },
            "Abordaje": {
                "descripcion": "Gestión comercial y de abordaje operativo.",
                "extension_turno": 7,
                "grupos": ["Abordaje"],
                "rotacion": "Alternancia Semanal"
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
    /* Fondo general más limpio */
    .stApp {{ background-color: #F4F7F6; }}
    
    /* Estilos del Sidebar */
    [data-testid="stSidebar"] {{ 
        background-color: {PRIMARY_COLOR}; 
        border-right: 1px solid #ffffff22; 
    }}
    [data-testid="stSidebar"] * {{ color: white !important; font-weight: 500; }}
    
    [data-testid="stSidebar"] [data-testid="stFileUploader"] {{
        background-color: #ffffff !important;
        padding: 12px;
        border-radius: 12px;
        border: 2px dashed #3a6073 !important;
        margin-bottom: 15px;
    }}
    [data-testid="stSidebar"] [data-testid="stFileUploader"] * {{
        color: #1E3D59 !important; 
        font-weight: bold !important;
    }}
    
    /* Inputs de texto modernos (Login y app) */
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
    
    /* Botones primarios con efecto 3D */
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
    
    /* Tarjeta principal del Inicio */
    .welcome-card {{
        background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #3a6073 100%);
        color: white; 
        padding: 3rem; 
        border-radius: 20px; 
        box-shadow: 0 15px 35px rgba(0,0,0,0.15); 
        margin-bottom: 2.5rem;
        text-align: center;
    }}
    
    /* Tipografía del Login */
    .login-title {{
        text-align: center;
        color: {PRIMARY_COLOR};
        font-weight: 800;
        margin-top: 15px;
        margin-bottom: 5px;
        font-size: 2.2rem;
    }}
    .login-subtitle {{
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }}
    </style>
    """, unsafe_allow_html=True)

def modulo_inicio():
    st.markdown(f'''
        <div class="welcome-card">
            <h1 style="font-size: 2.5rem; font-weight: 800;">👋 ¡Bienvenido al Panel de Control {st.session_state.empresa}!</h1>
            <p style="font-size: 1.3rem; opacity: 0.9; margin-top: 10px;">
                Garantizando cobertura técnica y operativa por Grupos bajo el cumplimiento de la Reforma Laboral Colombiana 2026.
            </p>
        </div>
    ''', unsafe_allow_html=True)
    
    df_p = cargar_excel("empleados_grupos.xlsx") 
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👷 Personal Registrado", len(df_p) if not df_p.empty else "0")
    c2.metric("📂 Modelos Activos", len(st.session_state.config_personal))
    c3.metric("⚖️ Deuda Global", "0 días")
    c4.metric("📡 Estado de BD", "Conectado", delta="Estable")

    st.divider()
    st.subheader("🇨🇴 Contexto Legal Global: Reforma Laboral 2026")
    inf1, inf2 = st.columns(2)
    with inf1:
        st.info("📉 **Reducción de la Jornada Semanal:** Para el año 2026 la jornada ordinaria máxima es de 42 horas semanales. El sistema controla los acumulados semanales por empleado.")
    with inf2:
        st.warning("🛌 **Descansos Compensatorios:** El sistema genera deudas automáticas individuales de compensación cuando las necesidades del servicio obligan a laborar en días de descanso base.")

if 'splash_done' not in st.session_state: st.session_state.splash_done = False
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'empresa' not in st.session_state: st.session_state.empresa = "Grupo Movil"

# --- PANTALLA SPLASH (BIENVENIDA) ---
if not st.session_state.splash_done:
    # Sistema de columnas para centrar perfectamente
    _, splash_center, _ = st.columns([1, 2, 1])
    
    with splash_center:
        st.markdown('<div style="text-align:center; margin-top:10vh;">', unsafe_allow_html=True)
        # Logo grande y centrado
        _, img_splash, _ = st.columns([1, 1.5, 1])
        with img_splash:
            st.image(LOGO_MÓVILGO, use_container_width=True)
            
        st.markdown("<h1 style='color:#1E3D59; font-size: 3.5rem; font-weight: 900; margin-top: 20px;'>Optimizer Pro 2026</h1>", unsafe_allow_html=True)
        st.markdown("<p style='font-size: 1.3rem; color: #666; margin-bottom: 40px;'>Inteligencia Operativa y Sistematización de Turnos</p>", unsafe_allow_html=True)
        
        if st.button("INGRESAR AL PORTAL", use_container_width=True):
            st.session_state.splash_done = True
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- PANTALLA DE LOGIN ---
elif not st.session_state.logged_in:
    # Sistema de columnas para encajonar el login en el centro de la pantalla
    _, login_center, _ = st.columns([1.5, 2, 1.5])
    
    with login_center:
        st.write("") 
        st.write("")
        st.write("")
        st.write("")
        
        # Tarjeta visual del login
        with st.container():
            # Logo centrado dentro de la tarjeta
            _, img_login, _ = st.columns([1, 1.2, 1])
            with img_login:
                st.image(LOGO_MÓVILGO, use_container_width=True)
            
            st.markdown("<h2 class='login-title'>Acceso Seguro</h2>", unsafe_allow_html=True)
            st.markdown("<p class='login-subtitle'>Ingresa tus credenciales administrativas</p>", unsafe_allow_html=True)
            
            # Campos de texto con iconos
            u = st.text_input("👤 Nombre de Usuario", placeholder="Ej: admin")
            p = st.text_input("🔒 Contraseña", type="password", placeholder="••••••••")
            
            st.write("")
            if st.button("🚀 INICIAR SESIÓN", use_container_width=True):
                if u == "admin" and p == "movilgo2026":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas. Por favor, intenta de nuevo.")

# --- INTERIOR DE LA APLICACIÓN ---
else:
    with st.sidebar:
        st.write("")
        st.image(LOGO_MÓVILGO, use_container_width=True)
        st.divider()
        menu = st.radio("Navegación del Sistema", ["🏠 Inicio", "👥 Personal", "📅 Programación"])
        st.divider()
        if st.button("🚪 Cerrar Sesión"):
            st.session_state.logged_in = False
            st.session_state.splash_done = False
            st.rerun()

    if menu == "🏠 Inicio": modulo_inicio()
    elif menu == "👥 Personal": pantalla_personal()
    elif menu == "📅 Programación": pantalla_programador()
