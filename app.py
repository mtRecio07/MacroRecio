import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
import io
import time
from datetime import date, timedelta 
import pandas as pd
from sqlalchemy import text
from streamlit_option_menu import option_menu 

# =================================================
# CONFIGURACIÓN DE PÁGINA
# =================================================
st.set_page_config(
    page_title="MacroRecioIA",
    layout="wide"
)

# =================================================
# ESTILOS CSS "LIQUID GLASS" PREMIUM + OVERLAY CARGA
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif; 
}

/* Fondo General con Gradiente Profundo */
.stApp { 
    background: linear-gradient(135deg, #0f172a, #020617); 
    color: #f8fafc; 
}

/* --- BARRA LATERAL LIQUID GLASS --- */
[data-testid="stSidebar"] {
    background-color: rgba(15, 23, 42, 0.65); /* Semi-transparente */
    backdrop-filter: blur(16px); /* Efecto vidrio esmerilado */
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Inputs y Textos */
.stTextInput > div > div > input { 
    color: #ffffff; 
    background-color: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
}
.stSelectbox > div > div {
    background-color: rgba(255, 255, 255, 0.05);
    color: white;
}

/* Tarjetas (Cards) */
.card { 
    background: rgba(30, 41, 59, 0.6); 
    border-radius: 20px; 
    padding: 28px; 
    margin-bottom: 24px; 
    border: 1px solid rgba(255, 255, 255, 0.05);
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    backdrop-filter: blur(10px);
}

/* Métricas */
[data-testid="stMetric"] { 
    background: rgba(255, 255, 255, 0.03); 
    padding: 18px; 
    border-radius: 16px; 
    text-align: center; 
    border: 1px solid rgba(255, 255, 255, 0.05);
}

/* Barra de Progreso */
.stProgress > div > div > div > div { 
    background: linear-gradient(90deg, #10B981, #34D399); 
}

/* Botones Premium */
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #10B981, #059669);
    color: white;
    border-radius: 14px;
    padding: 14px;
    font-weight: 700;
    border: none;
    margin-top: 10px;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}
.stButton > button:hover {
    background: linear-gradient(135deg, #34D399, #10B981);
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(16, 185, 129, 0.4);
}

/* --- OVERLAY DE CARGA --- */
#loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.95); /* Fondo muy oscuro */
    z-index: 999999;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(10px);
}

.loading-content {
    text-align: center;
    animation: fadeIn 0.8s ease-in-out;
}

/* Estilo para el contenedor del video */
.video-container {
    width: 340px;
    height: auto;
    border-radius: 20px;
    overflow: hidden; /* Para que el video respete el borde redondeado */
    box-shadow: 0 0 60px rgba(16, 185, 129, 0.5); /* Glow verde intenso */
    border: 3px solid #10B981;
    margin-bottom: 25px;
    background-color: #000; /* Fondo negro por si el video no carga al instante */
}

.loading-video {
    width: 100%;
    height: auto;
    display: block;
}

.loading-text {
    color: #10B981;
    font-size: 24px;
    font-weight: 800;
    margin-top: 20px;
    letter-spacing: 2px;
    text-transform: uppercase;
    text-shadow: 0 2px 20px rgba(16, 185, 129, 0.6);
    font-family: 'Inter', sans-serif;
}

@keyframes fadeIn {
    from { opacity: 0; transform: scale(0.9); }
    to { opacity: 1; transform: scale(1); }
}

img { border-radius: 18px; }
footer {visibility: hidden;}
.disclaimer { font-size: 12px; color: #94a3b8; text-align: center; margin-top: 50px; opacity: 0.7; }
#MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# =================================================
# CONEXIÓN BASE DE DATOS
# =================================================
def get_db_connection():
    return st.connection("supabase", type="sql")

def init_db():
    conn = get_db_connection()
    with conn.session as s:
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS Usuarios (
                ID_Usuario SERIAL PRIMARY KEY,
                Username TEXT UNIQUE,
                Password TEXT,
                Genero TEXT,
                Edad INTEGER,
                Peso REAL,
                Altura REAL,
                Actividad TEXT,
                Objetivo TEXT,
                Meta_Calorias INTEGER,
                Meta_Proteinas INTEGER,
                Meta_Grasas INTEGER,
                Meta_Carbos INTEGER
            );
        """))
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS Comidas (
                ID_Comida SERIAL PRIMARY KEY,
                ID_Usuario INTEGER,
                Nombre_Plato TEXT,
                Calorias INTEGER,
                Proteinas INTEGER,
                Grasas INTEGER,
                Carbos INTEGER,
                Fecha_Consumo DATE
            );
        """))
        s.commit()

try:
    init_db()
except:
    pass

# =================================================
# FUNCIONES DE LOGIN Y REGISTRO
# =================================================
def registrar_usuario(username, password):
    conn = get_db_connection()
    try:
        df = conn.query("SELECT COUNT(*) as count FROM Usuarios WHERE Username = :user", params={"user": username}, ttl=0)
        if df.iloc[0]["count"] > 0:
            return False, "El usuario ya existe."
    except:
        pass
    
    with conn.session as s:
        s.execute(text("INSERT INTO Usuarios (Username, Password) VALUES (:user, :pass)"), {"user": username, "pass": password})
        s.commit()
    return True, "Registro exitoso. Ahora inicia sesión."

def login_usuario(username, password):
    conn = get_db_connection()
    query = "SELECT * FROM Usuarios WHERE Username = :user AND Password = :pass"
    df = conn.query(query, params={"user": username, "pass": password}, ttl=0)
    
    if not df.empty:
        user_data = df.iloc[0].to_dict()
        return {k.lower(): v for k, v in user_data.items()}
    return None

# =================================================
# GESTIÓN DE SESIÓN
# =================================================
if 'login_status' not in st.session_state:
    st.session_state['login_status'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# =================================================
# LOGIN (SI NO ESTÁ LOGUEADO)
# =================================================
if not st.session_state['login_status']:
    st.markdown("<h1 style='text-align: center;'>MacroRecioIA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Tu entrenador inteligente.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
        with tab1:
            with st.form("login_form"):
                user = st.text_input("Usuario")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Entrar"):
                    usuario_encontrado = login_usuario(user, password)
                    if usuario_encontrado:
                        st.session_state['login_status'] = True
                        st.session_state['user_info'] = usuario_encontrado
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos.")
        with tab2:
            with st.form("register_form"):
                new_user = st.text_input("Nuevo Usuario")
                new_pass = st.text_input("Nueva Contraseña", type="password")
                if st.form_submit_button("Crear Cuenta"):
                    if new_user and new_pass:
                        ok, msg = registrar_usuario(new_user, new_pass)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)
                    else:
                        st.warning("Completa todos los campos.")
    st.stop()

# =================================================
# APP PRINCIPAL (LOGUEADO)
# =================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    pass

# Funciones de Datos
def guardar_perfil_usuario_actual(datos):
    conn = get_db_connection()
    uid = st.session_state['user_info']['id_usuario']
    with conn.session as s:
        query = text("""
            UPDATE Usuarios SET 
                Genero=:genero, Edad=:edad, Peso=:peso, Altura=:altura, 
                Actividad=:actividad, Objetivo=:objetivo, 
                Meta_Calorias=:calorias, Meta_Proteinas=:proteinas, 
                Meta_Grasas=:grasas, Meta_Carbos=:carbos
            WHERE ID_Usuario=:uid
        """)
        s.execute(query, {
            'uid': uid,
            'genero': datos['genero'], 'edad': datos['edad'], 'peso': datos['peso'], 
            'altura': datos['altura'], 'actividad': datos['actividad'], 'objetivo': datos['objetivo'],
            'calorias': datos['calorias'], 'proteinas': datos['proteinas'], 
            'grasas': datos['grasas'], 'carbos': datos['carbos']
        })
        s.commit()
    st.session_state['user_info'].update({
        'meta_calorias': datos['calorias'], 'meta_proteinas': datos['proteinas'],
        'meta_grasas': datos['grasas'], 'meta_carbos': datos['carbos'],
        'genero': datos['genero'], 'edad': datos['edad'], 'peso': datos['peso'],
        'altura': datos['altura'], 'actividad': datos['actividad'], 'objetivo': datos['objetivo']
    })

def guardar_comida_usuario_actual(plato):
    conn = get_db_connection()
    uid = st.session_state['user_info']['id_usuario']
    with conn.session as s:
        s.execute(text("""
            INSERT INTO Comidas 
            (ID_Usuario, Nombre_Plato, Calorias, Proteinas, Grasas, Carbos, Fecha_Consumo)
            VALUES (:uid, :nombre, :calorias, :proteinas, :grasas, :carbos, :fecha)
        """), {
            'uid': uid, 'nombre': plato['nombre_plato'], 'calorias': plato['calorias'], 
            'proteinas': plato['proteinas'], 'grasas': plato['grasas'], 'carbos': plato['carbos'],
            'fecha': date.today()
        })
        s.commit()

def leer_progreso_hoy_usuario_actual():
    conn = get_db_connection()
    uid = st.session_state['user_info']['id_usuario']
    hoy = date.today()
    query = "SELECT Nombre_Plato, Calorias, Proteinas, Grasas, Carbos FROM Comidas WHERE Fecha_Consumo = :fecha AND ID_Usuario = :uid"
    df = conn.query(query, params={"fecha": hoy, "uid": uid}, ttl=0)
    
    historial = []
    totales = {"calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0}
    for index, row in df.iterrows():
        nombre = row.get("nombre_plato") or row.get("Nombre_Plato")
        cal = row.get("calorias") or row.get("Calorias") or 0
        prot = row.get("proteinas") or row.get("Proteinas") or 0
        fat = row.get("grasas") or row.get("Grasas") or 0
        carb = row.get("carbos") or row.get("Carbos") or 0
        
        historial.append({
            "nombre_plato": nombre, 
            "calorias": cal, 
            "proteinas": prot, 
            "grasas": fat, 
            "carbos": carb
        })
        totales["calorias"] += cal
        totales["proteinas"] += prot
        totales["grasas"] += fat
        totales["carbos"] += carb
    return totales, historial

def obtener_historial_grafico():
    conn = get_db_connection()
    uid = st.session_state['user_info']['id_usuario']
    query = "SELECT Fecha_Consumo, SUM(Calorias) as Total_Calorias FROM Comidas WHERE ID_Usuario=:uid GROUP BY Fecha_Consumo ORDER BY Fecha_Consumo"
    return conn.query(query, params={"uid": uid}, ttl=0)

def obtener_todo_csv():
    conn = get_db_connection()
    uid = st.session_state['user_info']['id_usuario']
    query = "SELECT Fecha_Consumo, Nombre_Plato, Calorias, Proteinas, Grasas, Carbos FROM Comidas WHERE ID_Usuario=:uid ORDER BY Fecha_Consumo DESC"
    return conn.query(query, params={"uid": uid}, ttl=0)

def calcular_racha_usuario(uid):
    conn = get_db_connection()
    try:
        query = "SELECT DISTINCT Fecha_Consumo FROM Comidas WHERE ID_Usuario = :uid ORDER BY Fecha_Consumo DESC"
        df = conn.query(query, params={"uid": uid}, ttl=0)
        if df.empty: return 0
        
        fechas = pd.to_datetime(df.iloc[:, 0]).dt.date.tolist()
        hoy = date.today()
        racha = 0
        check = hoy
        if check not in fechas:
            check = hoy - timedelta(days=1)
            if check not in fechas: return 0
        
        while check in fechas:
            racha += 1
            check -= timedelta(days=1)
        return racha
    except: return 0

def analizar_comida_ia(image):
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    image_bytes = buffer.getvalue()
    prompt = """
    Analiza la comida y devuelve SOLO este JSON válido:
    {"nombre_plato": "string", "calorias": number, "proteinas": number, "grasas": number, "carbos": number}
    """
    intentos = 0
    while intentos < 2:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
            return json.loads(response.text.replace("```json", "").replace("```", "").strip())
        except Exception as e:
            if "429" in str(e): time.sleep(5); intentos += 1
            elif "API_KEY" in str(e): raise e
            else: break
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        raise e

def calcular_macros_logica(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero == "Hombre" else -161)
    mapa = {"Sedentario (0 días)": 1.2, "Ligero (1-2 días)": 1.375, "Moderado (3-4 días)": 1.55, "Activo (5-6 días)": 1.725, "Muy activo (7 días)": 1.9}
    factor = mapa.get(actividad, 1.2)
    calorias = tmb * factor
    prot_g_kg = 2.0
    if objetivo == "ganar musculo": calorias += 300; prot_g_kg = 2.2
    elif objetivo == "perder grasa": calorias -= 400; prot_g_kg = 2.3
    elif objetivo == "recomposicion corporal": calorias -= 100; prot_g_kg = 2.4
    elif objetivo == "mantener fisico": prot_g_kg = 1.8
    
    return {
        "calorias": int(calorias), "proteinas": int(peso * prot_g_kg),
        "grasas": int(peso * 0.9), "carbos": int((calorias - (peso * prot_g_kg * 4 + peso * 0.9 * 9)) / 4)
    }

# =================================================
# SIDEBAR PREMIUM
# =================================================
with st.sidebar:
    st.title("MacroRecioIA")
    user_name = st.session_state['user_info'].get('username', 'Usuario')
    user_id = st.session_state['user_info'].get('id_usuario')
    st.caption(f"Hola, {user_name}")
    
    # Racha
    racha_actual = calcular_racha_usuario(user_id)
    st.markdown(f"""
    <div style="background: rgba(251, 191, 36, 0.15); border: 1px solid rgba(251, 191, 36, 0.4); border-radius: 12px; padding: 10px; text-align: center; margin-bottom: 15px;">
        <h3 style="margin: 0; color: #fbbf24; font-size: 20px; font-weight: 800;">🔥 Racha: {racha_actual}</h3>
        <p style="margin: 0; font-size: 13px; color: #f8fafc; font-weight: 500;">días seguidos registrando</p>
    </div>
    """, unsafe_allow_html=True)
    
    # MENÚ LIQUID GLASS INTEGRADO
    selected = option_menu(
        menu_title=None,
        options=["Inicio", "Perfil", "Escaner", "Progreso", "Entrenador"],
        icons=["house", "person", "camera", "graph-up", "robot"],
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#10B981", "font-size": "18px"}, 
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "5px",
                "color": "#e2e8f0",
                "background-color": "transparent",
            },
            "nav-link-selected": {"background-color": "rgba(16, 185, 129, 0.2)", "color": "#10B981", "font-weight": "600", "border-left": "3px solid #10B981"},
        }
    )
    
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state['login_status'] = False
        st.session_state['user_info'] = None
        st.rerun()

# =================================================
# CONTENIDO
# =================================================

if selected == "Inicio":
    st.markdown("""
    <div class="card">
        <h1>Bienvenido a MacroRecioIA</h1>
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

    # SECCIÓN TECNOLOGÍA
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #94a3b8; margin-bottom: 20px;">
        <h4>🌟 Potenciado por Tecnología de Punta</h4>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col1.markdown("""
    <div class="card" style="text-align:center; padding: 10px;">
        <h2 style="margin:0;">🧠</h2>
        <p style="font-weight:bold; margin:0;">Gemini 2.5 Flash</p>
        <p style="font-size:12px; margin:0;">IA de Google de última generación</p>
    </div>
    """, unsafe_allow_html=True)
    col2.markdown("""
    <div class="card" style="text-align:center; padding: 10px;">
        <h2 style="margin:0;">⚡</h2>
        <p style="font-weight:bold; margin:0;">Supabase Cloud</p>
        <p style="font-size:12px; margin:0;">Base de datos en tiempo real</p>
    </div>
    """, unsafe_allow_html=True)
    col3.markdown("""
    <div class="card" style="text-align:center; padding: 10px;">
        <h2 style="margin:0;">🔒</h2>
        <p style="font-weight:bold; margin:0;">Privacidad Total</p>
        <p style="font-size:12px; margin:0;">Tus datos están encriptados</p>
    </div>
    """, unsafe_allow_html=True)

elif selected == "Perfil":
    st.markdown("<div class='card'><h2>Perfil nutricional</h2></div>", unsafe_allow_html=True)
    u = st.session_state['user_info']
    
    with st.form("perfil"):
        c1, c2 = st.columns(2)
        with c1:
            idx_genero = 0 if u.get('genero') == 'Hombre' else 1
            genero = st.selectbox("Género", ["Hombre", "Mujer"], index=idx_genero)
            edad = st.number_input("Edad", 15, 90, u.get('edad') or 25)
            peso = st.number_input("Peso (kg)", 40.0, 150.0, float(u.get('peso') or 70.0))
        with c2:
            altura = st.number_input("Altura (cm)", 140.0, 220.0, float(u.get('altura') or 170.0))
            opciones_actividad = ["Sedentario (0 días)", "Ligero (1-2 días)", "Moderado (3-4 días)", "Activo (5-6 días)", "Muy activo (7 días)"]
            try: idx_act = opciones_actividad.index(u.get('actividad'))
            except: idx_act = 0
            actividad = st.selectbox("Nivel de actividad", opciones_actividad, index=idx_act)
            
            opciones_objetivo = ["ganar musculo", "perder grasa", "recomposicion corporal", "mantener fisico"]
            try: idx_obj = opciones_objetivo.index(u.get('objetivo'))
            except: idx_obj = 0
            objetivo = st.selectbox("Objetivo", opciones_objetivo, index=idx_obj)
        
        if objetivo == "ganar musculo": st.info("💡 **Estrategia:** Superávit calórico ligero + Proteína moderada/alta para maximizar hipertrofia.")
        elif objetivo == "perder grasa": st.info("💡 **Estrategia:** Déficit calórico controlado + Proteína alta para proteger tu masa muscular.")
        elif objetivo == "recomposicion corporal": st.info("💡 **Estrategia:** Normocalórica o ligero déficit + Proteína muy alta para ganar músculo y perder grasa simultáneamente.")
        elif objetivo == "mantener fisico": st.info("💡 **Estrategia:** Calorías de mantenimiento + Proteína estándar para salud y rendimiento.")
        
        ok = st.form_submit_button("Calcular requerimientos")

    if ok:
        # === INICIO PANTALLA DE CARGA (OVERLAY) ===
        loader = st.empty()
        
        # VIDEO GENERADO (Médico musculoso cartoon escribiendo)
        video_medico = "http://googleusercontent.com/generated_video_content/15690523961302908185"
        
        loader.markdown(f"""
            <div id="loading-overlay">
                <div class="loading-content">
                    <div class="video-container">
                        <video src="{video_medico}" autoplay loop muted playsinline class="loading-video"></video>
                    </div>
                    <div class="loading-text">Analizando tu metabolismo...</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        time.sleep(3.5) 
        loader.empty() 
        # === FIN PANTALLA DE CARGA ===

        macros = calcular_macros_logica(genero, edad, peso, altura, actividad, objetivo)
        datos_para_bd = {
            'genero': genero, 'edad': edad, 'peso': peso, 'altura': altura,
            'actividad': actividad, 'objetivo': objetivo,
            'calorias': macros['calorias'], 'proteinas': macros['proteinas'],
            'grasas': macros['grasas'], 'carbos': macros['carbos']
        }
        guardar_perfil_usuario_actual(datos_para_bd)
        st.success("Perfil actualizado correctamente")
        st.rerun()

    if u.get('meta_calorias'):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Calorías", u['meta_calorias'])
        c2.metric("🥩 Proteínas", f"{u['meta_proteinas']}g")
        c3.metric("🥑 Grasas", f"{u['meta_grasas']}g")
        c4.metric("🍞 Carbos", f"{u['meta_carbos']}g")

elif selected == "Escaner":
    if not st.session_state['user_info'].get('meta_calorias'):
        st.warning("Primero configurá tu perfil")
        st.stop()

    st.markdown("<div class='card'><h2>Escanear comida</h2></div>", unsafe_allow_html=True)
    img = st.file_uploader("Subí una foto", ["jpg", "jpeg", "png"])
    if img:
        image = Image.open(img).convert("RGB")
        st.image(image, width=320)
        if st.button("Analizar comida"):
            with st.spinner("Analizando con IA..."):
                try:
                    data = analizar_comida_ia(image)
                    st.markdown(f"### 🍽️ {data['nombre_plato']}")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("🔥 Calorías", data['calorias'])
                    col2.metric("🥩 Proteínas", f"{data['proteinas']}g")
                    col3.metric("🥑 Grasas", f"{data['grasas']}g")
                    col4.metric("🍞 Carbos", f"{data['carbos']}g")

                    totales_hoy, _ = leer_progreso_hoy_usuario_actual()
                    meta = st.session_state['user_info'].get('meta_calorias')
                    if (totales_hoy["calorias"] + data["calorias"] > meta):
                        exceso = (totales_hoy["calorias"] + data["calorias"]) - meta
                        st.warning(f"⚠️ ¡Cuidado! Si comes esto excederás tu meta diaria por {exceso} calorías.")

                    guardar_comida_usuario_actual(data)
                    st.success(f"✅ {data['nombre_plato']} agregado a tu historial")
                except Exception as e:
                    if "API key expired" in str(e): st.error("🚨 TU CLAVE DE API HA CADUCADO.")
                    elif "429" in str(e): st.error("⏳ Servidor ocupado. Espera un minuto.")
                    else: st.error(f"❌ Error: {e}")

elif selected == "Progreso":
    if not st.session_state['user_info'].get('meta_calorias'):
        st.warning("Completá tu perfil primero para ver el progreso.")
        st.stop()
    u = st.session_state['user_info']
    totales, historial = leer_progreso_hoy_usuario_actual()
    meta_cal = u.get('meta_calorias', 2000)

    st.markdown("<div class='card'><h2>Progreso diario</h2></div>", unsafe_allow_html=True)
    progreso = min(totales["calorias"] / meta_cal, 1.0) if meta_cal > 0 else 0
    st.progress(progreso)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 Consumidas", totales["calorias"], f"Meta: {meta_cal}")
    c2.metric("🥩 Proteínas", totales["proteinas"], f"Meta: {u.get('meta_proteinas')}")
    c3.metric("🥑 Grasas", totales["grasas"], f"Meta: {u.get('meta_grasas')}")
    c4.metric("🍞 Carbos", totales["carbos"], f"Meta: {u.get('meta_carbos')}")
    
    st.markdown("### 📈 Tendencia")
    try:
        df_historial = obtener_historial_grafico()
        col_fecha = 'fecha_consumo' if 'fecha_consumo' in df_historial.columns else 'Fecha_Consumo'
        if not df_historial.empty: st.line_chart(df_historial.set_index(col_fecha))
        else: st.info("Aún no hay datos suficientes para mostrar gráficos.")
    except: pass

    if historial:
        st.markdown("### 🍽 Historial de Hoy")
        for h in historial:
            st.write(f"- **{h['nombre_plato']}** — {h['calorias']} kcal (P:{h['Proteinas']} G:{h['Grasas']} C:{h['Carbos']})")
    
    st.markdown("### 💾 Exportar Datos")
    try:
        df_todo = obtener_todo_csv()
        csv = df_todo.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar historial completo (CSV)", csv, 'historial.csv', 'text/csv')
    except: pass

elif selected == "Entrenador":
    st.markdown("<div class='card'><h2>💬 Tu Coach de Bolsillo</h2><p>Preguntame lo que quieras sobre tu dieta o entrenamiento.</p></div>", unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ej: ¿Qué puedo cenar ligero?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        u = st.session_state['user_info']
        totales, _ = leer_progreso_hoy_usuario_actual()
        
        contexto = f"""
        Actúa como un entrenador personal y nutricionista experto.
        Datos del usuario:
        - Objetivo: {u.get('objetivo', 'general')}
        - Calorías Meta: {u.get('meta_calorias')} (Lleva: {totales['calorias']})
        - Proteínas Meta: {u.get('meta_proteinas')} (Lleva: {totales['proteinas']})
        Responde breve y motivador.
        """
        
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    model = genai.GenerativeModel("gemini-2.5-flash")
                    response = model.generate_content(f"{contexto}\n\nUsuario: {prompt}")
                    st.markdown(response.text)
                    st.session_state.messages.append({"role": "assistant", "content": response.text})
                except:
                    st.error("Error al conectar con el coach.")

st.markdown("<div class='disclaimer'>Nota: Esta aplicación utiliza IA. Información estimativa. Puedes consultar a un profesional de la salud.</div>", unsafe_allow_html=True)
