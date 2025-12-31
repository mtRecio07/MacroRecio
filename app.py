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
# IA VISIÓN (GRATIS)
# =================================================
def analizar_comida(image):
    try:
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

        response = model.generate_content(
            [
                prompt,
                {
                    "mime_type": "image/jpeg",
                    "data": image.tobytes()
                }
            ]
        )

        texto = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(texto)

    except Exception as e:
        st.error(f"Error al analizar la comida: {e}")
        return None

# =================================================
# CÁLCULO DE MACROS (REAL)
# =================================================
def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10 * peso + 6.25 * altura - 5 * edad + (5 if genero == "Hombre" else -161)

    factores = {
        "Sedentario": 1.2,
        "Ligero": 1.375,
        "Moderado": 1.55,
        "Activo": 1.725,
        "Muy Activo": 1.9
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
menu = st.sidebar.radio("Navegación", ["Inicio", "Perfil", "Escáner"])

# =================================================
# INICIO
# =================================================
if menu == "Inicio":
    st.title("🥗 MacroRecioIA")
    st.subheader("Tu nutrición, medida con IA")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### ¿Qué es MacroRecioIA?
        - 📸 Escanea tus comidas
        - 🔢 Calcula tus macros diarios
        - 📊 Lleva tu progreso nutricional
        - 🎯 Te guía hacia tu objetivo físico
        """)

        st.success("Comer bien no es difícil. Medirlo, tampoco.")

    with col2:
        st.image(
            "https://images.unsplash.com/photo-1490645935967-10de6ba17061",
            use_column_width=True
        )

# =================================================
# PERFIL
# =================================================
elif menu == "Perfil":
    st.title("👤 Tu Perfil Nutricional")

    with st.form("perfil"):
        col1, col2 = st.columns(2)

        with col1:
            genero = st.selectbox("Género", ["Hombre", "Mujer"])
            edad = st.number_input("Edad", 10, 100, 25)
            peso = st.number_input("Peso (kg)", 30, 200, 70)

        with col2:
            altura = st.number_input("Altura (cm)", 100, 250, 170)
            actividad = st.selectbox("Actividad", ["Sedentario", "Ligero", "Moderado", "Activo", "Muy Activo"])
            objetivo = st.selectbox("Objetivo", ["Perder Grasa", "Mantener Peso", "Ganar Músculo"])

        ok = st.form_submit_button("Calcular requerimientos")

    if ok:
        st.session_state.usuario = calcular_macros(
            genero, edad, peso, altura, actividad, objetivo
        )
        st.success("Metas guardadas correctamente")

    if st.session_state.usuario:
        u = st.session_state.usuario
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Calorías", u["calorias"])
        c2.metric("💪 Proteínas", f'{u["proteinas"]} g')
        c3.metric("🥑 Grasas", f'{u["grasas"]} g')
        c4.metric("🍞 Carbos", f'{u["carbos"]} g')

# =================================================
# ESCÁNER
# =================================================
elif menu == "Escáner":
    st.title("📸 Escáner de Comidas")

    if not st.session_state.usuario:
        st.warning("Primero completá tu perfil")
        st.stop()

    img = st.file_uploader("Subí una foto de tu comida", ["jpg", "png", "jpeg"])

    if img:
        image = Image.open(img).convert("RGB")
        st.image(image, width=350)

        if st.button("Analizar comida"):
            data = analizar_comida(image)

            if data:
                d = st.session_state.diario
                d["calorias"] += data["calorias"]
                d["proteinas"] += data["proteinas"]
                d["grasas"] += data["grasas"]
                d["carbos"] += data["carbos"]
                d["historial"].append(data)

                st.success(f'🍽️ {data["nombre_plato"]}')

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Calorías", data["calorias"])
                col2.metric("Proteínas", f'{data["proteinas"]} g')
                col3.metric("Grasas", f'{data["grasas"]} g')
                col4.metric("Carbos", f'{data["carbos"]} g')

    # PROGRESO DIARIO
    u = st.session_state.usuario
    d = st.session_state.diario

    st.divider()
    st.subheader("📊 Progreso Diario")

    st.progress(min(d["calorias"] / u["calorias"], 1.0))

    if d["calorias"] < u["calorias"]:
        st.info("Todavía te faltan calorías para tu objetivo")
    elif d["calorias"] > u["calorias"]:
        st.warning("Te excediste en calorías hoy")
    else:
        st.success("¡Objetivo diario alcanzado!")
