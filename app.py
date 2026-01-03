import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
import io
import time
from datetime import date 
import pandas as pd
from sqlalchemy import text # Necesario para PostgreSQL/Supabase

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="MacroRecioIA",
    page_icon="💪",
    layout="wide"
)

# =================================================
# CONEXIÓN BASE DE DATOS (SUPABASE / POSTGRESQL)
# =================================================
def get_db_connection():
    # Conexión nativa de Streamlit a Supabase usando st.connection
    return st.connection("supabase", type="sql")

def init_db():
    conn = get_db_connection()
    # Usamos sintaxis compatible con PostgreSQL
    with conn.session as s:
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS Usuarios (
                ID_Usuario SERIAL PRIMARY KEY,
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

# Iniciamos tablas si no existen (Manejo de errores silencioso para producción)
try:
    init_db()
except Exception as e:
    # Si falla la primera vez, suele ser conexión, reintentamos o mostramos error sutil
    st.error(f"Error de conexión con la Base de Datos: {e}")

# =================================================
# FUNCIONES DE BASE DE DATOS (ADAPTADAS)
# =================================================

def guardar_perfil_bd(datos):
    conn = get_db_connection()
    # Verificar si existe usuario (ID 1 fijo por ahora)
    df = conn.query("SELECT COUNT(*) as count FROM Usuarios WHERE ID_Usuario = 1", ttl=0)
    existe = df.iloc[0]["count"]

    with conn.session as s:
        if existe == 0:
            query = text("""
                INSERT INTO Usuarios 
                (ID_Usuario, Genero, Edad, Peso, Altura, Actividad, Objetivo, 
                 Meta_Calorias, Meta_Proteinas, Meta_Grasas, Meta_Carbos)
                VALUES (1, :genero, :edad, :peso, :altura, :actividad, :objetivo, 
                        :calorias, :proteinas, :grasas, :carbos)
            """)
        else:
            query = text("""
                UPDATE Usuarios SET 
                    Genero=:genero, Edad=:edad, Peso=:peso, Altura=:altura, 
                    Actividad=:actividad, Objetivo=:objetivo, 
                    Meta_Calorias=:calorias, Meta_Proteinas=:proteinas, 
                    Meta_Grasas=:grasas, Meta_Carbos=:carbos
                WHERE ID_Usuario=1
            """)
        
        s.execute(query, {
            'genero': datos['genero'], 'edad': datos['edad'], 'peso': datos['peso'], 
            'altura': datos['altura'], 'actividad': datos['actividad'], 'objetivo': datos['objetivo'],
            'calorias': datos['calorias'], 'proteinas': datos['proteinas'], 
            'grasas': datos['grasas'], 'carbos': datos['carbos']
        })
        s.commit()

def cargar_perfil_bd():
    conn = get_db_connection()
    df = conn.query("SELECT Meta_Calorias, Meta_Proteinas, Meta_Grasas, Meta_Carbos FROM Usuarios WHERE ID_Usuario = 1", ttl=0)
    if not df.empty:
        return {
            "calorias": int(df.iloc[0]["Meta_Calorias"]), 
            "proteinas": int(df.iloc[0]["Meta_Proteinas"]), 
            "grasas": int(df.iloc[0]["Meta_Grasas"]), 
            "carbos": int(df.iloc[0]["Meta_Carbos"])
        }
    return None

def guardar_comida_bd(plato):
    conn = get_db_connection()
    with conn.session as s:
        s.execute(
            text("""
            INSERT INTO Comidas 
            (ID_Usuario, Nombre_Plato, Calorias, Proteinas, Grasas, Carbos, Fecha_Consumo)
            VALUES (1, :nombre, :calorias, :proteinas, :grasas, :carbos, :fecha)
            """),
            {
                'nombre': plato['nombre_plato'], 
                'calorias': plato['calorias'], 
                'proteinas': plato['proteinas'], 
                'grasas': plato['grasas'], 
                'carbos': plato['carbos'],
                'fecha': date.today()
            }
        )
        s.commit()

def leer_progreso_hoy_bd():
    conn = get_db_connection()
    hoy = date.today()
    # Usamos parámetros seguros (:fecha)
    query = "SELECT Nombre_Plato, Calorias, Proteinas, Grasas, Carbos FROM Comidas WHERE Fecha_Consumo = :fecha AND ID_Usuario = 1"
    df = conn.query(query, params={"fecha": hoy}, ttl=0)
    
    historial = []
    totales = {"calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0}
    
    for index, row in df.iterrows():
        historial.append({
            "nombre_plato": row["Nombre_Plato"], 
            "calorias": row["Calorias"], 
            "proteinas": row["Proteinas"], 
            "grasas": row["Grasas"], 
            "carbos": row["Carbos"]
        })
        totales["calorias"] += row["Calorias"]
        totales["proteinas"] += row["Proteinas"]
        totales["grasas"] += row["Grasas"]
        totales["carbos"] += row["Carbos"]
        
    return totales, historial

def obtener_historial_completo_df():
    conn = get_db_connection()
    query = "SELECT Fecha_Consumo, SUM(Calorias) as Total_Calorias FROM Comidas WHERE ID_Usuario=1 GROUP BY Fecha_Consumo ORDER BY Fecha_Consumo"
    return conn.query(query, ttl=0)

def obtener_todo_historial_csv():
    conn = get_db_connection()
    query = "SELECT Fecha_Consumo, Nombre_Plato, Calorias, Proteinas, Grasas, Carbos FROM Comidas WHERE ID_Usuario=1 ORDER BY Fecha_Consumo DESC"
    return conn.query(query, ttl=0)

# =================================================
# ESTILOS
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f172a, #020617); color: #f8fafc; }
[data-testid="stSidebar"] { background: #020617; border-right: 1px solid rgba(255,255,255,0.05); }
.stButton > button { width: 100%; background: linear-gradient(135deg, #10B981, #059669); color: white; border-radius: 12px; padding: 12px; font-weight: 600; border: none; margin-top: 6px; }
.stButton > button:hover { background: linear-gradient(135deg, #34D399, #10B981); }
.card { background: rgba(30,41,59,0.65); border-radius: 18px; padding: 26px; margin-bottom: 22px; border: 1px solid rgba(255,255,255,0.05); }
[data-testid="stMetric"] { background: rgba(30,41,59,0.6); padding: 16px; border-radius: 14px; text-align: center; }
.stProgress > div > div > div > div { background-color: #10B981; }
img { border-radius: 16px; }
footer {visibility: hidden;}
.disclaimer { font-size: 12px; color: #94a3b8; text-align: center; margin-top: 50px; }
</style>
""", unsafe_allow_html=True)

# =================================================
# SESSION STATE
# =================================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

if "usuario" not in st.session_state or st.session_state.usuario is None:
    try:
        perfil_db = cargar_perfil_bd()
        if perfil_db:
            st.session_state.usuario = perfil_db
        else:
            st.session_state.usuario = None
    except:
        st.session_state.usuario = None

try:
    totales_hoy, historial_hoy = leer_progreso_hoy_bd()
except:
    totales_hoy = {"calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0}
    historial_hoy = []

st.session_state.diario = {
    "fecha": datetime.date.today(),
    "calorias": totales_hoy["calorias"],
    "proteinas": totales_hoy["proteinas"],
    "grasas": totales_hoy["grasas"],
    "carbos": totales_hoy["carbos"],
    "historial": historial_hoy
}

# =================================================
# GEMINI CONFIG
# =================================================
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except:
    pass

# =================================================
# FUNCIONES IA
# =================================================
def analizar_comida(image: Image.Image):
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

    intentos = 0
    max_intentos = 2
    
    # Intento 1: Modelo Flash 2.5
    while intentos < max_intentos:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
            limpio = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(limpio)
        except Exception as e:
            if "429" in str(e): 
                time.sleep(5)
                intentos += 1
            elif "API_KEY" in str(e):
                raise e
            else:
                break

    # Intento 2: Modelo Flash 2.0 (Backup)
    try:
        model_backup = genai.GenerativeModel("gemini-2.0-flash")
        response = model_backup.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
        limpio = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(limpio)
    except Exception as e:
        raise e

def calcular_macros(genero, edad, peso, altura, actividad, objetivo):
    tmb = 10*peso + 6.25*altura - 5*edad + (5 if genero == "Hombre" else -161)
    mapa_actividad = {
        "Sedentario (0 días)": 1.2, "Ligero (1-2 días)": 1.375,
        "Moderado (3-4 días)": 1.55, "Activo (5-6 días)": 1.725,
        "Muy activo (7 días)": 1.9
    }
    factor = mapa_actividad.get(actividad, 1.2)
    calorias_mantenimiento = tmb * factor
    calorias_final = calorias_mantenimiento
    proteinas_gramos_kg = 2.0

    if objetivo == "ganar musculo":
        calorias_final += 300; proteinas_gramos_kg = 2.2
    elif objetivo == "perder grasa":
        calorias_final -= 400; proteinas_gramos_kg = 2.3
    elif objetivo == "recomposicion corporal":
        calorias_final -= 100; proteinas_gramos_kg = 2.4
    elif objetivo == "mantener fisico":
        calorias_final = calorias_mantenimiento; proteinas_gramos_kg = 1.8

    proteinas = peso * proteinas_gramos_kg
    grasas = peso * 0.9
    calorias_restantes = calorias_final - (proteinas * 4 + grasas * 9)
    carbos = calorias_restantes / 4

    return {
        "calorias": int(calorias_final), "proteinas": int(proteinas),
        "grasas": int(grasas), "carbos": int(carbos)
    }

# =================================================
# INTERFAZ
# =================================================
with st.sidebar:
    st.title("💪 MacroRecioIA")
    st.caption("Nutrición inteligente con IA")
    if st.button("🏠 Inicio"): st.session_state.pagina = "Inicio"
    if st.button("👤 Perfil"): st.session_state.pagina = "Perfil"
    if st.button("📸 Analizar comida"): st.session_state.pagina = "Escaner"
    if st.button("📊 Progreso"): st.session_state.pagina = "Progreso"
    
    st.markdown("---")
    st.caption("v1.2.0 - Pro DB")

if st.session_state.pagina == "Inicio":
    st.markdown("<div class='card'><h1>Bienvenido a MacroRecioIA</h1><p style='font-size:18px;'>Tu entrenador nutricional inteligente.</p></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.image("https://images.unsplash.com/photo-1490645935967-10de6ba17061", use_container_width=True)
    c2.image("https://images.unsplash.com/photo-1517836357463-d25dfeac3438", use_container_width=True)
    c3.image("https://images.unsplash.com/photo-1504674900247-0877df9cc836", use_container_width=True)
    st.markdown("<div class='card' style='text-align:center;'><h3>🌱 El progreso es constante</h3></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    c1.markdown("<div class='card'><h2>¿Para qué sirve?</h2><ul><li>📊 Macros personalizados</li><li>📸 Analizar comidas con IA</li><li>📈 Ver progreso</li></ul></div>", unsafe_allow_html=True)
    c2.markdown("<div class='card'><h2>¿Cómo se usa?</h2><ol><li>Completá tu perfil</li><li>Escaneá comidas</li><li>Seguimiento visual</li></ol></div>", unsafe_allow_html=True)

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
            actividad = st.selectbox("Nivel de actividad", ["Sedentario (0 días)", "Ligero (1-2 días)", "Moderado (3-4 días)", "Activo (5-6 días)", "Muy activo (7 días)"])
            objetivo = st.selectbox("Objetivo", ["ganar musculo", "perder grasa", "recomposicion corporal", "mantener fisico"])
        
        if objetivo == "ganar musculo": st.info("💡 Superávit calórico ligero + Proteína moderada.")
        elif objetivo == "perder grasa": st.info("💡 Déficit calórico controlado + Proteína alta.")
        elif objetivo == "recomposicion corporal": st.info("💡 Normocalórica + Proteína muy alta.")
        elif objetivo == "mantener fisico": st.info("💡 Calorías de mantenimiento.")
        
        ok = st.form_submit_button("Calcular requerimientos")

    if ok:
        macros = calcular_macros(genero, edad, peso, altura, actividad, objetivo)
        st.session_state.usuario = macros
        guardar_perfil_bd({
            'genero': genero, 'edad': edad, 'peso': peso, 'altura': altura,
            'actividad': actividad, 'objetivo': objetivo,
            'calorias': macros['calorias'], 'proteinas': macros['proteinas'],
            'grasas': macros['grasas'], 'carbos': macros['carbos']
        })

    if st.session_state.usuario:
        u = st.session_state.usuario
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🔥 Calorías", u["calorias"])
        c2.metric("🥩 Proteínas", f"{u['proteinas']}g")
        c3.metric("🥑 Grasas", f"{u['grasas']}g")
        c4.metric("🍞 Carbos", f"{u['carbos']}g")

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
                try:
                    data = analizar_comida(image)
                    
                    st.markdown(f"### 🍽️ {data['nombre_plato']}")
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("🔥 Calorías", data['calorias'])
                    col2.metric("🥩 Proteínas", f"{data['proteinas']}g")
                    col3.metric("🥑 Grasas", f"{data['grasas']}g")
                    col4.metric("🍞 Carbos", f"{data['carbos']}g")

                    u = st.session_state.usuario
                    d = st.session_state.diario
                    if u and (d["calorias"] + data["calorias"] > u["calorias"]):
                        exceso = (d["calorias"] + data["calorias"]) - u["calorias"]
                        st.warning(f"⚠️ ¡Cuidado! Si comes esto excederás tu meta diaria por {exceso} calorías.")

                    guardar_comida_bd(data)
                    for k in ["calorias", "proteinas", "grasas", "carbos"]: d[k] += data[k]
                    d["historial"].append(data)
                    st.success(f"✅ {data['nombre_plato']} agregado a tu historial")
                
                except Exception as e:
                    if "API key expired" in str(e):
                        st.error("🚨 TU CLAVE DE API HA CADUCADO.")
                    elif "429" in str(e):
                        st.error("⏳ Servidor ocupado. Espera un minuto.")
                    else:
                        st.error(f"❌ Error: {e}")

elif st.session_state.pagina == "Progreso":
    if not st.session_state.usuario:
        st.warning("Completá tu perfil primero para ver el progreso.")
        st.stop()
    u = st.session_state.usuario
    d = st.session_state.diario
    st.markdown("<div class='card'><h2>Progreso diario</h2></div>", unsafe_allow_html=True)
    progreso = min(d["calorias"] / u["calorias"], 1.0) if u["calorias"] > 0 else 0
    st.progress(progreso)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔥 Consumidas", d["calorias"], f"Meta: {u['calorias']}")
    c2.metric("🥩 Proteínas", d["proteinas"], f"Meta: {u['proteinas']}")
    c3.metric("🥑 Grasas", d["grasas"], f"Meta: {u['grasas']}")
    c4.metric("🍞 Carbos", d["carbos"], f"Meta: {u['carbos']}")
    
    st.markdown("### 📈 Tendencia")
    try:
        df_historial = obtener_historial_completo_df()
        if not df_historial.empty:
            st.line_chart(df_historial.set_index('Fecha_Consumo'))
        else:
            st.info("Aún no hay datos suficientes.")
    except:
        pass

    if d["historial"]:
        st.markdown("### 🍽 Historial de Hoy")
        for h in d["historial"]:
            st.write(f"- **{h['nombre_plato']}** — {h['calorias']} kcal (P:{h['proteinas']} G:{h['grasas']} C:{h['carbos']})")
    
    st.markdown("### 💾 Exportar Datos")
    try:
        df_todo = obtener_todo_historial_csv()
        csv = df_todo.to_csv(index=False).encode('utf-8')
        st.download_button("Descargar historial completo (CSV)", csv, 'historial.csv', 'text/csv')
    except:
        pass

st.markdown("<div class='disclaimer'>Nota: Esta aplicación utiliza IA. Información estimativa. Consulta a un profesional de la salud.</div>", unsafe_allow_html=True)
