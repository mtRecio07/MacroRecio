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
# ESTILOS
# =================================================
st.markdown("""
<style>
.stApp { background-color: #0f172a; color: white; }
.stButton>button { background-color:#10B981; color:white; font-weight:600; }
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
# GEMINI CONFIG
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
Analiza la comida de la imagen y devuelve SOLO este JSON válido:
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
        {
            "mime_type": "image/jpeg",
            "data": image_bytes
        }
    ])

    text = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero=="Hombre" else -161)

    factores = {
        "Sedentario": 1.2,
        "Ligero": 1.375,
        "Moderado": 1.55,
        "Activo": 1.725,
        "Muy activo": 1.9
    }

    calorias = tmb * factores[actividad]
    if objetivo == "Perder grasa":
        calorias -= 400
    elif objetivo == "Ganar músculo":
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
# SIDEBAR
# =================================================
with st.sidebar:
    st.title("💪 MacroRecioIA")

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
    st.title("Bienvenido a MacroRecioIA")
    st.write("Calculá tus macros y analizá tu comida con IA")

elif st.session_state.pagina == "Perfil":
    st.title("Perfil nutricional")

    with st.form("perfil"):
        genero = st.selectbox("Género", ["Hombre", "Mujer"])
        edad = st.number_input("Edad", 15, 90, 25)
        peso = st.number_input("Peso (kg)", 40, 150, 70)
        altura = st.number_input("Altura (cm)", 140, 220, 170)
        actividad = st.selectbox("Actividad", ["Sedentario", "Ligero", "Moderado", "Activo", "Muy activo"])
        objetivo = st.selectbox("Objetivo", ["Perder grasa", "Mantener", "Ganar músculo"])
        ok = st.form_submit_button("Calcular")

    if ok:
        st.session_state.usuario = calcular_macros(
            genero, edad, peso, altura, actividad, objetivo
        )

    if st.session_state.usuario:
        u = st.session_state.usuario
        st.metric("🔥 Calorías", u["calorias"])
        st.metric("🥩 Proteínas (g)", u["proteinas"])
        st.metric("🥑 Grasas (g)", u["grasas"])
        st.metric("🍞 Carbos (g)", u["carbos"])

elif st.session_state.pagina == "Escaner":
    if not st.session_state.usuario:
        st.warning("Primero configurá tu perfil")
        st.stop()

    img = st.file_uploader("Subí una foto de tu comida", ["jpg", "jpeg", "png"])
    if img:
        image = Image.open(img).convert("RGB")
        st.image(image, width=300)

        if st.button("Analizar comida"):
            with st.spinner("Analizando comida..."):
                data = analizar_comida(image)

            d = st.session_state.diario
            for k in ["calorias", "proteinas", "grasas", "carbos"]:
                d[k] += data[k]
            d["historial"].append(data)

            st.success(f"✅ {data['nombre_plato']} agregado")

elif st.session_state.pagina == "Progreso":
    u = st.session_state.usuario
    d = st.session_state.diario

    st.progress(min(d["calorias"] / u["calorias"], 1.0))
    st.write("🔥 Calorías:", d["calorias"])
    st.write("🥩 Proteínas:", d["proteinas"])
    st.write("🥑 Grasas:", d["grasas"])
    st.write("🍞 Carbos:", d["carbos"])

    for h in d["historial"]:
        st.write(f"- {h['nombre_plato']} ({h['calorias']} kcal)")
