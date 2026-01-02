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

/* Sidebar */
[data-testid="stSidebar"] {
    background: #020617;
    border-right: 1px solid rgba(255,255,255,0.05);
}

/* Buttons */
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

/* Cards */
.card {
    background: rgba(30,41,59,0.65);
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 22px;
    border: 1px solid rgba(255,255,255,0.05);
}

/* Metrics */
[data-testid="stMetric"] {
    background: rgba(30,41,59,0.6);
    padding: 16px;
    border-radius: 14px;
    text-align: center;
}

/* Progress */
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
        <p style="font-size:18px; max-width:800px;">
        Tu entrenador nutricional inteligente para aprender a comer mejor,
        progresar sin extremos y mantener resultados reales.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.image("https://images.unsplash.com/photo-1490645935967-10de6ba17061", use_container_width=True)
    c2.image("https://images.unsplash.com/photo-1517836357463-d25dfeac3438", use_container_width=True)
    c3.image("https://images.unsplash.com/photo-1504674900247-0877df9cc836", use_container_width=True)

    st.markdown("""
    <div class="card" style="text-align:center;">
        <h3>🌱 El progreso no es perfecto, es constante</h3>
        <p>No necesitás dietas extremas, necesitás un sistema que puedas sostener.</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    c1.markdown("""
    <div class="card">
        <h2>¿Para qué sirve?</h2>
        <ul>
            <li>📊 Calcular tus macros personalizados</li>
            <li>📸 Analizar tus comidas con IA</li>
            <li>📈 Ver tu progreso diario</li>
            <li>🧠 Aprender hábitos saludables</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    c2.markdown("""
    <div class="card">
        <h2>¿Cómo se usa?</h2>
        <ol>
            <li>Completá tu perfil</li>
            <li>Obtené tus requerimientos</li>
            <li>Escaneá tus comidas</li>
            <li>Seguimiento simple y visual</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='card'><h3>🔥 Constancia</h3><p>Hacelo posible, no perfecto.</p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card'><h3>🧠 Paciencia</h3><p>Los cambios reales toman tiempo.</p></div>", unsafe_allow_html=True)
    c3.markdown("<div class='card'><h3>💚 Equilibrio</h3><p>Comer bien también es disfrutar.</p></div>", unsafe_allow_html=True)

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
            actividad = st.selectbox("Actividad", ["Sedentario", "Ligero", "Moderado", "Activo", "Muy activo"])
            objetivo = st.selectbox("Objetivo", ["Perder grasa", "Mantener", "Ganar músculo"])

        ok = st.form_submit_button("Calcular requerimientos")

    if ok:
        st.session_state.usuario = calcular_macros(genero, edad, peso, altura, actividad, objetivo)

    if st.session_state.usuario:
        u = st.session_state.usuario
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Calorías", u["calorias"])
        c2.metric("🥩 Proteínas", u["proteinas"])
        c3.metric("🥑 Grasas", u["grasas"])
        c4.metric("🍞 Carbos", u["carbos"])

elif st.session_state.pagina == "Escaner":
    if not st.session_state.usuario:
        st.warning("Primero configurá tu perfil")
        st.stop()

    st.markdown("<div class='card'><h2>Escanear comida</h2></div>", unsafe_allow_html=True)

    img = st.file_uploader("Subí una foto", ["jpg", "jpeg", "png"])
    if img:
        image = Image.open(img).convert("RGB")
        st.image(image, width=320)

        if st.button("Analizar comida"):
            with st.spinner("Analizando con IA..."):
                data = analizar_comida(image)

            d = st.session_state.diario
            for k in ["calorias", "proteinas", "grasas", "carbos"]:
                d[k] += data[k]
            d["historial"].append(data)

            st.success(f"✅ {data['nombre_plato']} agregado")

elif st.session_state.pagina == "Progreso":
    u = st.session_state.usuario
    d = st.session_state.diario

    st.markdown("<div class='card'><h2>Progreso diario</h2></div>", unsafe_allow_html=True)

    st.progress(min(d["calorias"] / u["calorias"], 1.0))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 Consumidas", d["calorias"])
    c2.metric("🥩 Proteínas", d["proteinas"])
    c3.metric("🥑 Grasas", d["grasas"])
    c4.metric("🍞 Carbos", d["carbos"])

    if d["historial"]:
        st.markdown("### 🍽 Historial")
        for h in d["historial"]:
            st.write(f"- {h['nombre_plato']} — {h['calorias']} kcal")
