import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
import io
import sqlite3 
import os      
from datetime import date 
import time

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="MacroRecioIA",
    page_icon="💪",
    layout="wide"
)

# =================================================
# SQLITE - CONFIGURACIÓN AUTOMÁTICA
# =================================================
DB_PATH = "database/macrorecio.db"

def init_db():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Usuarios (
        ID_Usuario INTEGER PRIMARY KEY AUTOINCREMENT,
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
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Comidas (
        ID_Comida INTEGER PRIMARY KEY AUTOINCREMENT,
        ID_Usuario INTEGER,
        Nombre_Plato TEXT,
        Calorias INTEGER,
        Proteinas INTEGER,
        Grasas INTEGER,
        Carbos INTEGER,
        Fecha_Consumo TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# =================================================
# CONEXIÓN BASE DE DATOS (SQLITE)
# =================================================
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

def guardar_perfil_bd(datos):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Usuarios")
    existe = cursor.fetchone()[0]

    if existe == 0:
        cursor.execute("""
        INSERT INTO Usuarios 
        (Genero, Edad, Peso, Altura, Actividad, Objetivo, 
         Meta_Calorias, Meta_Proteinas, Meta_Grasas, Meta_Carbos)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos['genero'], datos['edad'], datos['peso'], datos['altura'], 
            datos['actividad'], datos['objetivo'], 
            datos['calorias'], datos['proteinas'], 
            datos['grasas'], datos['carbos']
        ))
    else:
        cursor.execute("""
        UPDATE Usuarios SET 
            Genero=?, Edad=?, Peso=?, Altura=?, Actividad=?, Objetivo=?, 
            Meta_Calorias=?, Meta_Proteinas=?, Meta_Grasas=?, Meta_Carbos=?
        WHERE ID_Usuario=1
        """, (
            datos['genero'], datos['edad'], datos['peso'], datos['altura'], 
            datos['actividad'], datos['objetivo'], 
            datos['calorias'], datos['proteinas'], 
            datos['grasas'], datos['carbos']
        ))
    conn.commit()
    conn.close()

def cargar_perfil_bd():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Meta_Calorias, Meta_Proteinas, Meta_Grasas, Meta_Carbos FROM Usuarios WHERE ID_Usuario=1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "calorias": row["Meta_Calorias"], 
            "proteinas": row["Meta_Proteinas"], 
            "grasas": row["Meta_Grasas"], 
            "carbos": row["Meta_Carbos"]
        }
    return None

def guardar_comida_bd(plato):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO Comidas 
    (ID_Usuario, Nombre_Plato, Calorias, Proteinas, Grasas, Carbos, Fecha_Consumo)
    VALUES (1, ?, ?, ?, ?, ?, ?)
    """, (
        plato['nombre_plato'], 
        plato['calorias'], 
        plato['proteinas'], 
        plato['grasas'], 
        plato['carbos'],
        date.today().isoformat()
    ))
    conn.commit()
    conn.close()

def leer_progreso_hoy_bd():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Nombre_Plato, Calorias, Proteinas, Grasas, Carbos FROM Comidas WHERE Fecha_Consumo=? AND ID_Usuario=1", (date.today().isoformat(),))
    rows = cursor.fetchall()
    conn.close()
    historial = []
    totales = {"calorias": 0, "proteinas": 0, "grasas": 0, "carbos": 0}
    for r in rows:
        historial.append({
            "nombre_plato": r["Nombre_Plato"], 
            "calorias": r["Calorias"], 
            "proteinas": r["Proteinas"], 
            "grasas": r["Grasas"], 
            "carbos": r["Carbos"]
        })
        totales["calorias"] += r["Calorias"]
        totales["proteinas"] += r["Proteinas"]
        totales["grasas"] += r["Grasas"]
        totales["carbos"] += r["Carbos"]
    return totales, historial

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
</style>
""", unsafe_allow_html=True)

# =================================================
# SESSION STATE
# =================================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

if "usuario" not in st.session_state or st.session_state.usuario is None:
    perfil_db = cargar_perfil_bd()
    if perfil_db:
        st.session_state.usuario = perfil_db
    else:
        st.session_state.usuario = None

totales_hoy, historial_hoy = leer_progreso_hoy_bd()
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
# FUNCIONES IA (CON GEMINI 2.5 FLASH)
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

    # Intentamos con gemini-2.5-flash como pediste
    intentos = 0
    max_intentos = 2
    
    while intentos < max_intentos:
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
            limpio = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(limpio)
        except Exception as e:
            if "429" in str(e): # Error de cuota
                time.sleep(5)
                intentos += 1
            elif "API_KEY" in str(e):
                # Si la key está mal, no sirve de nada reintentar
                raise e
            else:
                # Si falla el 2.5, intentamos fallback con el 2.0 que funcionaba antes
                break

    # Backup: gemini-2.0-flash
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

if st.session_state.pagina == "Inicio":
    st.markdown("<div class='card'><h1>Bienvenido a MacroRecioIA 💪</h1><p style='font-size:18px;'>Tu entrenador nutricional inteligente.</p></div>", unsafe_allow_html=True)
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
                    guardar_comida_bd(data)
                    d = st.session_state.diario
                    for k in ["calorias", "proteinas", "grasas", "carbos"]: d[k] += data[k]
                    d["historial"].append(data)
                    st.success(f"✅ {data['nombre_plato']} guardado en BD")
                except Exception as e:
                    if "API key expired" in str(e):
                        st.error("🚨 TU CLAVE DE API HA CADUCADO. Necesitas generar una nueva en Google AI Studio y actualizarla en Streamlit Cloud Secrets.")
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
    if d["historial"]:
        st.markdown("### 🍽 Historial")
        for h in d["historial"]:
            st.write(f"- **{h['nombre_plato']}** — {h['calorias']} kcal (P:{h['proteinas']} G:{h['grasas']} C:{h['carbos']})")
