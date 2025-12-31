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
# ESTILOS MODERNOS Y LIMPIOS (CSS)
# =================================================
st.markdown("""
<style>
    /* Tipografía */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Fondo oscuro fitness */
    .stApp {
        background: #0f172a;
        color: #F1F5F9;
    }

    /* --- RADIO BUTTONS MODERNOS (NAVEGACIÓN) --- */
    /* Ocultamos los círculos predeterminados y estilizamos el contenedor */
    div[role="radiogroup"] > label {
        background-color: rgba(30, 41, 59, 0.5);
        padding: 12px 20px;
        border-radius: 12px;
        margin-bottom: 8px;
        border: 1px solid rgba(255,255,255,0.05);
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex; /* Asegura alineación */
        width: 100%;
    }
    
    /* Efecto Hover */
    div[role="radiogroup"] > label:hover {
        background-color: rgba(30, 41, 59, 1);
        border-color: #10B981;
    }

    /* Cuando está seleccionado (Active) */
    div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, #10B981 0%, #059669 100%);
        color: white;
        border: none;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    }

    /* --- CARDS --- */
    .st-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }

    /* --- BOTONES --- */
    .stButton > button {
        width: 100%;
        background-color: #10B981;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-weight: 600;
        transition: 0.2s;
    }
    .stButton > button:hover {
        background-color: #059669;
        color: white;
    }

    /* --- TEXTOS --- */
    h1, h2, h3 { color: white; font-weight: 800; }
    p { color: #94a3b8; }
    
    /* --- BARRA PROGRESO --- */
    .stProgress > div > div > div > div { background-color: #10B981; }
    
    /* Imágenes redondeadas */
    img { border-radius: 12px; }

</style>
""", unsafe_allow_html=True)

# =================================================
# LÓGICA (BACKEND)
# =================================================
# Inicializar variables
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "diario" not in st.session_state:
    st.session_state.diario = {"fecha": datetime.date.today(), "calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0, "historial": []}

# Reset diario
if st.session_state.diario["fecha"] != datetime.date.today():
    st.session_state.diario = {"fecha": datetime.date.today(), "calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0, "historial": []}

# Configuración API
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("⚠️ Falta API Key en secrets")

# Funciones
def analizar_comida(image):
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    prompt = """Analiza la comida. Responde SOLO JSON: {"nombre_plato": "string", "calorias": int, "proteinas": int, "grasas": int, "carbos": int}"""
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image.tobytes()}])
    return json.loads(response.text.replace("```json", "").replace("```", "").strip())

def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero == "Hombre" else -161)
    factores = {"Sedentario (0 días)": 1.2, "Ligero (1-2 días)": 1.375, "Moderado (3-4 días)": 1.55, "Activo (5-6 días)": 1.725, "Muy Activo (7 días)": 1.9}
    calorias = tmb * factores[actividad]
    if objetivo == "Perder Grasa": calorias -= 400
    elif objetivo == "Ganar Músculo": calorias += 300
    return {"calorias": int(calorias), "proteinas": int(peso*2), "grasas": int(peso*0.9), "carbos": int((calorias - (peso*2*4 + peso*0.9*9))/4)}

# =================================================
# SIDEBAR NAVEGACIÓN
# =================================================
with st.sidebar:
    st.title("🥑 MacroRecio")
    st.write("Tu entrenador nutricional IA.")
    st.markdown("---")
    
    # Navegación con Session State para poder cambiar desde botones
    if 'pagina_actual' not in st.session_state:
        st.session_state.pagina_actual = "Inicio"

    # Widget de selección que actualiza el estado
    seleccion = st.radio(
        "MENÚ PRINCIPAL",
        ["Inicio", "Configurar Perfil", "Escanear Comida", "Mi Progreso Diario"],
        label_visibility="collapsed",
        key="navegacion_radio"
    )
    
    # Sincronizar selección manual
    st.session_state.pagina_actual = seleccion

    st.markdown("---")
    # Botón directo a Avances (Requerimiento)
    if st.button("📊 VER RESUMEN DEL DÍA"):
        st.session_state.pagina_actual = "Mi Progreso Diario"
        st.rerun()

# =================================================
# PÁGINAS
# =================================================

# 1. INICIO (Informativo)
if st.session_state.pagina_actual == "Inicio":
    st.markdown("""
    <div class="st-card">
        <h1>Bienvenido a MacroRecio FIT ⚡</h1>
        <p style="font-size:1.1rem">La herramienta definitiva para transformar tu cuerpo usando Inteligencia Artificial.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image("https://images.unsplash.com/photo-1540497077202-7c8a33801524?q=80&w=1000&auto=format&fit=crop", use_column_width=True)
    with col2:
        st.markdown("""
        <div class="st-card">
            <h3>¿Cómo funciona?</h3>
            <p>1️⃣ Configura tus datos en <b>Perfil</b>.</p>
            <p>2️⃣ Sube una foto de tu plato en <b>Escanear</b>.</p>
            <p>3️⃣ Revisa si cumpliste en <b>Mi Progreso</b>.</p>
            <br>
            <blockquote>"La disciplina es hacer lo que tienes que hacer, incluso cuando no quieres hacerlo."</blockquote>
        </div>
        """, unsafe_allow_html=True)

# 2. PERFIL
elif st.session_state.pagina_actual == "Configurar Perfil":
    st.markdown('<div class="st-card"><h2>👤 Configura tus Datos</h2></div>', unsafe_allow_html=True)
    
    with st.form("perfil"):
        c1, c2 = st.columns(2)
        with c1:
            genero = st.selectbox("Género", ["Hombre", "Mujer"])
            edad = st.number_input("Edad", 15, 90, 25)
            peso = st.number_input("Peso (kg)", 40, 150, 70)
        with c2:
            altura = st.number_input("Altura (cm)", 140, 220, 170)
            actividad = st.selectbox("Nivel de actividad", ["Sedentario (0 días)", "Ligero (1-2 días)", "Moderado (3-4 días)", "Activo (5-6 días)", "Muy Activo (7 días)"])
            objetivo = st.selectbox("Objetivo", ["Perder Grasa", "Mantener Peso", "Ganar Músculo"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn = st.form_submit_button("💾 Guardar y Calcular Metas")
    
    if btn:
        st.session_state.usuario = calcular_macros(genero, edad, peso, altura, actividad, objetivo)
        st.success("¡Perfil guardado! Ahora ve a escanear tu primera comida.")

# 3. ESCÁNER
elif st.session_state.pagina_actual == "Escanear Comida":
    if not st.session_state.usuario:
        st.warning("⚠️ Primero configura tu perfil.")
        st.stop()

    st.markdown('<div class="st-card"><h2>📸 Escáner Nutricional IA</h2></div>', unsafe_allow_html=True)

    # 1. SUBIDA DE FOTO
    uploaded_file = st.file_uploader("Sube una foto de tu comida", type=["jpg", "png"])

    if uploaded_file:
        col_img, col_btn = st.columns([1, 1])
        with col_img:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, caption="Tu plato", width=300)
        
        with col_btn:
            st.markdown("<br><br>", unsafe_allow_html=True)
            # 2. BOTÓN DE ANÁLISIS
            if st.button("🔍 ANALIZAR COMIDA AHORA"):
                with st.spinner("La IA está contando calorías..."):
                    try:
                        data = analizar_comida(image)
                        # Guardar
                        d = st.session_state.diario
                        d["calorias"] += data["calorias"]
                        d["proteinas"] += data["proteinas"]
                        d["grasas"] += data["grasas"]
                        d["carbos"] += data["carbos"]
                        d["historial"].append(data)
                        st.success(f"¡Listo! Se agregaron {data['calorias']} kcal.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    # 3. RESULTADOS RÁPIDOS
    if st.session_state.diario["historial"]:
        st.markdown("### Último plato escaneado:")
        last = st.session_state.diario["historial"][-1]
        st.info(f"🍽️ {last['nombre_plato']} | 🔥 {last['calorias']} kcal")

# 4. AVANCES (NUEVO APARTADO SOLICITADO)
elif st.session_state.pagina_actual == "Mi Progreso Diario":
    if not st.session_state.usuario:
        st.warning("Configura tu perfil para ver el progreso.")
        st.stop()

    u = st.session_state.usuario
    d = st.session_state.diario
    restante = u["calorias"] - d["calorias"]
    porcentaje = min(d["calorias"] / u["calorias"], 1.0)

    st.markdown('<div class="st-card"><h2>📊 Tablero de Control Diario</h2></div>', unsafe_allow_html=True)

    # RESUMEN GRÁFICO
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("Objetivo", f"{u['calorias']} kcal")
    col_kpi2.metric("Consumido", f"{d['calorias']} kcal")
    col_kpi3.metric("Restante", f"{restante} kcal", delta_color="normal" if restante > 0 else "inverse")

    st.progress(porcentaje)
    
    # ANÁLISIS FINAL DEL DÍA
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    st.markdown("### 🏁 Estado Actual")
    
    if porcentaje < 0.85:
        st.warning(f"⚠️ **TE FALTA COMIDA:** Aún necesitas {restante} calorías para llegar a tu meta y construir músculo/mantenerte. ¡Haz una cena fuerte!")
    elif porcentaje >= 0.85 and porcentaje <= 1.1:
        st.success("✅ **¡EXCELENTE TRABAJO!** Estás en el rango perfecto. Has cumplido tus requerimientos nutricionales del día.")
    else:
        st.error(f"🚫 **EXCEDIDO:** Te has pasado por {abs(restante)} calorías. Intenta hacer algo de cardio ligero o ajusta mañana.")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # HISTORIAL DETALLADO
    st.markdown("### 📋 Comidas de Hoy")
    if not d["historial"]:
        st.info("No hay registros hoy.")
    else:
        for item in reversed(d["historial"]):
            st.markdown(f"""
            <div class="st-mini-card" style="background:#1e293b; padding:15px; border-radius:10px; margin-bottom:10px; border-left:4px solid #10B981;">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:white; font-weight:bold;">{item['nombre_plato']}</span>
                    <span style="color:#10B981; font-weight:bold;">{item['calorias']} kcal</span>
                </div>
                <div style="font-size:0.9rem; color:#94a3b8;">
                    Prot: {item['proteinas']}g | Gras: {item['grasas']}g | Carb: {item['carbos']}g
                </div>
            </div>
            """, unsafe_allow_html=True)
