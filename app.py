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
# ESTILOS (CSS)
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
    background-color: rgba(30, 41, 59, 0.5);
    color: #F1F5F9;
    border-radius: 12px;
    padding: 12px 20px;
    font-weight: 600;
    text-align: left;
    margin-bottom: 8px;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(30, 41, 59, 1);
    border-color: #10B981;
}

.st-card {
    background-color: #1e293b;
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

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
    st.session_state.diario["fecha"] = datetime.date.today()
    st.session_state.diario["calorias"] = 0
    st.session_state.diario["proteinas"] = 0
    st.session_state.diario["grasas"] = 0
    st.session_state.diario["carbos"] = 0
    st.session_state.diario["historial"] = []

# =================================================
# API GOOGLE
# =================================================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# =================================================
# FUNCIONES
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
    model = genai.GenerativeModel("models/gemini-1.5-pro")

    prompt = """
    Analiza la comida de la imagen.
    Devuelve SOLO un JSON válido sin texto adicional:

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
    st.write("Entrenador nutricional IA")

    if "pagina" not in st.session_state:
        st.session_state.pagina = "Inicio"

    if st.button("🏠 Inicio"):
        st.session_state.pagina = "Inicio"

    if st.button("👤 Configurar Perfil"):
        st.session_state.pagina = "Perfil"

    if st.button("📸 Escanear Comida"):
        st.session_state.pagina = "Escanear"

    if st.button("📊 Mi Progreso"):
        st.session_state.pagina = "Progreso"

# =================================================
# PÁGINAS
# =================================================
if st.session_state.pagina == "Inicio":
    st.markdown('<div class="st-card"><h1>MacroRecio FIT 💪</h1><p>Controla tu alimentación con IA</p></div>', unsafe_allow_html=True)

elif st.session_state.pagina == "Perfil":
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

        if st.form_submit_button("Guardar"):
            st.session_state.usuario = calcular_macros(
                genero, edad, peso, altura, actividad, objetivo
            )
            st.success("Perfil guardado")

elif st.session_state.pagina == "Escanear":
    if not st.session_state.usuario:
        st.warning("Configura tu perfil primero")
        st.stop()

    img = st.file_uploader("Sube una imagen", type=["jpg", "jpeg", "png"])
    if img:
        image = Image.open(img).convert("RGB")
        st.image(image)

        if st.button("Analizar"):
            with st.spinner("Analizando..."):
                data = analizar_comida(image)

                d = st.session_state.diario
                d["calorias"] += data["calorias"]
                d["proteinas"] += data["proteinas"]
                d["grasas"] += data["grasas"]
                d["carbos"] += data["carbos"]
                d["historial"].append(data)

                st.success(f"{data['nombre_plato']} agregado ({data['calorias']} kcal)")

elif st.session_state.pagina == "Progreso":
    u = st.session_state.usuario
    d = st.session_state.diario

    st.metric("Objetivo", f"{u['calorias']} kcal")
    st.metric("Consumido", f"{d['calorias']} kcal")
