import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
import io

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="MacroRecioIA",
    page_icon="💪",
    layout="wide"
)

# =================================================
# ESTILOS PREMIUM
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background: linear-gradient(135deg, #0f172a, #020617);
    color: #f8fafc;
}

[data-testid="stSidebar"] {
    background: #020617;
    border-right: 1px solid rgba(255,255,255,0.05);
}

.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #10B981, #059669);
    color: white;
    border-radius: 12px;
    padding: 12px;
    font-weight: 600;
    border: none;
    margin-top: 6px;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #34D399, #10B981);
}

.card {
    background: rgba(30,41,59,0.65);
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 22px;
    border: 1px solid rgba(255,255,255,0.05);
}

[data-testid="stMetric"] {
    background: rgba(30,41,59,0.6);
    padding: 16px;
    border-radius: 14px;
    text-align: center;
}

.stProgress > div > div > div > div {
    background-color: #10B981;
}

img {
    border-radius: 16px;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# SESSION STATE
# =================================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

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

# =================================================
# GEMINI
# =================================================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# =================================================
# FUNCIONES
# =================================================
def analizar_comida(image: Image.Image):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()

    prompt = """
Analiza la comida y devuelve SOLO este JSON válido:
{
  "nombre_plato": "string",
  "calorias": number,
  "proteinas": number,
  "grasas": number,
  "carbos": number
}
"""

    response = model.generate_content([
        prompt,
        {"mime_type": "image/jpeg", "data": image_bytes}
    ])

    limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(limpio)

def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero == "Hombre" else -161)

    factores = {
        "Sedentario (0 días)": 1.2,
        "Ligero (1–2 días)": 1.375,
        "Moderado (3–4 días)": 1.55,
        "Activo (5–6 días)": 1.725,
        "Muy activo (7 días)": 1.9
    }

    calorias = tmb * factores[actividad]

    if objetivo == "Ganar músculo":
        calorias += 300
    elif objetivo == "Perder grasa":
        calorias -= 400
    elif objetivo == "Recomposición corporal":
        calorias -= 150
    elif objetivo == "Mantener físico":
        calorias = calorias

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
# SIDEBAR
# =================================================
with st.sidebar:
    st.title("💪 MacroRecioIA")
    st.caption("Nutrición inteligente con IA")

    if st.button("🏠 Inicio"):
        st.session_state.pagina = "Inicio"
    if st.button("👤 Perfil"):
        st.session_state.pagina = "Perfil"
    if st.button("📸 Analizar comida"):
        st.session_state.pagina = "Escaner"
    if st.button("📊 Progreso"):
        st.session_state.pagina = "Progreso"

# =================================================
# PÁGINAS
# =================================================
if st.session_state.pagina == "Inicio":
    st.markdown("""
    <div class="card">
        <h1>Bienvenido a MacroRecioIA 💪</h1>
        <p>Tu entrenador nutricional inteligente.</p>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.pagina == "Perfil":
    st.markdown("<div class='card'><h2>Perfil nutricional</h2></div>", unsafe_allow_html=True)

    with st.form("perfil"):
        c1, c2 = st.columns(2)
        with c1:
            genero = st.selectbox("Género", ["Hombre", "Mujer"])
            edad = st.number_input("Edad", 15, 90, 25)
            peso = st.number_input("Peso (kg)", 40, 150, 70)
        with c2:
            altura = st.number_input("Altura (cm)", 140, 220, 170)
            actividad = st.selectbox(
                "Nivel de actividad",
                [
                    "Sedentario (0 días)",
                    "Ligero (1–2 días)",
                    "Moderado (3–4 días)",
                    "Activo (5–6 días)",
                    "Muy activo (7 días)"
                ]
            )
            objetivo = st.selectbox(
                "Objetivo",
                [
                    "Ganar músculo",
                    "Perder grasa",
                    "Recomposición corporal",
                    "Mantener físico"
                ]
            )

        ok = st.form_submit_button("Calcular requerimientos")

    if ok:
        st.session_state.usuario = calcular_macros(
            genero, edad, peso, altura, actividad, objetivo
        )

    if st.session_state.usuario:
        u = st.session_state.usuario
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Calorías", u["calorias"])
        c2.metric("🥩 Proteínas", u["proteinas"])
        c3.metric("🥑 Grasas", u["grasas"])
        c4.metric("🍞 Carbos", u["carbos"])

elif st.session_state.pagina == "Escaner":
    st.warning("Primero configurá tu perfil")

elif st.session_state.pagina == "Progreso":
    st.info("Completá tu perfil y cargá comidas para ver progreso")
