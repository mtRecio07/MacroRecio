import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import datetime
import io
import sqlite3
import os

# =================================================
# CONFIG
# =================================================
st.set_page_config(
    page_title="MacroRecioIA",
    page_icon="💪",
    layout="wide"
)

# =================================================
# SQLITE (REEMPLAZO SQL SERVER – SOLO LÓGICA BD)
# =================================================
DB_PATH = "database/macrorecio.db"

def get_db_connection():
    os.makedirs("database", exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
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

    cur.execute("""
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
# FUNCIONES BD (MISMO COMPORTAMIENTO, SQLITE)
# =================================================
def guardar_perfil_bd(datos):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM Usuarios WHERE ID_Usuario = 1")
    existe = cur.fetchone()[0]

    if existe == 0:
        cur.execute("""
        INSERT INTO Usuarios VALUES
        (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos['genero'], datos['edad'], datos['peso'], datos['altura'],
            datos['actividad'], datos['objetivo'],
            datos['calorias'], datos['proteinas'],
            datos['grasas'], datos['carbos']
        ))
    else:
        cur.execute("""
        UPDATE Usuarios SET
        Genero=?, Edad=?, Peso=?, Altura=?, Actividad=?, Objetivo=?,
        Meta_Calorias=?, Meta_Proteinas=?, Meta_Grasas=?, Meta_Carbos=?
        WHERE ID_Usuario = 1
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
    cur = conn.cursor()

    cur.execute("""
    SELECT Meta_Calorias, Meta_Proteinas, Meta_Grasas, Meta_Carbos
    FROM Usuarios WHERE ID_Usuario = 1
    """)
    row = cur.fetchone()
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
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO Comidas
    (ID_Usuario, Nombre_Plato, Calorias, Proteinas, Grasas, Carbos, Fecha_Consumo)
    VALUES (1, ?, ?, ?, ?, ?, DATE('now'))
    """, (
        plato['nombre_plato'],
        plato['calorias'],
        plato['proteinas'],
        plato['grasas'],
        plato['carbos']
    ))

    conn.commit()
    conn.close()

def leer_progreso_hoy_bd():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT Nombre_Plato, Calorias, Proteinas, Grasas, Carbos
    FROM Comidas
    WHERE Fecha_Consumo = DATE('now') AND ID_Usuario = 1
    """)

    rows = cur.fetchall()
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
# ESTILOS PREMIUM (ORIGINAL – SIN TOCAR)
# =================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f172a, #020617); color: #f8fafc; }
[data-testid="stSidebar"] { background: #020617; border-right: 1px solid rgba(255,255,255,0.05); }
.stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #10B981, #059669);
    color: white;
    border-radius: 12px;
    padding: 12px;
    font-weight: 600;
    border: none;
    margin-top: 6px;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #34D399, #10B981);
}
.card {
    background: rgba(30,41,59,0.65);
    border-radius: 18px;
    padding: 26px;
    margin-bottom: 22px;
    border: 1px solid rgba(255,255,255,0.05);
}
[data-testid="stMetric"] {
    background: rgba(30,41,59,0.6);
    padding: 16px;
    border-radius: 14px;
    text-align: center;
}
.stProgress > div > div > div > div { background-color: #10B981; }
img { border-radius: 16px; }
</style>
""", unsafe_allow_html=True)

# =================================================
# SESSION STATE (IGUAL)
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
# GEMINI (IGUAL)
# =================================================
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
