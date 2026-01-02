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
    prompt = """
    Analiza la comida y responde SOLO en JSON:
    {
      "nombre_plato": "string",
      "calorias": int,
      "proteinas": int,
      "grasas": int,
      "carbos": int
    }
    """
    response = model.generate_content(
        [prompt, {"mime_type": "image/jpeg", "data": image.tobytes()}]
    )
    limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(limpio)

def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero=="Hombre" else -161)
    factores = {
        "Sedentario (0 días)": 1.2,
        "Ligero (1-2 días)": 1.375,
        "Moderado (3-4 días)": 1.55,
        "Activo (5-6 días)": 1.725,
        "Muy Activo (7 días)": 1.9
    }
    calorias = tmb * factores[actividad]
    if objetivo == "Perder Grasa": calorias -= 400
    if objetivo == "Ganar Músculo": calorias += 300

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
    st.title("💪 MacroRecio FIT")
    st.write("Entrenador nutricional IA")
    st.markdown("---")

    if st.button("🏠 Inicio"): st.session_state.pagina_actual="Inicio"; st.rerun()
    if st.button("👤 Configurar Perfil"): st.session_state.pagina_actual="Perfil"; st.rerun()
    if st.button("📸 Escanear Comida"): st.session_state.pagina_actual="Escaner"; st.rerun()
    if st.button("📊 Mi Progreso"): st.session_state.pagina_actual="Progreso"; st.rerun()

    if st.session_state.usuario:
        st.markdown(f"""
        <div class="goal-card">
        🎯 {st.session_state.usuario["calorias"]} kcal/día
        </div>
        """, unsafe_allow_html=True)

# =================================================
# INICIO
# =================================================
if st.session_state.pagina_actual == "Inicio":
    st.markdown("""
    <div class="st-card">
    <h1>Bienvenido a MacroRecio FIT</h1>
    <p>Tu entrenador nutricional inteligente basado en IA.</p>
    </div>
    """, unsafe_allow_html=True)

    st.image("https://images.unsplash.com/photo-1517836357463-d25dfeac3438", use_column_width=True)

    st.markdown("""
    <div class="st-card">
    <h3>¿Qué hace esta app?</h3>
    <ul>
        <li>Calcula tus requerimientos reales</li>
        <li>Reconoce tu comida con una foto</li>
        <li>Lleva tu progreso diario</li>
    </ul>
    <p><i>Disciplina + Datos = Resultados</i></p>
    </div>
    """, unsafe_allow_html=True)

# =================================================
# PERFIL
# =================================================
elif st.session_state.pagina_actual == "Perfil":
    st.markdown('<div class="st-card"><h2>Configurar Perfil</h2></div>', unsafe_allow_html=True)

    with st.form("perfil"):
        c1,c2=st.columns(2)
        with c1:
            genero=st.selectbox("Género",["Hombre","Mujer"])
            edad=st.number_input("Edad",15,90,25)
            peso=st.number_input("Peso (kg)",40,150,70)
        with c2:
            altura=st.number_input("Altura (cm)",140,220,170)
            actividad=st.selectbox("Actividad",[
                "Sedentario (0 días)","Ligero (1-2 días)",
                "Moderado (3-4 días)","Activo (5-6 días)",
                "Muy Activo (7 días)"
            ])
            objetivo=st.selectbox("Objetivo",["Perder Grasa","Mantener Peso","Ganar Músculo"])
        ok=st.form_submit_button("Calcular requerimientos")

    if ok:
        st.session_state.usuario=calcular_macros(genero,edad,peso,altura,actividad,objetivo)

    if st.session_state.usuario:
        u=st.session_state.usuario
        c1,c2,c3,c4=st.columns(4)
        c1.metric("🔥 Calorías",u["calorias"])
        c2.metric("🥩 Proteínas",f'{u["proteinas"]} g')
        c3.metric("🥑 Grasas",f'{u["grasas"]} g')
        c4.metric("🍞 Carbos",f'{u["carbos"]} g')

# =================================================
# ESCÁNER
# =================================================
elif st.session_state.pagina_actual=="Escaner":
    if not st.session_state.usuario:
        st.warning("Configura tu perfil primero")
        st.stop()

    img=st.file_uploader("Subí una foto",["jpg","jpeg","png"])
    if img:
        image=Image.open(img).convert("RGB")
        st.image(image,width=300)
        if st.button("Analizar comida"):
            data=analizar_comida(image)
            d=st.session_state.diario
            for k in ["calorias","proteinas","grasas","carbos"]:
                d[k]+=data[k]
            d["historial"].append(data)
            st.success(f'{data["nombre_plato"]} agregado')

# =================================================
# PROGRESO
# =================================================
elif st.session_state.pagina_actual=="Progreso":
    u=st.session_state.usuario
    d=st.session_state.diario
    prog=min(d["calorias"]/u["calorias"],1)
    st.progress(prog)

    c1,c2,c3,c4=st.columns(4)
    c1.metric("🔥 Consumidas",d["calorias"])
    c2.metric("🥩 Proteínas",d["proteinas"])
    c3.metric("🥑 Grasas",d["grasas"])
    c4.metric("🍞 Carbos",d["carbos"])

    if d["historial"]:
        for i in d["historial"]:
            st.write(f'{i["nombre_plato"]} - {i["calorias"]} kcal')
