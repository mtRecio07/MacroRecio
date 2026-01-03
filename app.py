import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
import io
import sqlite3

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="MacroRecioIA",
    page_icon="💪",
    layout="wide"
)

# =================================================
# SQLITE DB
# =================================================
DB_NAME = "macrorecio.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Usuarios (
        ID_Usuario INTEGER PRIMARY KEY,
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
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        ID_Usuario INTEGER,
        Nombre_Plato TEXT,
        Calorias INTEGER,
        Proteinas INTEGER,
        Grasas INTEGER,
        Carbos INTEGER,
        Fecha_Consumo DATE
    )
    """)

    conn.commit()
    conn.close()

init_db()

# =================================================
# BD FUNCTIONS
# =================================================
def guardar_perfil_bd(datos):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM Usuarios WHERE ID_Usuario = 1")
    existe = cursor.fetchone()[0]

    if existe == 0:
        cursor.execute("""
        INSERT INTO Usuarios VALUES (1,?,?,?,?,?,?,?,?,?,?)
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
            "calorias": row[0],
            "proteinas": row[1],
            "grasas": row[2],
            "carbos": row[3]
        }
    return None

def guardar_comida_bd(plato):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO Comidas
    (ID_Usuario, Nombre_Plato, Calorias, Proteinas, Grasas, Carbos, Fecha_Consumo)
    VALUES (1,?,?,?,?,?,?)
    """, (
        plato['nombre_plato'],
        plato['calorias'],
        plato['proteinas'],
        plato['grasas'],
        plato['carbos'],
        datetime.date.today()
    ))

    conn.commit()
    conn.close()

def leer_progreso_hoy_bd():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT Nombre_Plato, Calorias, Proteinas, Grasas, Carbos
    FROM Comidas
    WHERE Fecha_Consumo = ?
    """, (datetime.date.today(),))

    rows = cursor.fetchall()
    conn.close()

    historial = []
    totales = {"calorias":0,"proteinas":0,"grasas":0,"carbos":0}

    for r in rows:
        historial.append({
            "nombre_plato": r[0],
            "calorias": r[1],
            "proteinas": r[2],
            "grasas": r[3],
            "carbos": r[4]
        })
        totales["calorias"] += r[1]
        totales["proteinas"] += r[2]
        totales["grasas"] += r[3]
        totales["carbos"] += r[4]

    return totales, historial

# =================================================
# SESSION STATE
# =================================================
if "pagina" not in st.session_state:
    st.session_state.pagina = "Inicio"

perfil_db = cargar_perfil_bd()
st.session_state.usuario = perfil_db

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

# =================================================
# FUNCIONES IA
# =================================================
def analizar_comida(image: Image.Image):
    model = genai.GenerativeModel("gemini-1.5-flash-latest")

    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")

    prompt = """
Devuelve SOLO este JSON válido:
{
  "nombre_plato": "string",
  "calorias": number,
  "proteinas": number,
  "grasas": number,
  "carbos": number
}
"""
    response = model.generate_content([
        prompt,
        {"mime_type": "image/jpeg", "data": buffer.getvalue()}
    ])

    return json.loads(response.text.replace("```json","").replace("```",""))

# =================================================
# (EL RESTO DE TU CÓDIGO VISUAL SIGUE EXACTAMENTE IGUAL)
# =================================================
