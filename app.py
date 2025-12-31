import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime

# =================================================
# CONFIGURACIÓN GENERAL
# =================================================
st.set_page_config(
    page_title="MacroRecioIA",
    page_icon="🥑",
    layout="wide"
)

# =================================================
# ESTILOS PREMIUM
# =================================================
st.markdown("""
<style>
.metric-card {
    background-color: #0f172a;
    padding: 20px;
    border-radius: 16px;
    text-align: center;
    color: white;
}
.progress-good {color: #22c55e;}
.progress-mid {color: #eab308;}
.progress-bad {color: #ef4444;}
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

# Reset diario automático
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
# API KEY
# =================================================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# =================================================
# IA VISIÓN
# =================================================
def analizar_comida(image):
    model = genai.GenerativeModel("models/gemini-1.5-flash")

    prompt = """
    Analiza la comida de la imagen.
    Respondé SOLO en JSON válido:
    {
      "nombre_plato": "string",
      "calorias": int,
      "proteinas": int,
      "grasas": int,
      "carbos": int
    }
    """

    response = model.generate_content([
        prompt,
        {"mime_type": "image/jpeg", "data": image.tobytes()}
    ])

    texto = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

# =================================================
# CÁLCULO DE MACROS
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

# =================================================
# SIDEBAR
# =================================================
st.sidebar.title("🥑 MacroRecioIA")
menu = st.sidebar.radio("Navegación", ["Inicio", "Perfil", "Dashboard", "Escáner"])

# =================================================
# INICIO
# =================================================
if menu == "Inicio":
    st.title("🥗 MacroRecioIA")
    st.subheader("Nutrición inteligente con IA")

    st.markdown("""
    - 📸 Escaneá comidas
    - 📊 Seguimiento real
    - 🎯 Objetivos claros
    - 🔁 Reset diario automático
    """)

# =================================================
# PERFIL
# =================================================
elif menu == "Perfil":
    st.title("👤 Perfil Nutricional")

    with st.form("perfil"):
        c1, c2 = st.columns(2)

        with c1:
            genero = st.selectbox("Género", ["Hombre", "Mujer"])
            edad = st.number_input("Edad", 10, 100, 25)
            peso = st.number_input("Peso (kg)", 30, 200, 70)

        with c2:
            altura = st.number_input("Altura (cm)", 100, 250, 170)
            actividad = st.selectbox(
                "Nivel de actividad",
                [
                    "Sedentario (0 días)",
                    "Ligero (1-2 días)",
                    "Moderado (3-4 días)",
                    "Activo (5-6 días)",
                    "Muy Activo (7 días)"
                ]
            )
            objetivo = st.selectbox(
                "Objetivo",
                ["Perder Grasa", "Mantener Peso", "Ganar Músculo"]
            )

        guardar = st.form_submit_button("Guardar y calcular")

    if guardar:
        st.session_state.usuario = calcular_macros(
            genero, edad, peso, altura, actividad, objetivo
        )
        st.success("Perfil guardado correctamente")

    if st.session_state.usuario:
        u = st.session_state.usuario
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Calorías", u["calorias"])
        c2.metric("💪 Proteínas", f"{u['proteinas']} g")
        c3.metric("🥑 Grasas", f"{u['grasas']} g")
        c4.metric("🍞 Carbos", f"{u['carbos']} g")

# =================================================
# DASHBOARD AVANZADO
# =================================================
elif menu == "Dashboard":
    if not st.session_state.usuario:
        st.warning("Completá tu perfil primero")
        st.stop()

    u = st.session_state.usuario
    d = st.session_state.diario

    st.title("📊 Dashboard Diario")

    progreso = d["calorias"] / u["calorias"]
    st.progress(min(progreso, 1.0))

    if progreso < 0.7:
        st.markdown("<h3 class='progress-bad'>⚠ Vas muy por debajo</h3>", unsafe_allow_html=True)
    elif progreso < 0.95:
        st.markdown("<h3 class='progress-mid'>🟡 Podrías mejorar</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 class='progress-good'>✅ Vas excelente</h3>", unsafe_allow_html=True)

    st.subheader("🍽 Historial de comidas")
    for h in d["historial"]:
        st.write(f"- {h['nombre_plato']} | {h['calorias']} kcal")

# =================================================
# ESCÁNER
# =================================================
elif menu == "Escáner":
    if not st.session_state.usuario:
        st.warning("Primero configurá tu perfil")
        st.stop()

    st.title("📸 Escáner de Comidas")

    img = st.file_uploader("Subí una foto", ["jpg", "png", "jpeg"])

    if img:
        image = Image.open(img).convert("RGB")
        st.image(image, width=300)

        if st.button("Analizar comida"):
            data = analizar_comida(image)

            d = st.session_state.diario
            d["calorias"] += data["calorias"]
            d["proteinas"] += data["proteinas"]
            d["grasas"] += data["grasas"]
            d["carbos"] += data["carbos"]
            d["historial"].append(data)

            st.success(f"🍽 {data['nombre_plato']} registrado")
