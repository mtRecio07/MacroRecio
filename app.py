import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="NutriIA Gratis", page_icon="🥑", layout="wide")

# Inicializar memoria (Session State)
if 'usuario' not in st.session_state:
    st.session_state.usuario = None
if 'diario' not in st.session_state:
    st.session_state.diario = {'calorias': 0, 'proteinas': 0, 'grasas': 0, 'carbos': 0, 'historial': []}

# --- BARRA LATERAL ---
st.sidebar.title("🥑 Menú Principal")

# Configuración de API Key (Blindada para Streamlit Secrets)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ Error de Configuración: No se encontró la API Key en los 'Secrets' de Streamlit.")
    st.stop()

menu = st.sidebar.radio("Ir a:", ["🏠 Inicio", "👤 Mi Perfil & Metas", "📸 Escáner de Comida"])

# --- FUNCIÓN: CONSULTAR GEMINI (SOLIDEZ EXTRA) ---
def consultar_gemini_json(prompt, image=None):
    try:
        # Usamos flash por ser rápido y multimodal (texto + imagen)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if image:
            response = model.generate_content([prompt, image])
        else:
            response = model.generate_content(prompt)
        
        # Limpieza y parseo de JSON
        texto_limpio = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(texto_limpio)
    except Exception as e:
        st.error(f"Error conectando con la IA: {e}")
        return None

# =================================================
# 1. PANTALLA DE INICIO
# =================================================
if menu == "🏠 Inicio":
    st.title("Bienvenido a tu Nutricionista de Bolsillo 🥗")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        ### ¿Qué hace esta App?
        1. **Define tus metas:** Calculamos lo que tu cuerpo necesita.
        2. **Saca fotos:** Olvídate de pesar comida, solo tómale una foto.
        3. **Control total:** La IA suma todo y te avisa cuando llegas a tu límite.
        """)
    with col2:
        st.image("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?q=80&w=1000&auto=format&fit=crop", use_column_width=True)
    st.info("👈 Ve a la pestaña 'Mi Perfil' para comenzar.")

# =================================================
# 2. PERFIL DE USUARIO
# =================================================
elif menu == "👤 Mi Perfil & Metas":
    st.header("Configuración Personal")
    with st.form("perfil_form"):
        col1, col2 = st.columns(2)
        with col1:
            genero = st.selectbox("Género", ["Hombre", "Mujer"])
            edad = st.number_input("Edad", 10, 100, 25)
            altura = st.number_input("Altura (cm)", 100, 250, 170)
        with col2:
            peso = st.number_input("Peso (kg)", 30, 200, 70)
            actividad = st.selectbox("Nivel de Actividad", ["Sedentario (Poco o nada)", "Ligero (1-3 días/sem)", "Moderado (3-5 días/sem)", "Activo (6-7 días/sem)", "Muy Activo (Trabajo físico/Atleta)"])
            objetivo = st.selectbox("Objetivo", ["Perder Grasa", "Mantener Peso", "Ganar Músculo", "Recomposición Corporal"])
        
        submit_btn = st.form_submit_button("Calcular Requerimientos")
    
    if submit_btn:
        with st.spinner("La IA está calculando tu plan ideal..."):
            prompt_perfil = f"""
            Actúa como un nutricionista deportivo experto.
            Datos: {genero}, {edad} años, {peso}kg, {altura}cm. Actividad: {actividad}. Objetivo: {objetivo}.
            Calcula macros y agua. Responde SOLO JSON:
            {{ "calorias": int, "proteinas": int, "grasas": int, "carbos": int, "agua_litros": float, "consejo": "string" }}
            """
            datos = consultar_gemini_json(prompt_perfil)
            if datos:
                st.session_state.usuario = datos
                st.success("¡Datos guardados!")

    if st.session_state.usuario:
        u = st.session_state.usuario
        st.divider()
        st.subheader("🎯 Tus Metas Diarias")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Calorías", f"{u['calorias']}")
        c2.metric("Proteínas", f"{u['proteinas']}g")
        c3.metric("Grasas", f"{u['grasas']}g")
        c4.metric("Carbos", f"{u['carbos']}g")

# =================================================
# 3. ESCÁNER
# =================================================
elif menu == "📸 Escáner de Comida":
    st.header("Registro de Comidas")
    
    if not st.session_state.usuario:
        st.warning("⚠️ Primero configura tu perfil.")
        st.stop()
        
    metas = st.session_state.usuario
    actual = st.session_state.diario
    
    # Barras de progreso
    progreso = min(actual['calorias'] / metas['calorias'], 1.0)
    st.progress(progreso, text=f"Calorías: {actual['calorias']} / {metas['calorias']} kcal")
    
    uploaded_file = st.file_uploader("📸 Sube una foto de tu comida", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Foto subida", width=300)
        
        if st.button("➕ Analizar y Agregar"):
            with st.spinner("Analizando plato..."):
                prompt_comida = """
                Analiza esta comida. Responde SOLO JSON estimado:
                {{ "nombre_plato": "string", "calorias": int, "proteinas": int, "grasas": int, "carbos": int, "es_saludable": bool }}
                """
                res = consultar_gemini_json(prompt_comida, image)
                
                if res:
                    st.session_state.diario['calorias'] += res['calorias']
                    st.session_state.diario['proteinas'] += res['proteinas']
                    st.session_state.diario['grasas'] += res['grasas']
                    st.session_state.diario['carbos'] += res['carbos']
                    st.session_state.diario['historial'].append(res)
                    st.success(f"¡Añadido! {res['nombre_plato']}")
                    st.rerun()

    if st.session_state.diario['historial']:
        with st.expander("Historial de hoy"):
            for p in st.session_state.diario['historial']:
                st.write(f"**{p['nombre_plato']}** - {p['calorias']} kcal")
