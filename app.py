import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime

# =================================================
# CONFIGURACIÓN GENERAL
# =================================================
st.set_page_config(
    page_title="MacroRecio FIT",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================================================
# ESTILOS (NO MODIFICADOS)
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #0f172a; color: #F1F5F9; }

[data-testid="stSidebar"] {
    background-color: #0b1120;
    border-right: 1px solid rgba(255,255,255,0.05);
}

[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background-color: rgba(30,41,59,0.5)!important;
    color: #F1F5F9!important;
    border: 1px solid rgba(255,255,255,0.1)!important;
    border-radius: 12px!important;
    padding: 12px 20px!important;
    font-weight: 600!important;
    text-align: left!important;
    margin-bottom: 8px!important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #10B981!important;
    background-color: rgba(30,41,59,1)!important;
}

.goal-card {
    background-color: rgba(30,41,59,0.5);
    border-radius: 12px;
    padding: 12px;
    text-align: center;
}

.st-card {
    background-color: #1e293b;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
}

.main .stButton > button {
    background-color: #10B981;
    color: white;
    border-radius: 8px;
    padding: 12px;
    font-weight: 600;
}

.stProgress > div > div > div > div { background-color: #10B981; }
img { border-radius: 12px; }
</style>
""", unsafe_allow_html=True)

# =================================================
# SESSION STATE
# =================================================
if "pagina_actual" not in st.session_state:
    st.session_state.pagina_actual = "Inicio"

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "diario" not in st.session_state:
    st.session_state.diario = {
        "fecha": datetime.date.today(),
        "calorias": 0,
        "proteinas": 0,
        "grasas": 0,
        "carbos": 0,
        "historial": []
    }

if st.session_state.diario["fecha"] != datetime.date.today():
    st.session_state.diario = {
        "fecha": datetime.date.today(),
        "calorias": 0,
        "proteinas": 0,
        "grasas": 0,
        "carbos": 0,
        "historial": []
    }

# =================================================
# API GEMINI
# =================================================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def analizar_comida(image):
    model = genai.GenerativeModel("models/gemini-1.5-flash")
