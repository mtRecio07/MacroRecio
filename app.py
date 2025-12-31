import streamlit as st

import google.generativeai as genai

from PIL import Image

import json

import datetime



# =================================================

# CONFIG GENERAL

# =================================================

st.set_page_config(

    page_title="MacroRecio FIT",

    page_icon="💪",

    layout="wide",

    initial_sidebar_state="expanded"

)



# =================================================

# ESTILOS PREMIUM (CSS AVANZADO)

# =================================================

st.markdown("""

<style>

    /* --- Tipografía y Fondo General --- */

    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');



    html, body, [class*="css"] {

        font-family: 'Inter', sans-serif;

    }



    .stApp {

        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);

        color: #F1F5F9;

    }



    /* --- Componentes: Tarjetas (Cards) --- */

    .st-card {

        background-color: rgba(30, 41, 59, 0.7);

        backdrop-filter: blur(10px);

        border: 1px solid rgba(255, 255, 255, 0.08);

        border-radius: 20px;

        padding: 24px;

        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);

        margin-bottom: 20px;

    }



    /* Tarjetas mini para historial */

    .st-mini-card {

        background-color: rgba(51, 65, 85, 0.5);

        border-radius: 12px;

        padding: 16px;

        margin-bottom: 12px;

        border-left: 4px solid #10B981;

        display: flex;

        justify-content: space-between;

        align-items: center;

    }



    /* --- Títulos --- */

    h1, h2, h3 { color: #ffffff; font-weight: 700; letter-spacing: -0.5px; }

    h2 { border-bottom: 2px solid rgba(16, 185, 129, 0.5); padding-bottom: 10px; margin-bottom: 25px; display: inline-block; }

    p, label { color: #94A3B8; }



    /* --- Métricas --- */

    div[data-testid="stMetricLabel"] { font-size: 0.9rem; color: #94A3B8; font-weight: 600; }

    div[data-testid="stMetricValue"] { font-size: 1.8rem; color: #10B981; font-weight: 700; }



    /* --- Botones --- */

    .stButton > button {

        width: 100%;

        background: linear-gradient(90deg, #10B981 0%, #059669 100%);

        border: none;

        color: white;

        padding: 12px 24px;

        font-size: 16px;

        font-weight: 600;

        border-radius: 12px;

        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);

        transition: all 0.3s ease;

    }

    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6); }



    /* --- Inputs --- */

    .stTextInput > div > div > input, .stNumberInput > div > div > input, .stSelectbox > div > div > div {

        background-color: rgba(15, 23, 42, 0.6);

        color: #F1F5F9;

        border-radius: 10px;

        border: 1px solid rgba(255, 255, 255, 0.1);

    }



    /* --- Barra de Progreso --- */

    .stProgress > div > div > div > div { background-color: #10B981; border-radius: 10px; }

    .stProgress > div > div { background-color: rgba(255,255,255,0.1) !important; border-radius: 10px; height: 12px !important; }



    /* --- Sidebar --- */

    section[data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid rgba(255,255,255,0.05); }

    section[data-testid="stSidebar"] h1 { color: #10B981; font-size: 1.5rem; }



    /* --- Status Tags --- */

    .status-card { padding: 15px; border-radius: 15px; text-align: center; font-weight: bold; margin-top: 20px; }

    .status-bad { background: rgba(239, 68, 68, 0.2); color: #EF4444; border: 1px solid #EF4444; }

    .status-avg { background: rgba(245, 158, 11, 0.2); color: #F59E0B; border: 1px solid #F59E0B; }

    .status-good { background: rgba(16, 185, 129, 0.2); color: #10B981; border: 1px solid #10B981; }

    

    /* Corrección para imágenes redondeadas vía CSS global */

    img { border-radius: 12px; }

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

# API KEY & FUNCIONES

# =================================================

try:

    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

except Exception:

    st.error("Falta configurar la API KEY en los secrets.")



def analizar_comida(image):

    model = genai.GenerativeModel("models/gemini-1.5-flash")

    prompt = """Analiza la comida de la imagen. Respondé SOLO en JSON válido: {"nombre_plato": "string", "calorias": int, "proteinas": int, "grasas": int, "carbos": int}"""

    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image.tobytes()}])

    texto = response.text.replace("```json", "").replace("```", "").strip()

    return json.loads(texto)



def calcular_macros(genero, edad, peso, altura, actividad, objetivo):

    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero == "Hombre" else -161)

    factores = {"Sedentario (0 días)": 1.2, "Ligero (1-2 días)": 1.375, "Moderado (3-4 días)": 1.55, "Activo (5-6 días)": 1.725, "Muy Activo (7 días)": 1.9}

    calorias = tmb * factores[actividad]

    if objetivo == "Perder Grasa": calorias -= 400

    elif objetivo == "Ganar Músculo": calorias += 300

    proteinas = peso * 2

    grasas = peso * 0.9

    carbos = (calorias - (proteinas*4 + grasas*9)) / 4

    return {"calorias": int(calorias), "proteinas": int(proteinas), "grasas": int(grasas), "carbos": int(carbos)}



# =================================================

# SIDEBAR

# =================================================

st.sidebar.markdown("# ⚡ MacroFit AI")

st.sidebar.markdown("---")

menu = st.sidebar.radio(

    "Navegación",

    ["Dashboard Inicio", "Configurar Perfil", "Escanear Alimento"],

    index=0,

    format_func=lambda x: f"{'🏠' if 'Inicio' in x else '👤' if 'Perfil' in x else '📸'}  {x}"

)

st.sidebar.markdown("---")

if st.session_state.usuario:

     st.sidebar.success(f"Objetivo: {st.session_state.usuario.get('calorias')} kcal")

else:

     st.sidebar.warning("Perfil no configurado")



# =================================================

# PANTALLAS

# =================================================



# --- INICIO ---

if "Inicio" in menu:

    st.markdown("""

    <div class="st-card">

        <h1>⚡ Tu Transformación Empieza Hoy.</h1>

        <p style="font-size: 1.2rem;">Control total de tu nutrición con inteligencia artificial.</p>

    </div>

    """, unsafe_allow_html=True)



    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("""<div class="st-card" style="text-align:center;"><h3>📸 Escanea</h3><p>Sube foto de tu plato.</p></div>""", unsafe_allow_html=True)

    with col2:

        st.markdown("""<div class="st-card" style="text-align:center;"><h3>📊 Controla</h3><p>Visualiza tus macros.</p></div>""", unsafe_allow_html=True)

    with col3:

        st.markdown("""<div class="st-card" style="text-align:center;"><h3>🎯 Progresa</h3><p>Alcanza tu objetivo.</p></div>""", unsafe_allow_html=True)

    

    if not st.session_state.usuario:

         st.info("👉 Ve a 'Configurar Perfil' para comenzar.")



# --- PERFIL ---

elif "Perfil" in menu:

    st.markdown('<div class="st-card">', unsafe_allow_html=True)

    st.markdown("<h2>👤 Configuración de Metas</h2>", unsafe_allow_html=True)

    with st.form("perfil"):

        c1, c2 = st.columns(2)

        with c1:

            genero = st.selectbox("Género", ["Hombre", "Mujer"])

            edad = st.number_input("Edad", 10, 100, 25)

            peso = st.number_input("Peso (kg)", 30, 200, 70)

        with c2:

            altura = st.number_input("Altura (cm)", 100, 250, 170)

            actividad = st.selectbox("Nivel de actividad", ["Sedentario (0 días)", "Ligero (1-2 días)", "Moderado (3-4 días)", "Activo (5-6 días)", "Muy Activo (7 días)"])

            objetivo = st.selectbox("Objetivo", ["Perder Grasa", "Mantener Peso", "Ganar Músculo"])

        st.markdown("<br>", unsafe_allow_html=True)

        ok = st.form_submit_button("🚀 CALCULAR MIS REQUERIMIENTOS")



    if ok:

        st.session_state.usuario = calcular_macros(genero, edad, peso, altura, actividad, objetivo)

    st.markdown('</div>', unsafe_allow_html=True)



    if st.session_state.usuario:

        st.markdown('<div class="st-card">', unsafe_allow_html=True)

        st.markdown("<h3>🎯 Tus Metas Diarias</h3>", unsafe_allow_html=True)

        u = st.session_state.usuario

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("🔥 Calorías", u["calorias"])

        c2.metric("💪 Proteínas", f"{u['proteinas']}g")

        c3.metric("🥑 Grasas", f"{u['grasas']}g")

        c4.metric("🍞 Carbos", f"{u['carbos']}g")

        st.markdown('</div>', unsafe_allow_html=True)



# --- ESCÁNER (MODIFICADO: PRIMERO FOTO, LUEGO BARRAS) ---

elif "Escanear" in menu:

    if not st.session_state.usuario:

        st.warning("⚠️ Configura tu perfil primero.")

        st.stop()



    u = st.session_state.usuario

    d = st.session_state.diario

    progreso_val = d["calorias"] / u["calorias"] if u["calorias"] > 0 else 0



    # 1. SECCIÓN DE CARGA (Arriba, como pediste)

    st.markdown('<div class="st-card">', unsafe_allow_html=True)

    st.markdown("<h3>📸 Registro de Comida</h3>", unsafe_allow_html=True)

    

    col_img, col_info = st.columns([1, 2])

    

    with col_img:

        # File uploader simple

        img = st.file_uploader("Sube tu plato", ["jpg", "jpeg", "png"], label_visibility="collapsed")

    

    with col_info:

        if img:

            # CORRECCIÓN AQUÍ: Quitamos 'style' dentro de st.image

            image = Image.open(img).convert("RGB")

            st.image(image, width=300) 

            

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("🔍 ANALIZAR E IMPUTAR PLATO"):

                with st.spinner("Analizando con IA..."):

                    try:

                        data = analizar_comida(image)

                        d = st.session_state.diario

                        d["calorias"] += data["calorias"]

                        d["proteinas"] += data["proteinas"]

                        d["grasas"] += data["grasas"]

                        d["carbos"] += data["carbos"]

                        d["historial"].append(data)

                        st.success(f"✅ ¡{data['nombre_plato']} agregado!")

                        st.rerun()

                    except Exception as e:

                        st.error(f"Error: {e}")

        else:

            st.info("👈 Sube una foto para comenzar el análisis.")

    

    st.markdown('</div>', unsafe_allow_html=True)



    # 2. SECCIÓN DE BARRAS Y DASHBOARD (Abajo)

    st.markdown('<div class="st-card">', unsafe_allow_html=True)

    st.markdown(f"<h2>📊 Progreso del Día <span style='font-size:1rem; color:#94A3B8; float:right'>{d['fecha']}</span></h2>", unsafe_allow_html=True)



    # Barra Principal

    st.markdown(f"<p>Progreso Calórico: <b>{int(progreso_val*100)}%</b> ({d['calorias']} / {u['calorias']} kcal)</p>", unsafe_allow_html=True)

    st.progress(min(progreso_val, 1.0))

    st.markdown("<br>", unsafe_allow_html=True)



    # Métricas

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("🔥 Consumidas", d["calorias"], delta=f"{u['calorias'] - d['calorias']} restantes", delta_color="inverse")

    c2.metric("💪 Proteínas", f"{d['proteinas']}g", f"Meta: {u['proteinas']}g")

    c3.metric("🥑 Grasas", f"{d['grasas']}g", f"Meta: {u['grasas']}g")

    c4.metric("🍞 Carbos", f"{d['carbos']}g", f"Meta: {u['carbos']}g")



    # Estado

    if progreso_val < 0.5:

        st.markdown('<div class="status-card status-avg">🟡 Sigue comiendo para llegar a tu meta.</div>', unsafe_allow_html=True)

    elif progreso_val <= 1.05:

        st.markdown('<div class="status-card status-good">🟢 ¡Vas excelente! Mantén este ritmo.</div>', unsafe_allow_html=True)

    else:

        st.markdown('<div class="status-card status-bad">🔴 Cuidado, te has pasado de calorías.</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)



    # 3. HISTORIAL

    if d["historial"]:

        st.markdown('<div class="st-card">', unsafe_allow_html=True)

        st.markdown("<h3>📋 Comidas de Hoy</h3>", unsafe_allow_html=True)

        for item in reversed(d["historial"]):

            st.markdown(f"""

            <div class="st-mini-card">

                <div>

                    <strong style="font-size: 1.1rem;">{item['nombre_plato']}</strong><br>

                    <span style="color: #94A3B8; font-size: 0.9rem;">P: {item['proteinas']}g | G: {item['grasas']}g | C: {item['carbos']}g</span>

                </div>

                <div style="text-align:right;">

                    <span style="color: #10B981; font-weight:bold; font-size: 1.2rem;">{item['calorias']} kcal</span>

                </div>

            </div>

            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
