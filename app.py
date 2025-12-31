import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# =================================================
# CONFIGURACIÓN INICIAL
# =================================================
st.set_page_config(
    page_title="NutriIA Gratis",
    page_icon="🥑",
    layout="wide"
)

# Session State
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
# API KEY (Streamlit Secrets)
# =================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception:
    st.error("❌ Falta GOOGLE_API_KEY en los Secrets de Streamlit")
    st.stop()

# =================================================
# FUNCIÓN GEMINI (CORREGIDA Y ESTABLE)
# =================================================
def consultar_gemini_json(prompt, image=None):
    try:
        model = genai.GenerativeModel("gemini-1.5-pro")

        if image is not None:
            response = model.generate_content([prompt, image])
        else:
            response = model.generate_content(prompt)

        texto = response.text.strip()
        texto = texto.replace("```json", "").replace("```", "").strip()

        return json.loads(texto)

    except Exception as e:
        st.error(f"Error conectando con la IA: {e}")
        return None

# =================================================
# BARRA LATERAL
# =================================================
st.sidebar.title("🥑 Menú Principal")
menu = st.sidebar.radio(
    "Ir a:",
    ["🏠 Inicio", "👤 Mi Perfil & Metas", "📸 Escáner de Comida"]
)

# =================================================
# 1. INICIO
# =================================================
if menu == "🏠 Inicio":
    st.title("Bienvenido a tu Nutricionista de Bolsillo 🥗")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### ¿Qué hace esta App?
        1. Definís tus metas nutricionales
        2. Sacás fotos de tus comidas
        3. La IA calcula todo automáticamente
        """)

    with col2:
        st.image(
            "https://images.unsplash.com/photo-1512621776951-a57141f2eefd",
            use_column_width=True
        )

    st.info("👈 Comenzá en la sección **Mi Perfil & Metas**")

# =================================================
# 2. PERFIL & METAS
# =================================================
elif menu == "👤 Mi Perfil & Metas":
    st.header("Configuración Personal")

    with st.form("perfil_form"):
        col1, col2 = st.columns(2)

        with col1:
            genero = st.selectbox("Género", ["Hombre", "Mujer"])
            edad = st.number_input("Edad", 10, 100, 25)
            altura = st.number_input("Altura (cm)", 100, 250, 170)

        with col2:
            peso = st.number_input("Peso (kg)", 30, 200, 70)
            actividad = st.selectbox(
                "Nivel de Actividad",
                [
                    "Sedentario",
                    "Ligero (1-3 días)",
                    "Moderado (3-5 días)",
                    "Activo (6-7 días)",
                    "Muy Activo"
                ]
            )
            objetivo = st.selectbox(
                "Objetivo",
                ["Perder Grasa", "Mantener Peso", "Ganar Músculo", "Recomposición"]
            )

        submit = st.form_submit_button("Calcular Requerimientos")

    if submit:
        with st.spinner("Calculando requerimientos..."):
            prompt = f"""
            Actúa como nutricionista deportivo.
            Persona: {genero}, {edad} años, {peso} kg, {altura} cm.
            Actividad: {actividad}. Objetivo: {objetivo}.

            Devuelve SOLO un JSON válido:
            {{
              "calorias": int,
              "proteinas": int,
              "grasas": int,
              "carbos": int,
              "agua_litros": float,
              "consejo": "string"
            }}
            """

            datos = consultar_gemini_json(prompt)

            if datos:
                st.session_state.usuario = datos
                st.success("✅ Metas guardadas correctamente")

    if st.session_state.usuario:
        u = st.session_state.usuario
        st.divider()
        st.subheader("🎯 Metas Diarias")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Calorías", u["calorias"])
        c2.metric("Proteínas", f"{u['proteinas']} g")
        c3.metric("Grasas", f"{u['grasas']} g")
        c4.metric("Carbos", f"{u['carbos']} g")

# =================================================
# 3. ESCÁNER DE COMIDA
# =================================================
elif menu == "📸 Escáner de Comida":
    st.header("Registro de Comidas")

    if not st.session_state.usuario:
        st.warning("⚠️ Configurá primero tu perfil")
        st.stop()

    metas = st.session_state.usuario
    diario = st.session_state.diario

    progreso = min(diario["calorias"] / metas["calorias"], 1.0)
    st.progress(progreso, text=f"{diario['calorias']} / {metas['calorias']} kcal")

    archivo = st.file_uploader(
        "Subí una foto de tu comida",
        type=["jpg", "jpeg", "png"]
    )

    if archivo:
        imagen = Image.open(archivo)
        st.image(imagen, width=300)

        if st.button("➕ Analizar y Agregar"):
            with st.spinner("Analizando comida..."):
                prompt = """
                Analiza esta comida.
                Devuelve SOLO un JSON válido:
                {
                  "nombre_plato": "string",
                  "calorias": int,
                  "proteinas": int,
                  "grasas": int,
                  "carbos": int,
                  "es_saludable": bool
                }
                """

                resultado = consultar_gemini_json(prompt, imagen)

                if resultado:
                    diario["calorias"] += resultado["calorias"]
                    diario["proteinas"] += resultado["proteinas"]
                    diario["grasas"] += resultado["grasas"]
                    diario["carbos"] += resultado["carbos"]
                    diario["historial"].append(resultado)

                    st.success(f"✔ {resultado['nombre_plato']} agregado")
                    st.rerun()

    if diario["historial"]:
        with st.expander("📋 Historial del día"):
            for item in diario["historial"]:
                st.write(f"• {item['nombre_plato']} — {item['calorias']} kcal")
