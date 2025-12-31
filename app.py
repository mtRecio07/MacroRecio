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
# ESTILOS (NO TOCADOS)
# =================================================
st.markdown("""<style>""" + """/* TODO TU CSS ORIGINAL AQUÍ */""" + """</style>""", unsafe_allow_html=True)

# =================================================
# SESSION STATE
# =================================================
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
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("❌ Falta GOOGLE_API_KEY en los Secrets")

# =================================================
# FUNCIONES BACKEND
# =================================================

def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10 * peso + 6.25 * altura - 5 * edad + (5 if genero == "Hombre" else -161)

    factores = {
        "Sedentario (0 días)": 1.2,
        "Ligero (1-2 días)": 1.375,
        "Moderado (3-4 días)": 1.55,
        "Activo (5-6 días)": 1.725,
        "Muy Activo (7 días)": 1.9
    }

    calorias = tmb * factores[actividad]

    if objetivo == "Perder Grasa":
        calorias -= 400
    elif objetivo == "Ganar Músculo":
        calorias += 300

    proteinas = peso * 2
    grasas = peso * 0.9
    carbos = (calorias - (proteinas * 4 + grasas * 9)) / 4

    return {
        "calorias": int(calorias),
        "proteinas": int(proteinas),
        "grasas": int(grasas),
        "carbos": int(carbos)
    }


def analizar_comida(image):
    model = genai.GenerativeModel("models/gemini-pro-vision")

    prompt = """
    Analiza la comida de la imagen.
    Devuelve SOLO JSON válido:

    {
      "nombre_plato": "string",
      "calorias": int,
      "proteinas": int,
      "grasas": int,
      "carbos": int
    }
    """

    response = model.generate_content([prompt, image])

    texto = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

# =================================================
# SIDEBAR
# =================================================
with st.sidebar:
    st.title("🥑 MacroRecio")
    st.write("Tu entrenador nutricional IA")
    st.markdown("---")

    if "pagina_actual" not in st.session_state:
        st.session_state.pagina_actual = "Inicio"

    if st.button("🏠 Inicio", use_container_width=True):
        st.session_state.pagina_actual = "Inicio"
        st.rerun()

    if st.button("👤 Configurar Perfil", use_container_width=True):
        st.session_state.pagina_actual = "Configurar Perfil"
        st.rerun()

    if st.button("📸 Escanear Comida", use_container_width=True):
        st.session_state.pagina_actual = "Escanear Comida"
        st.rerun()

    st.markdown("---")

    if st.session_state.usuario:
        st.markdown(
            f"<div class='goal-card'>🎯 Objetivo: {st.session_state.usuario['calorias']} kcal</div>",
            unsafe_allow_html=True
        )

    if st.button("📊 VER RESUMEN DEL DÍA", use_container_width=True):
        st.session_state.pagina_actual = "Mi Progreso Diario"
        st.rerun()

# =================================================
# PÁGINAS
# =================================================

if st.session_state.pagina_actual == "Configurar Perfil":
    with st.form("perfil"):
        genero = st.selectbox("Género", ["Hombre", "Mujer"])
        edad = st.number_input("Edad", 15, 90, 25)
        peso = st.number_input("Peso (kg)", 40, 150, 70)
        altura = st.number_input("Altura (cm)", 140, 220, 170)
        actividad = st.selectbox("Actividad", [
            "Sedentario (0 días)",
            "Ligero (1-2 días)",
            "Moderado (3-4 días)",
            "Activo (5-6 días)",
            "Muy Activo (7 días)"
        ])
        objetivo = st.selectbox("Objetivo", ["Perder Grasa", "Mantener Peso", "Ganar Músculo"])
        ok = st.form_submit_button("Guardar")

    if ok:
        st.session_state_
