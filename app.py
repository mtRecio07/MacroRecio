import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
from streamlit_option_menu import option_menu  # Librería para el menú pro

# =================================================
# CONFIGURACIÓN GENERAL
# =================================================
st.set_page_config(
    page_title="MacroFit Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================================================
# ESTILOS PREMIUM (CSS AVANZADO)
# =================================================
st.markdown("""
<style>
    /* Tipografía Importada */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Fondo Principal - Gradiente Profundo */
    .stApp {
        background: radial-gradient(circle at top left, #1e293b, #0f172a);
        color: #f8fafc;
    }

    /* --- CARDS CON EFECTO GLASSMORPHISM --- */
    .st-card {
        background: rgba(30, 41, 59, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 28px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
        margin-bottom: 24px;
        transition: transform 0.2s ease;
    }
    
    .st-card:hover {
        border-color: rgba(16, 185, 129, 0.3);
    }

    /* --- MINI CARDS DE HISTORIAL --- */
    .st-mini-card {
        background: rgba(15, 23, 42, 0.6);
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
        border-left: 5px solid #10B981;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: background 0.2s;
    }
    .st-mini-card:hover {
        background: rgba(15, 23, 42, 0.9);
    }

    /* --- TEXTOS Y TÍTULOS --- */
    h1 { font-weight: 800; letter-spacing: -1px; background: -webkit-linear-gradient(#fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    h2 { font-weight: 700; color: #f1f5f9; border-bottom: 2px solid #10B981; padding-bottom: 8px; display: inline-block; margin-bottom: 20px;}
    h3 { font-weight: 600; color: #e2e8f0; }
    p, label, .stMarkdown { color: #94a3b8; }

    /* --- MÉTRICAS PERSONALIZADAS --- */
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: #64748b; font-weight: 700; }
    div[data-testid="stMetricValue"] { font-size: 2rem; color: #10B981; font-weight: 800; text-shadow: 0 0 20px rgba(16,185,129,0.3); }

    /* --- BOTONES PRO --- */
    .stButton > button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        border: none;
        padding: 14px 28px;
        font-weight: 700;
        border-radius: 14px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 14px 0 rgba(16, 185, 129, 0.39);
        letter-spacing: 0.5px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.23);
    }

    /* --- INPUTS --- */
    div[data-baseweb="input"] {
        background-color: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
    }
    div[data-baseweb="select"] > div {
        background-color: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
    }

    /* --- BARRA DE PROGRESO --- */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #10B981, #34d399);
        border-radius: 10px;
    }
    .stProgress > div > div {
        background-color: rgba(255,255,255,0.05) !important;
        border-radius: 10px;
        height: 14px !important;
    }

    /* --- SIDEBAR --- */
    section[data-testid="stSidebar"] {
        background-color: #0b1120;
        border-right: 1px solid #1e293b;
    }
    
    /* Corrección imágenes */
    img { border-radius: 16px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }
    
</style>
""", unsafe_allow_html=True)

# =================================================
# LÓGICA DEL NEGOCIO (Sin cambios, solo Backend)
# =================================================
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if "diario" not in st.session_state:
    st.session_state.diario = {
        "fecha": datetime.date.today(),
        "calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0, "historial": []
    }

if st.session_state.diario["fecha"] != datetime.date.today():
    st.session_state.diario = {"fecha": datetime.date.today(), "calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0, "historial": []}

try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    st.error("⚠️ Error: API Key no configurada.")

def analizar_comida(image):
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    prompt = """Analiza la comida. Responde SOLO JSON válido: {"nombre_plato": "string", "calorias": int, "proteinas": int, "grasas": int, "carbos": int}"""
    response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image.tobytes()}])
    return json.loads(response.text.replace("```json", "").replace("```", "").strip())

def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero == "Hombre" else -161)
    factores = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Activo": 1.725, "Muy Activo": 1.9}
    calorias = tmb * factores[actividad.split()[0]]
    if objetivo == "Perder Grasa": calorias -= 400
    elif objetivo == "Ganar Músculo": calorias += 300
    return {"calorias": int(calorias), "proteinas": int(peso*2), "grasas": int(peso*0.9), "carbos": int((calorias - (peso*2*4 + peso*0.9*9))/4)}

# =================================================
# SIDEBAR PROFESIONAL
# =================================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3063/3063822.png", width=60) # Logo genérico fit
    st.markdown("<h1 style='font-size: 1.5rem; margin-top: -10px;'>MacroFit Pro</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.8rem; opacity: 0.7;'>V 2.0.1 Premium</p>", unsafe_allow_html=True)
    
    # MENÚ DE NAVEGACIÓN PRO (Requiere streamlit-option-menu)
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Perfil", "Scanner"],
        icons=["grid-fill", "person-circle", "camera-fill"], # Iconos de Bootstrap
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#10B981", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "#1e293b"},
            "nav-link-selected": {"background-color": "#10B981", "font-weight": "600"},
        }
    )
    
    st.markdown("---")
    
    # WIDGET DE RESUMEN RÁPIDO EN SIDEBAR
    if st.session_state.usuario:
        u = st.session_state.usuario
        d = st.session_state.diario
        restantes = u['calorias'] - d['calorias']
        
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; text-align: center;">
            <span style="font-size: 0.8rem; color: #94a3b8;">CALORÍAS RESTANTES</span>
            <h2 style="margin: 0; color: {'#ef4444' if restantes < 0 else '#10B981'}; border: none;">{restantes}</h2>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Configura tu perfil para ver tus métricas aquí.")

# =================================================
# PANTALLAS
# =================================================

# --- DASHBOARD (HOME) ---
if selected == "Dashboard":
    # Header Principal
    st.markdown("""
    <div class="st-card">
        <h1 style="margin-bottom: 10px;">👋 Bienvenido de nuevo.</h1>
        <p style="font-size: 1.1rem; max-width: 600px;">
            Tu centro de comando nutricional. Aquí tienes el resumen de tu progreso hoy. 
            Mantén la constancia para ver resultados reales.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.usuario:
        st.warning("⚠️ Tu perfil aún no está configurado. Ve a la pestaña 'Perfil' para empezar.")
        st.stop()

    u = st.session_state.usuario
    d = st.session_state.diario
    progreso = d["calorias"] / u["calorias"] if u["calorias"] > 0 else 0

    # Panel de Métricas Principal
    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    st.markdown("<h2>🔥 Resumen del Día</h2>", unsafe_allow_html=True)
    
    # Barra de progreso grande
    st.markdown(f"<div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span>Consumido: <b>{d['calorias']}</b></span><span>Meta: <b>{u['calorias']}</b></span></div>", unsafe_allow_html=True)
    st.progress(min(progreso, 1.0))
    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Proteínas", f"{d['proteinas']}g", f"/ {u['proteinas']}g")
    c2.metric("Carbohidratos", f"{d['carbos']}g", f"/ {u['carbos']}g")
    c3.metric("Grasas", f"{d['grasas']}g", f"/ {u['grasas']}g")
    c4.metric("Estado", "En Rango" if progreso < 1.0 else "Excedido", delta_color="normal")
    st.markdown('</div>', unsafe_allow_html=True)

    # Gráficos rápidos o info extra
    c_left, c_right = st.columns([1,1])
    with c_left:
        st.markdown('<div class="st-card" style="height:200px; display:flex; align-items:center; justify-content:center; flex-direction:column;"><h3>💧 Hidratación</h3><h1 style="color:#3b82f6; border:none;">0.5 L</h1><p>Meta: 2.5 L</p></div>', unsafe_allow_html=True)
    with c_right:
        st.markdown('<div class="st-card" style="height:200px; display:flex; align-items:center; justify-content:center; flex-direction:column;"><h3>🔥 Racha</h3><h1 style="color:#f59e0b; border:none;">3 Días</h1><p>¡Sigue así!</p></div>', unsafe_allow_html=True)


# --- PERFIL ---
elif selected == "Perfil":
    st.markdown('<div class="st-card">', unsafe_allow_html=True)
    st.markdown("<h2>⚙️ Configuración Personal</h2>", unsafe_allow_html=True)
    st.markdown("<p>La precisión es clave. Ingresa tus datos reales para que la IA calcule tu plan perfecto.</p>", unsafe_allow_html=True)
    
    with st.form("form_perfil"):
        c1, c2, c3 = st.columns(3)
        with c1:
            genero = st.selectbox("Género", ["Hombre", "Mujer"])
            edad = st.number_input("Edad", 15, 90, 25)
        with c2:
            peso = st.number_input("Peso (kg)", 40, 150, 70)
            altura = st.number_input("Altura (cm)", 140, 220, 170)
        with c3:
            objetivo = st.selectbox("Meta", ["Perder Grasa", "Mantener Peso", "Ganar Músculo"])
            actividad = st.selectbox("Actividad", ["Sedentario (0 días)", "Ligero (1-2 días)", "Moderado (3-4 días)", "Activo (5-6 días)", "Muy Activo (7 días)"])
        
        st.markdown("<br>", unsafe_allow_html=True)
        btn = st.form_submit_button("💾 Guardar y Recalcular")
    
    if btn:
        st.session_state.usuario = calcular_macros(genero, edad, peso, altura, actividad, objetivo)
        st.success("¡Perfil actualizado con éxito!")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.usuario:
        u = st.session_state.usuario
        st.markdown(f"""
        <div class="st-card" style="border-left: 5px solid #10B981;">
            <h3>🎯 Tu Plan Personalizado</h3>
            <div style="display: flex; justify-content: space-around; margin-top: 20px;">
                <div style="text-align:center;"><h2>{u['calorias']}</h2><p>KCAL</p></div>
                <div style="text-align:center;"><h2>{u['proteinas']}g</h2><p>PROT</p></div>
                <div style="text-align:center;"><h2>{u['carbos']}g</h2><p>CARB</p></div>
                <div style="text-align:center;"><h2>{u['grasas']}g</h2><p>GRAS</p></div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# --- SCANNER ---
elif selected == "Scanner":
    if not st.session_state.usuario:
        st.warning("Primero configura tu perfil.")
        st.stop()

    col_izq, col_der = st.columns([1, 1.5])

    with col_izq:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.markdown("<h3>📸 Escáner IA</h3>", unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Sube foto del plato", ["jpg", "png"], label_visibility="collapsed")
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, use_column_width=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🔍 Analizar Nutrientes"):
                with st.spinner("🧠 IA procesando alimentos..."):
                    try:
                        data = analizar_comida(image)
                        d = st.session_state.diario
                        d["calorias"] += data["calorias"]
                        d["proteinas"] += data["proteinas"]
                        d["grasas"] += data["grasas"]
                        d["carbos"] += data["carbos"]
                        d["historial"].append(data)
                        st.toast(f"✅ Registrado: {data['nombre_plato']}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
        else:
            st.markdown("""
            <div style="text-align: center; padding: 40px; border: 2px dashed #334155; border-radius: 12px;">
                <p>Arrastra una foto o haz clic para subir</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_der:
        st.markdown('<div class="st-card">', unsafe_allow_html=True)
        st.markdown("<h3>🍽️ Registro de Hoy</h3>", unsafe_allow_html=True)
        
        historial = st.session_state.diario["historial"]
        
        if not historial:
            st.info("Aún no hay comidas registradas hoy. ¡Sube tu primera foto!")
        else:
            for item in reversed(historial):
                st.markdown(f"""
                <div class="st-mini-card">
                    <div>
                        <div style="font-weight: 700; color: #fff; font-size: 1.1rem;">{item['nombre_plato']}</div>
                        <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">
                            🥩 {item['proteinas']}g  •  🍞 {item['carbos']}g  •  🥑 {item['grasas']}g
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.4rem; color: #10B981; font-weight: 800;">{item['calorias']}</div>
                        <div style="font-size: 0.7rem; color: #64748b;">KCAL</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
