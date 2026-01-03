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
from streamlit_option_menu import option_menu # Necesitas agregar esto a requirements.txt

# =================================================
# CONFIGURACIÓN DE PÁGINA
# =================================================
st.set_page_config(
    page_title="MacroRecioIA",
    layout="wide"
)

# =================================================
# ESTILOS CSS
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f172a, #020617); color: #f8fafc; }
.stTextInput > div > div > input { color: #000000; } 
.card { background: rgba(30,41,59,0.65); border-radius: 18px; padding: 26px; margin-bottom: 22px; border: 1px solid rgba(255,255,255,0.05); }
[data-testid="stMetric"] { background: rgba(30,41,59,0.6); padding: 16px; border-radius: 14px; text-align: center; }
img { border-radius: 16px; }
.disclaimer { font-size: 12px; color: #94a3b8; text-align: center; margin-top: 50px; }
/* Ocultar menú de hamburguesa default */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
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
        # Tabla Usuarios con Login
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

try:
    init_db()
except:
    pass

# =================================================
# FUNCIONES DE LOGIN Y USUARIO
# =================================================
def registrar_usuario(username, password):
    conn = get_db_connection()
    # Verificar si existe
    df = conn.query("SELECT COUNT(*) as count FROM Usuarios WHERE Username = :user", params={"user": username}, ttl=0)
    if df.iloc[0]["count"] > 0:
        return False, "El usuario ya existe."
    
    with conn.session as s:
        s.execute(text("""
            INSERT INTO Usuarios (Username, Password) VALUES (:user, :pass)
        """), {"user": username, "pass": password})
        s.commit()
    return True, "Registro exitoso. Ahora inicia sesión."

def login_usuario(username, password):
    conn = get_db_connection()
    query = "SELECT * FROM Usuarios WHERE Username = :user AND Password = :pass"
    df = conn.query(query, params={"user": username, "pass": password}, ttl=0)
    if not df.empty:
        return df.iloc[0].to_dict() # Retorna todo el perfil del usuario
    return None

# =================================================
# GESTIÓN DE SESIÓN
# =================================================
if 'login_status' not in st.session_state:
    st.session_state['login_status'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# =================================================
# PANTALLA DE LOGIN / REGISTRO
# =================================================
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
    
    # Detener ejecución aquí si no hay login
    st.stop()

# =================================================
# APLICACIÓN PRINCIPAL (SOLO SI ESTÁ LOGUEADO)
# =================================================

# Cargar API Key
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    pass

# --- Funciones de Datos Propias del Usuario Logueado ---
def guardar_perfil_completo(datos):
    conn = get_db_connection()
    user_id = st.session_state['user_info']['id_usuario'] # Clave PostgreSQL suele ser minuscula
    
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
            'uid': user_id,
            'genero': datos['genero'], 'edad': datos['edad'], 'peso': datos['peso'], 
            'altura': datos['altura'], 'actividad': datos['actividad'], 'objetivo': datos['objetivo'],
            'calorias': datos['calorias'], 'proteinas': datos['proteinas'], 
            'grasas': datos['grasas'], 'carbos': datos['carbos']
        })
        s.commit()
    # Actualizar sesión local
    st.session_state['user_info'].update(datos)

def guardar_comida(plato):
    conn = get_db_connection()
    user_id = st.session_state['user_info']['id_usuario']
    with conn.session as s:
        s.execute(text("""
            INSERT INTO Comidas 
            (ID_Usuario, Nombre_Plato, Calorias, Proteinas, Grasas, Carbos, Fecha_Consumo)
            VALUES (:uid, :nombre, :calorias, :proteinas, :grasas, :carbos, :fecha)
        """), {
            'uid': user_id, 'nombre': plato['nombre_plato'], 'calorias': plato['calorias'], 
            'proteinas': plato['proteinas'], 'grasas': plato['grasas'], 'carbos': plato['carbos'],
            'fecha': date.today()
        })
        s.commit()

def leer_progreso_hoy():
    conn = get_db_connection()
    user_id = st.session_state['user_info']['id_usuario']
    hoy = date.today()
    query = "SELECT Nombre_Plato, Calorias, Proteinas, Grasas, Carbos FROM Comidas WHERE Fecha_Consumo = :fecha AND ID_Usuario = :uid"
    df = conn.query(query, params={"fecha": hoy, "uid": user_id}, ttl=0)
    
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
    user_id = st.session_state['user_info']['id_usuario']
    query = "SELECT Fecha_Consumo, SUM(Calorias) as Total_Calorias FROM Comidas WHERE ID_Usuario=:uid GROUP BY Fecha_Consumo ORDER BY Fecha_Consumo"
    return conn.query(query, params={"uid": user_id}, ttl=0)

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
    # Fallback
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        raise e

def calcular_macros_logica(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero == "Hombre" else -161)
    mapa = {"Sedentario": 1.2, "Ligero": 1.375, "Moderado": 1.55, "Activo": 1.725, "Muy activo": 1.9}
    factor = 1.2
    for k, v in mapa.items():
        if k in actividad: factor = v
            
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
# SIDEBAR NAVEGACIÓN
# =================================================
with st.sidebar:
    st.title("MacroRecioIA")
    username = st.session_state['user_info']['username']
    st.write(f"Hola, **{username}** 👋")
    
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

# =================================================
# PÁGINAS DEL USUARIO
# =================================================

if selected == "Inicio":
    st.markdown("<div class='card'><h1>Bienvenido a tu Panel</h1><p>Control total de tu nutrición.</p></div>", unsafe_allow_html=True)
    
    # Métricas rápidas de hoy
    totales, _ = leer_progreso_hoy()
    meta_cal = st.session_state['user_info'].get('meta_calorias') or 0
    
    col1, col2 = st.columns(2)
    col1.metric("Calorías Hoy", totales['calorias'], f"Meta: {meta_cal}")
    if meta_cal > 0:
        col2.progress(min(totales['calorias'] / meta_cal, 1.0))
    
    # Sección Tecnológica
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #94a3b8;'><h4>🌟 Potenciado por Tecnología de Punta</h4></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.markdown("<div class='card' style='text-align:center;'><h2>🧠</h2><p>Gemini 2.5 Flash</p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card' style='text-align:center;'><h2>⚡</h2><p>Supabase Cloud</p></div>", unsafe_allow_html=True)
    c3.markdown("<div class='card' style='text-align:center;'><h2>🔒</h2><p>Datos Privados</p></div>", unsafe_allow_html=True)

elif selected == "Perfil":
    st.markdown("<div class='card'><h2>Tu Perfil Nutricional</h2></div>", unsafe_allow_html=True)
    u = st.session_state['user_info']
    
    with st.form("perfil_form"):
        c1, c2 = st.columns(2)
        genero = c1.selectbox("Género", ["Hombre", "Mujer"], index=0 if u.get('genero') == 'Hombre' else 1)
        edad = c1.number_input("Edad", 15, 90, u.get('edad') or 25)
        peso = c1.number_input("Peso (kg)", 40, 150, float(u.get('peso') or 70))
        
        altura = c2.number_input("Altura (cm)", 140, 220, float(u.get('altura') or 170))
        actividad = c2.selectbox("Actividad", ["Sedentario", "Ligero", "Moderado", "Activo", "Muy activo"], index=0)
        objetivo = c2.selectbox("Objetivo", ["ganar musculo", "perder grasa", "recomposicion corporal", "mantener fisico"])
        
        if st.form_submit_button("Calcular y Guardar"):
            macros = calcular_macros_logica(genero, edad, peso, altura, actividad, objetivo)
            # Guardar todo en BD y Session
            datos_completos = {
                'genero': genero, 'edad': edad, 'peso': peso, 'altura': altura,
                'actividad': actividad, 'objetivo': objetivo,
                'meta_calorias': macros['calorias'], 'meta_proteinas': macros['proteinas'],
                'meta_grasas': macros['grasas'], 'meta_carbos': macros['carbos']
            }
            guardar_perfil_completo(datos_completos)
            st.success("✅ Perfil actualizado correctamente.")
            st.rerun()

    if u.get('meta_calorias'):
        st.markdown("### Tus Metas Diarias")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Calorías", u['meta_calorias'])
        c2.metric("🥩 Proteínas", f"{u['meta_proteinas']}g")
        c3.metric("🥑 Grasas", f"{u['meta_grasas']}g")
        c4.metric("🍞 Carbos", f"{u['meta_carbos']}g")

elif selected == "Escaner":
    st.markdown("<div class='card'><h2>Escanear Comida</h2></div>", unsafe_allow_html=True)
    img = st.file_uploader("Sube una foto", type=["jpg", "png", "jpeg"])
    
    if img:
        st.image(img, width=300)
        if st.button("Analizar con IA"):
            with st.spinner("Procesando..."):
                try:
                    data = analizar_comida_ia(Image.open(img))
                    
                    st.markdown(f"### 🍽️ {data['nombre_plato']}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Calorías", data['calorias'])
                    c2.metric("Proteínas", f"{data['proteinas']}g")
                    c3.metric("Grasas", f"{data['grasas']}g")
                    c4.metric("Carbos", f"{data['carbos']}g")
                    
                    # Alerta de exceso
                    totales, _ = leer_progreso_hoy()
                    meta = st.session_state['user_info'].get('meta_calorias') or 2000
                    if (totales['calorias'] + data['calorias']) > meta:
                        st.warning(f"⚠️ Atención: Excederás tu meta por {(totales['calorias'] + data['calorias']) - meta} kcal.")
                    
                    guardar_comida(data)
                    st.success("Comida guardada en tu historial.")
                except Exception as e:
                    st.error(f"Error: {e}")

elif selected == "Progreso":
    st.markdown("<div class='card'><h2>Tu Progreso</h2></div>", unsafe_allow_html=True)
    totales, historial = leer_progreso_hoy()
    meta = st.session_state['user_info'].get('meta_calorias') or 1
    
    st.progress(min(totales['calorias']/meta, 1.0))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Consumidas", totales['calorias'], f"/{meta}")
    c2.metric("Proteínas", totales['proteinas'])
    c3.metric("Grasas", totales['grasas'])
    c4.metric("Carbos", totales['carbos'])
    
    st.subheader("📈 Tendencia")
    df_graf = obtener_historial_grafico()
    if not df_graf.empty:
        st.line_chart(df_graf.set_index('Fecha_Consumo'))
    else:
        st.info("No hay datos suficientes para mostrar gráficos.")
        
    st.subheader("🍽️ Comidas de Hoy")
    for h in historial:
        st.text(f"{h['Nombre_Plato']} - {h['Calorias']} kcal")

st.markdown("<div class='disclaimer'>Nota: Esta aplicación utiliza IA. Información estimativa. Puedes consultar a un profesional de la salud.</div>", unsafe_allow_html=True)
