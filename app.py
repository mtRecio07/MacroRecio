import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
import io
import sqlite3
import os
from datetime import date

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

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# =================================================
# FUNCIONES BD
# =================================================
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
    cursor.execute("""
    SELECT Meta_Calorias, Meta_Proteinas, Meta_Grasas, Meta_Carbos
    FROM Usuarios WHERE ID_Usuario=1
    """)
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
    cursor.execute("""
    SELECT Nombre_Plato, Calorias, Proteinas, Grasas, Carbos
    FROM Comidas
    WHERE Fecha_Consumo=? AND ID_Usuario=1
    """, (date.today().isoformat(),))
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
[data-testid="stSidebar"] { background: #020617; }
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #10B981, #059669);
    color: white;
    border-radius: 12px;
    padding: 12px;
    font-weight: 600;
}
.card {
    background: rgba(30,41,59,0.65);
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 22px;
}
</style>
""", unsafe_allow_html=True)

# =================================================
# SESSION STATE
# =================================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

if "usuario" not in st.session_state:
    st.session_state.usuario = cargar_perfil_bd()

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
# GEMINI
# =================================================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

def analizar_comida(image):
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    response = model.generate_content([
        "Devuelve SOLO este JSON válido con valores nutricionales:",
        {"mime_type": "image/jpeg", "data": buffer.getvalue()}
    ])
    limpio = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(limpio)

# =================================================
# SIDEBAR
# =================================================
with st.sidebar:
    st.title("💪 MacroRecioIA")
    if st.button("🏠 Inicio"): st.session_state.pagina = "Inicio"
    if st.button("👤 Perfil"): st.session_state.pagina = "Perfil"
    if st.button("📸 Analizar comida"): st.session_state.pagina = "Escaner"
    if st.button("📊 Progreso"): st.session_state.pagina = "Progreso"

# =================================================
# PÁGINAS
# =================================================
if st.session_state.pagina == "Inicio":
    st.markdown("<div class='card'><h1>Bienvenido a MacroRecioIA 💪</h1></div>", unsafe_allow_html=True)

elif st.session_state.pagina == "Perfil":
    with st.form("perfil"):
        genero = st.selectbox("Género", ["Hombre", "Mujer"])
        edad = st.number_input("Edad", 15, 90, 25)
        peso = st.number_input("Peso", 40, 150, 70)
        altura = st.number_input("Altura", 140, 220, 170)
        actividad = st.selectbox("Actividad", [
            "Sedentario (0 días)",
            "Ligero (1-2 días)",
            "Moderado (3-4 días)",
            "Activo (5-6 días)",
            "Muy activo (7 días)"
        ])
        objetivo = st.selectbox("Objetivo", [
            "ganar musculo", "perder grasa",
            "recomposicion corporal", "mantener fisico"
        ])
        ok = st.form_submit_button("Calcular requerimientos")

    if ok:
        calorias = int(peso * 30)
        macros = {
            "calorias": calorias,
            "proteinas": int(peso * 2),
            "grasas": int(peso * 0.9),
            "carbos": int((calorias - (peso*2*4 + peso*0.9*9)) / 4)
        }
        st.session_state.usuario = macros
        guardar_perfil_bd({
            "genero": genero, "edad": edad, "peso": peso,
            "altura": altura, "actividad": actividad,
            "objetivo": objetivo, **macros
        })
        st.success("Perfil guardado")

elif st.session_state.pagina == "Escaner":
    img = st.file_uploader("Subí una foto", ["jpg", "png"])
    if img and st.button("Analizar"):
        data = analizar_comida(Image.open(img))
        guardar_comida_bd(data)
        st.success(data["nombre_plato"])

elif st.session_state.pagina == "Progreso":
    d = st.session_state.diario
    st.metric("Calorías hoy", d["calorias"])
    for h in d["historial"]:
        st.write(h)
