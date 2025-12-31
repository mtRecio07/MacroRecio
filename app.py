import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import math

# =================================================
# CONFIGURACIÓN
# =================================================
st.set_page_config("NutriIA Gratis", "🥑", "wide")

if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "diario" not in st.session_state:
    st.session_state.diario = {
        "calorias": 0,
        "proteinas": 0,
        "grasas": 0,
        "carbos": 0,
        "historial": []
    }

# =================================================
# API KEY
# =================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("Falta GOOGLE_API_KEY")
    st.stop()

# =================================================
# IA SOLO PARA IMÁGENES (GRATIS)
# =================================================
def analizar_comida(image):
    try:
        model = genai.GenerativeModel("models/gemini-pro-vision")

        prompt = """
        Analiza la comida de la imagen.
        Responde SOLO JSON:
        {
          "nombre_plato": "string",
          "calorias": int,
          "proteinas": int,
          "grasas": int,
          "carbos": int
        }
        """

        res = model.generate_content([prompt, image])
        texto = res.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)

    except Exception as e:
        st.error(f"Error IA: {e}")
        return None

# =================================================
# CÁLCULO NUTRICIONAL REAL (SIN IA)
# =================================================
def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    if genero == "Hombre":
        tmb = 10*peso + 6.25*altura - 5*edad + 5
    else:
        tmb = 10*peso + 6.25*altura - 5*edad - 161

    factores = {
        "Sedentario": 1.2,
        "Ligero (1-3 días)": 1.375,
        "Moderado (3-5 días)": 1.55,
        "Activo (6-7 días)": 1.725,
        "Muy Activo": 1.9
    }

    calorias = tmb * factores[actividad]

    if objetivo == "Perder Grasa":
        calorias -= 400
    elif objetivo == "Ganar Músculo":
        calorias += 300

    proteinas = peso * 2
    grasas = peso * 0.9
    carbos = (calorias - (proteinas*4 + grasas*9)) / 4

    return {
        "calorias": int(calorias),
        "proteinas": int(proteinas),
        "grasas": int(grasas),
        "carbos": int(carbos)
    }

# =================================================
# UI
# =================================================
st.sidebar.title("🥑 Menú")
menu = st.sidebar.radio("Ir a:", ["Inicio", "Perfil", "Escáner"])

# =================================================
# PERFIL
# =================================================
if menu == "Perfil":
    st.header("Configuración Personal")

    with st.form("perfil"):
        genero = st.selectbox("Género", ["Hombre", "Mujer"])
        edad = st.number_input("Edad", 10, 100, 25)
        peso = st.number_input("Peso (kg)", 30, 200, 70)
        altura = st.number_input("Altura (cm)", 100, 250, 170)
        actividad = st.selectbox(
            "Actividad",
            ["Sedentario", "Ligero (1-3 días)", "Moderado (3-5 días)", "Activo (6-7 días)", "Muy Activo"]
        )
        objetivo = st.selectbox("Objetivo", ["Perder Grasa", "Mantener Pes]()
