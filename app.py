import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
import io
import time
from datetime import date 
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
# ESTILOS CSS (TU DISEÑO ORIGINAL)
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f172a, #020617); color: #f8fafc; }
.stTextInput > div > div > input { color: #000000; } 
.card { background: rgba(30,41,59,0.65); border-radius: 18px; padding: 26px; margin-bottom: 22px; border: 1px solid rgba(255,255,255,0.05); }
[data-testid="stMetric"] { background: rgba(30,41,59,0.6); padding: 16px; border-radius: 14px; text-align: center; }
.stProgress > div > div > div > div { background-color: #10B981; }
img { border-radius: 16px; }
footer {visibility: hidden;}
.disclaimer { font-size: 12px; color: #94a3b8; text-align: center; margin-top: 50px; }
/* Ocultar menú default */
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
        # Tabla Usuarios AHORA CON LOGIN (Username/Password)
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
        # Tabla Comidas
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

# Inicializar DB
try:
    init_db()
except:
    pass

# =================================================
# FUNCIONES DE LOGIN Y REGISTRO
# =================================================
def registrar_usuario(username, password):
    conn = get_db_connection()
    # Verificar si existe
    try:
        df = conn.query("SELECT COUNT(*) as count FROM Usuarios WHERE Username = :user", params={"user": username}, ttl=0)
        if df.iloc[0]["count"] > 0:
            return False, "El usuario ya existe."
    except:
        pass # Si falla la consulta, asumimos que no existe o es error de tabla vacía
    
    with conn.session as s:
        s.execute(text("""
            INSERT INTO Usuarios (Username, Password) VALUES (:user, :pass)
        """), {"user": username, "pass": password})
        s.commit()
    return True, "Registro exitoso. Ahora inicia sesión."

def login_usuario(username, password):
    conn = get_db_connection()
    # Buscamos usuario y contraseña
    query = "SELECT * FROM Usuarios WHERE Username = :user AND Password = :pass"
    df = conn.query(query, params={"user": username, "pass": password}, ttl=0)
    
    if not df.empty:
        # Convertimos a diccionario para la sesión (nombres de columnas pueden venir en minuscula)
        user_data = df.iloc[0].to_dict()
        # Normalizamos claves por si acaso PostgreSQL las devuelve en minúscula
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
# LÓGICA DE PANTALLAS (LOGIN VS APP)
# =================================================

# 1. SI NO ESTÁ LOGUEADO -> MOSTRAR LOGIN
if not st.session_state['login_status']:
    st.markdown("<h1 style='text-align: center;'>MacroRecioIA</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Tu entrenador inteligente.</p>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        with st.form("login_form"):
            user = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            submit = st.form_submit_button("Entrar")
            if submit:
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
            submit_reg = st.form_submit_button("Crear Cuenta")
            if submit_reg:
                if new_user and new_pass:
                    ok, msg = registrar_usuario(new_user, new_pass)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
                else:
                    st.warning("Completa todos los campos.")
    
    st.stop() # Detiene la ejecución del resto del código si no hay login

# 2. SI ESTÁ LOGUEADO -> MOSTRAR APP COMPLETA
# (Aquí empieza tu código original adaptado al usuario logueado)

# Cargar API
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    pass

# --- Funciones de Datos ESPECÍFICAS DEL USUARIO ---
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
    # Actualizar la sesión local para ver los cambios al instante
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
        historial.append(row.to_dict())
        totales["calorias"] += row["Calorias"]
        totales["proteinas"] += row["Proteinas"]
        totales["grasas"] += row["Grasas"]
        totales["carbos"] += row["Carbos"]
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

# Funciones de cálculo e IA
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
# SIDEBAR
# =================================================
with st.sidebar:
    st.title("MacroRecioIA")
    user_name = st.session_state['user_info'].get('username', 'Usuario')
    st.write(f"Hola, **{user_name}** 👋")
    
    selected = option_menu(
        menu_title=None,
        options=["Inicio", "Perfil", "Escaner", "Progreso"],
        icons=["house", "person", "camera", "graph-up"],
        default_index=0,
    )
    
    if st.button("Cerrar Sesión"):
        st.session_state['login_status'] = False
        st.session_state['user_info'] = None
        st.rerun()
    
    st.markdown("---")
    st.caption("v2.0 - Multiuser")

# =================================================
# PÁGINAS (DISEÑO INTACTO)
# =================================================

if selected == "Inicio":
    st.markdown("<div class='card'><h1>Bienvenido a MacroRecioIA</h1><p style='font-size:18px;'>Tu entrenador nutricional inteligente.</p></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.image("https://images.unsplash.com/photo-1490645935967-10de6ba17061", use_container_width=True)
    c2.image("https://images.unsplash.com/photo-1517836357463-d25dfeac3438", use_container_width=True)
    c3.image("https://images.unsplash.com/photo-1504674900247-0877df9cc836", use_container_width=True)
    st.markdown("<div class='card' style='text-align:center;'><h3>🌱 El progreso es constante</h3></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown("<div class='card'><h2>¿Para qué sirve?</h2><ul><li>📊 Macros personalizados</li><li>📸 Analizar comidas con IA</li><li>📈 Ver progreso</li></ul></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card'><h2>¿Cómo se usa?</h2><ol><li>Completá tu perfil</li><li>Escaneá comidas</li><li>Seguimiento visual</li></ol></div>", unsafe_allow_html=True)

    # --- AGREGADO PROFESIONAL Y LLAMATIVO ---
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
    
    # Recuperamos datos del usuario para pre-llenar el form
    u = st.session_state['user_info']
    
    with st.form("perfil"):
        c1, c2 = st.columns(2)
        with c1:
            # Pre-seleccionamos valores si existen en la BD
            idx_genero = 0 if u.get('genero') == 'Hombre' else 1
            genero = st.selectbox("Género", ["Hombre", "Mujer"], index=idx_genero)
            edad = st.number_input("Edad", 15, 90, u.get('edad') or 25)
            peso = st.number_input("Peso (kg)", 40, 150, float(u.get('peso') or 70))
        with c2:
            altura = st.number_input("Altura (cm)", 140, 220, float(u.get('altura') or 170))
            
            # Buscar el index de la actividad guardada
            opciones_actividad = ["Sedentario (0 días)", "Ligero (1-2 días)", "Moderado (3-4 días)", "Activo (5-6 días)", "Muy activo (7 días)"]
            try:
                idx_act = opciones_actividad.index(u.get('actividad'))
            except:
                idx_act = 0
            actividad = st.selectbox("Nivel de actividad", opciones_actividad, index=idx_act)
            
            # Buscar el index del objetivo guardado
            opciones_objetivo = ["ganar musculo", "perder grasa", "recomposicion corporal", "mantener fisico"]
            try:
                idx_obj = opciones_objetivo.index(u.get('objetivo'))
            except:
                idx_obj = 0
            objetivo = st.selectbox("Objetivo", opciones_objetivo, index=idx_obj)
        
        if objetivo == "ganar musculo": st.info("💡 Superávit calórico ligero + Proteína moderada.")
        elif objetivo == "perder grasa": st.info("💡 Déficit calórico controlado + Proteína alta.")
        elif objetivo == "recomposicion corporal": st.info("💡 Normocalórica + Proteína muy alta.")
        elif objetivo == "mantener fisico": st.info("💡 Calorías de mantenimiento.")
        
        ok = st.form_submit_button("Calcular requerimientos")

    if ok:
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

    # Mostrar métricas si el usuario tiene metas
    if u.get('meta_calorias'):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Calorías", u['meta_calorias'])
        c2.metric("🥩 Proteínas", f"{u['meta_proteinas']}g")
        c3.metric("🥑 Grasas", f"{u['meta_grasas']}g")
        c4.metric("🍞 Carbos", f"{u['meta_carbos']}g")

elif selected == "Escaner":
    # Verificar si tiene perfil configurado (meta > 0)
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

                    # Alerta Exceso
                    totales_hoy, _ = leer_progreso_hoy_usuario_actual()
                    meta = st.session_state['user_info'].get('meta_calorias')
                    
                    if (totales_hoy["calorias"] + data["calorias"] > meta):
                        exceso = (totales_hoy["calorias"] + data["calorias"]) - meta
                        st.warning(f"⚠️ ¡Cuidado! Si comes esto excederás tu meta diaria por {exceso} calorías.")

                    guardar_comida_usuario_actual(data)
                    st.success(f"✅ {data['nombre_plato']} agregado a tu historial")
                
                except Exception as e:
                    if "API key expired" in str(e):
                        st.error("🚨 TU CLAVE DE API HA CADUCADO.")
                    elif "429" in str(e):
                        st.error("⏳ Servidor ocupado. Espera un minuto.")
                    else:
                        st.error(f"❌ Error: {e}")

elif selected == "Progreso":
    if not st.session_state['user_info'].get('meta_calorias'):
        st.warning("Completá tu perfil primero para ver el progreso.")
        st.stop()
        
    u = st.session_state['user_info']
    totales, historial = leer_progreso_hoy_usuario_actual()
    meta_cal = u.get('meta_calorias', 2000)

    st.markdown("<div class='card'><h2>Progreso diario</h2></div>", unsafe_allow_html=True)
    
    if meta_cal > 0:
        progreso = min(totales["calorias"] / meta_cal, 1.0)
    else:
        progreso = 0
        
    st.progress(progreso)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 Consumidas", totales["calorias"], f"Meta: {meta_cal}")
    c2.metric("🥩 Proteínas", totales["proteinas"], f"Meta: {u.get('meta_proteinas')}")
    c3.metric("🥑 Grasas", totales["grasas"], f"Meta: {u.get('meta_grasas')}")
    c4.metric("🍞 Carbos", totales["carbos"], f"Meta: {u.get('meta_carbos')}")
    
    st.markdown("### 📈 Tendencia")
    try:
        df_historial = obtener_historial_grafico()
        if not df_historial.empty:
            st.line_chart(df_historial.set_index('Fecha_Consumo'))
        else:
            st.info("Aún no hay datos suficientes.")
    except:
        pass

    if historial:
        st.markdown("### 🍽 Historial de Hoy")
        for h in historial:
            st.write(f"- **{h['Nombre_Plato']}** — {h['Calorias']} kcal (P:{h['Proteinas']} G:{h['Grasas']} C:{h['Carbos']})")
    
    st.markdown("### 💾 Exportar Datos")
    try:
        df_todo = obtener_todo_csv()
        csv = df_todo.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar historial completo (CSV)", csv, 'historial.csv', 'text/csv')
    except:
        pass

st.markdown("<div class='disclaimer'>Nota: Esta aplicación utiliza IA. Información estimativa. Puedes consultar a un profesional de la salud.</div>", unsafe_allow_html=True)
