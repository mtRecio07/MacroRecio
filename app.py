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
# ESTILOS MODERNOS Y UNIFICADOS (CSS)
# =================================================
st.markdown("""
<style>
    /* --- Tipografía --- */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* --- Fondo General --- */
    .stApp {
        background: #0f172a; /* Fondo oscuro sólido y limpio */
        color: #F1F5F9;
    }

    /* -------------------------------------------------- */
    /* --- ESTILOS EXCLUSIVOS PARA LA BARRA LATERAL --- */
    /* -------------------------------------------------- */
    
    /* Color de fondo de la barra lateral */
    [data-testid="stSidebar"] {
        background-color: #0b1120;
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* --- BOTONES DE LA BARRA LATERAL (UNIFICADOS) --- */
    /* Esto aplica A TODOS los botones dentro del sidebar */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        background-color: rgba(30, 41, 59, 0.5) !important; /* Fondo oscuro transparente */
        color: #F1F5F9 !important; /* Texto claro */
        border: 1px solid rgba(255,255,255,0.1) !important; /* Borde sutil */
        border-radius: 12px !important; /* Esquinas redondeadas */
        padding: 12px 20px !important;
        font-weight: 600 !important;
        text-align: left !important; /* Texto alineado a la izquierda para parecer menú */
        transition: all 0.2s ease-in-out !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
        margin-bottom: 8px !important; /* Espacio entre botones */
    }

    /* Efecto Hover (al pasar el mouse) para TODOS los botones del sidebar */
    [data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(30, 41, 59, 1) !important; /* Fondo más oscuro */
        border-color: #10B981 !important; /* Borde verde brillante */
        color: white !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important; /* Sutil resplandor verde */
        transform: translateY(-2px) !important; /* Pequeño efecto de elevación */
    }

    /* Estilo para la tarjeta de "Objetivo" para que coincida con los botones */
    .goal-card {
        background-color: rgba(30, 41, 59, 0.5);
        color: #F1F5F9;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 12px 20px;
        font-weight: 600;
        text-align: center;
        margin-bottom: 16px;
    }
    
    /* Títulos y textos en el sidebar */
    [data-testid="stSidebar"] h1 { color: #10B981; font-weight: 800; }
    [data-testid="stSidebar"] p { color: #94a3b8; }
    [data-testid="stSidebar"] hr { margin: 1.5em 0; border-color: rgba(255,255,255,0.1); }


    /* -------------------------------------------------- */
    /* --- ESTILOS PARA EL ÁREA PRINCIPAL (MAIN) --- */
    /* -------------------------------------------------- */

    /* --- CARDS (Tarjetas de contenido) --- */
    .st-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 20px;
    }
    
    /* --- BOTONES PRINCIPALES (Formularios, Acciones) --- */
    /* Estos mantienen el estilo de "botón relleno" para destacar */
    .main .stButton > button {
        width: 100%;
        background-color: #10B981;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px;
        font-weight: 600;
        transition: 0.2s;
    }
    .main .stButton > button:hover {
        background-color: #059669;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }

    /* --- TEXTOS GENERALES --- */
    h1, h2, h3 { color: white; font-weight: 800; }
    p { color: #94a3b8; font-size: 1rem; line-height: 1.5; }
    
    /* --- BARRA DE PROGRESO --- */
    .stProgress > div > div > div > div { background-color: #10B981; }
    .stProgress > div > div { background-color: rgba(255,255,255,0.1) !important; }
    
    /* --- IMÁGENES --- */
    img { border-radius: 12px; }
    
    /* --- MÉTICAS --- */
    [data-testid="stMetricLabel"] { color: #94a3b8; }
    [data-testid="stMetricValue"] { color: #F1F5F9; }

</style>
""", unsafe_allow_html=True)

# =================================================
# LÓGICA (BACKEND)
# =================================================
# Inicializar Session State
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "diario" not in st.session_state:
    st.session_state.diario = {"fecha": datetime.date.today(), "calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0, "historial": []}

# Reset diario automático
if st.session_state.diario["fecha"] != datetime.date.today():
    st.session_state.diario = {"fecha": datetime.date.today(), "calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0, "historial": []}

# Configuración API
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except Exception:
    st.error("⚠️ Error: Falta la API Key en los secrets de Streamlit.")

# Funciones
def analizar_comida(image):
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    prompt = """Analiza la comida de la imagen. Responde SOLO con un objeto JSON válido: {"nombre_plato": "string", "calorias": int, "proteinas": int, "grasas": int, "carbos": int}"""
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image.tobytes()}])
    texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(texto_limpio)

def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero == "Hombre" else -161)
    # Factores de actividad simplificados para el nombre del selectbox
    factores = {
        "Sedentario (0 días)": 1.2,
        "Ligero (1-2 días)": 1.375,
        "Moderado (3-4 días)": 1.55,
        "Activo (5-6 días)": 1.725,
        "Muy Activo (7 días)": 1.9
    }
    calorias = tmb * factores[actividad]
    if objetivo == "Perder Grasa": calorias -= 400
    elif objetivo == "Ganar Músculo": calorias += 300
    
    # Distribución estándar de macros
    proteinas = peso * 2 # 2g por kg de peso
    grasas = peso * 0.9 # 0.9g por kg de peso
    carbos = (calorias - (proteinas*4 + grasas*9)) / 4
    
    return {
        "calorias": int(calorias),
        "proteinas": int(proteinas),
        "grasas": int(grasas),
        "carbos": int(carbos)
    }

# =================================================
# NUEVA BARRA LATERAL (DISEÑO UNIFICADO)
# =================================================
with st.sidebar:
    st.title("🥑 MacroRecio")
    st.write("Tu entrenador nutricional IA.")
    st.markdown("---")
    
    # Inicializar la página actual si no existe
    if 'pagina_actual' not in st.session_state:
        st.session_state.pagina_actual = "Inicio"

    # --- MENÚ DE NAVEGACIÓN (BOTONES) ---
    # Usamos st.button estándar, el CSS se encarga de que se vean increíbles y uniformes.
    
    if st.button("🏠  Inicio", use_container_width=True):
        st.session_state.pagina_actual = "Inicio"
        st.rerun()
    
    if st.button("👤  Configurar Perfil", use_container_width=True):
        st.session_state.pagina_actual = "Configurar Perfil"
        st.rerun()
        
    if st.button("📸  Escanear Comida", use_container_width=True):
        st.session_state.pagina_actual = "Escanear Comida"
        st.rerun()

    st.markdown("---")
    
    # --- MOSTRAR OBJETIVO ---
    if st.session_state.usuario:
        # Usamos un div con la clase 'goal-card' para que coincida con el estilo de los botones
        st.markdown(f"""
        <div class="goal-card">
            🎯 Objetivo Diario: <span style="color: #10B981;">{st.session_state.usuario.get('calorias')} kcal</span>
        </div>
        """, unsafe_allow_html=True)
    else:
         st.info("💡 Configura tu perfil para ver tu meta aquí.")

    # --- BOTÓN DE ACCIÓN FINAL ---
    # Este botón es igual a los de navegación, cumpliendo tu requisito de uniformidad.
    if st.button("📊  VER RESUMEN DEL DÍA", use_container_width=True):
        st.session_state.pagina_actual = "Mi Progreso Diario"
        st.rerun()

# =================================================
# PÁGINAS DE LA APLICACIÓN
# =================================================

# 1. INICIO (Informativo y Motivacional)
if st.session_state.pagina_actual == "Inicio":
    st.markdown("""
    <div class="st-card">
        <h1 style="font-size: 2.5rem;">Bienvenido a MacroRecio FIT ⚡</h1>
        <p style="font-size:1.2rem; margin-top: 10px;">La herramienta definitiva para transformar tu cuerpo usando el poder de la Inteligencia Artificial.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1])
    with col1:
        # Imagen de alta calidad y motivadora
        st.image("https://images.unsplash.com/photo-1517836357463-d25dfeac3438?q=80&w=1000&auto=format&fit=crop", use_column_width=True)
    with col2:
        st.markdown("""
        <div class="st-card" style="height: 100%; display: flex; flex-direction: column; justify-content: center;">
            <h3>🚀 ¿Cómo funciona?</h3>
            <ol style="color: #94a3b8; font-size: 1.1rem; line-height: 1.8; padding-left: 20px;">
                <li>Configura tus metas en <b>Perfil</b>.</li>
                <li>Sube una foto de tu plato en <b>Escanear</b>.</li>
                <li>La IA calcula los macros al instante.</li>
                <li>Revisa tu avance en <b>Mi Progreso</b>.</li>
            </ol>
            <br>
            <div style="border-left: 4px solid #10B981; padding-left: 15px; font-style: italic; color: #F1F5F9;">
                "La disciplina es hacer lo que tienes que hacer, incluso cuando no quieres hacerlo."
            </div>
        </div>
        """, unsafe_allow_html=True)

# 2. PERFIL
elif st.session_state.pagina_actual == "Configurar Perfil":
    st.markdown('<div class="st-card"><h2>👤 Configura tus Datos y Metas</h2></div>', unsafe_allow_html=True)
    
    with st.form("perfil_form"):
        st.write("Ingresa tus datos para crear un plan nutricional personalizado.")
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
        # Este botón usa el estilo de botón principal (relleno verde)
        btn_calcular = st.form_submit_button("💾 Guardar y Calcular Metas")
    
    if btn_calcular:
        st.session_state.usuario = calcular_macros(genero, edad, peso, altura, actividad, objetivo)
        st.success("¡Perfil guardado con éxito! Ahora puedes empezar a escanear tus comidas.")
        st.balloons()

# 3. ESCÁNER
elif st.session_state.pagina_actual == "Escanear Comida":
    if not st.session_state.usuario:
        st.warning("⚠️ Por favor, configura tu perfil primero para poder calcular tus metas.")
        st.stop()

    st.markdown('<div class="st-card"><h2>📸 Escáner Nutricional con IA</h2></div>', unsafe_allow_html=True)

    col_upload, col_preview = st.columns([1, 1])
    
    with col_upload:
        st.markdown("### 1. Sube tu plato")
        uploaded_file = st.file_uploader("Arrastra una imagen o haz clic", type=["jpg", "png", "jpeg"])
        
    with col_preview:
        st.markdown("### 2. Vista previa y Análisis")
        if uploaded_file:
            image = Image.open(uploaded_file).convert("RGB")
            st.image(image, caption="Tu comida", use_column_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            # Botón de acción principal
            if st.button("🔍 ANALIZAR COMIDA AHORA"):
                with st.spinner("🤖 La IA está analizando los nutrientes..."):
                    try:
                        data = analizar_comida(image)
                        
                        # Actualizar el diario
                        d = st.session_state.diario
                        d["calorias"] += data["calorias"]
                        d["proteinas"] += data["proteinas"]
                        d["grasas"] += data["grasas"]
                        d["carbos"] += data["carbos"]
                        d["historial"].append(data)
                        
                        st.success(f"¡Éxito! Se han agregado **{data['calorias']} kcal** de '{data['nombre_plato']}' a tu diario.")
                    except Exception as e:
                        st.error(f"Ocurrió un error al analizar la imagen: {e}. Por favor, intenta con otra foto.")
        else:
            st.info("👈 Esperando imagen para analizar...")

    # Mostrar el último plato escaneado si existe
    if st.session_state.diario["historial"]:
        st.markdown("---")
        st.markdown("### Último registro:")
        last = st.session_state.diario["historial"][-1]
        st.write(f"🍽️ **{last['nombre_plato']}** | 🔥 {last['calorias']} kcal | P: {last['proteinas']}g | G: {last['grasas']}g | C: {last['carbos']}g")

# 4. AVANCES (Tu nuevo apartado solicitado)
elif st.session_state.pagina_actual == "Mi Progreso Diario":
    if not st.session_state.usuario:
        st.warning("Configura tu perfil para ver el tablero de progreso.")
        st.stop()

    u = st.session_state.usuario
    d = st.session_state.diario
    
    # Cálculos
    calorias_restantes = u["calorias"] - d["calorias"]
    porcentaje_progreso = min(d["calorias"] / u["calorias"], 1.0) if u["calorias"] > 0 else 0

    st.markdown('<div class="st-card"><h2>📊 Tablero de Control Diario</h2></div>', unsafe_allow_html=True)

    # --- KPIs (Indicadores Clave) ---
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("🎯 Objetivo Diario", f"{u['calorias']} kcal")
    col_kpi2.metric("🍔 Consumido Hoy", f"{d['calorias']} kcal")
    # El color del delta cambia si te pasaste
    col_kpi3.metric("⚡ Restante", f"{calorias_restantes} kcal", delta=calorias_restantes, delta_color="normal" if calorias_restantes >= 0 else "inverse")

    # Barra de progreso
    st.write(f"Progreso: {int(porcentaje_progreso * 100)}%")
    st.progress(porcentaje_progreso)
    
    # --- ANÁLISIS DEL ESTADO ACTUAL ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    st.markdown("### 🏁 Estado de tu Meta")
    
    # Lógica para los mensajes de estado
    if porcentaje_progreso < 0.85:
        st.warning(f"⚠️ **TE FALTA COMIDA:** Aún necesitas consumir unas **{calorias_restantes} calorías** para llegar a tu meta óptima. ¡Asegúrate de hacer una buena cena!")
    elif porcentaje_progreso >= 0.85 and porcentaje_progreso <= 1.05:
        st.success("✅ **¡EXCELENTE TRABAJO!** Estás en el rango perfecto. Has cumplido tus requerimientos nutricionales del día de forma balanceada.")
    else:
        # Se excedió
        exceso = abs(calorias_restantes)
        st.error(f"🚫 **LÍMITE EXCEDIDO:** Te has pasado por **{exceso} calorías**. No te preocupes, intenta compensar mañana con un poco más de actividad o ajustando tus comidas.")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # --- HISTORIAL DETALLADO CON MINI-CARDS ---
    st.markdown("### 📋 Historial de Comidas de Hoy")
    if not d["historial"]:
        st.info("Aún no has registrado ninguna comida hoy.")
    else:
        # Mostrar el historial en orden inverso (lo más reciente primero)
        for item in reversed(d["historial"]):
            st.markdown(f"""
            <div style="
                background-color: #1e293b;
                padding: 16px;
                border-radius: 12px;
                margin-bottom: 12px;
                border-left: 4px solid #10B981;
                display: flex;
                justify-content: space-between;
                align-items: center;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            ">
                <div>
                    <div style="color: white; font-weight: 700; font-size: 1.1rem;">{item['nombre_plato']}</div>
                    <div style="font-size: 0.9rem; color: #94a3b8; margin-top: 4px;">
                        🥩 {item['proteinas']}g Pro | 🥑 {item['grasas']}g Gra | 🍞 {item['carbos']}g Car
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="color: #10B981; font-weight: 800; font-size: 1.3rem;">{item['calorias']}</div>
                    <div style="color: #64748b; font-size: 0.8rem;">kcal</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
