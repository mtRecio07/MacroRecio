import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="NutriIA Gratis", page_icon="🥑", layout="wide")

# Inicializar memoria (Session State) para guardar datos mientras la app está abierta
if 'usuario' not in st.session_state:
    st.session_state.usuario = None # Aquí guardaremos las metas (calorías, proteínas, etc)
if 'diario' not in st.session_state:
    st.session_state.diario = {'calorias': 0, 'proteinas': 0, 'grasas': 0, 'carbos': 0, 'historial': []}

# --- BARRA LATERAL (NAVEGACIÓN) ---
st.sidebar.title("🥑 Menú Principal")
# API Key (Idealmente esto va en secrets, pero lo dejamos aquí para tu prueba)
# Intenta obtener la clave de los "Secretos" (Configuración en la Nube)
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    # Si no encuentra el secreto (por ejemplo, probando en tu PC), muestra la cajita
    api_key = st.sidebar.text_input("Tu Google API Key:", type="password")
    
menu = st.sidebar.radio("Ir a:", ["🏠 Inicio", "👤 Mi Perfil & Metas", "📸 Escáner de Comida"])

if api_key:
    genai.configure(api_key=api_key)

# --- FUNCIÓN AUXILIAR: LLAMAR A GEMINI CON FORMATO JSON ---
def consultar_gemini_json(prompt, image=None):
    try:
        model = genai.GenerativeModel('gemini-pro')
        if image:
            response = model.generate_content([prompt, image])
        else:
            response = model.generate_content(prompt)
        
        # Limpieza básica para asegurar que sea JSON
        texto_limpio = response.text.replace("```json", "").replace("```", "")
        return json.loads(texto_limpio)
    except Exception as e:
        st.error(f"Error en la IA: {e}")
        return None

# =================================================
# 1. PANTALLA DE INICIO (EDUCACIÓN)
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
        
        > *"Que tu medicina sea tu alimento, y el alimento tu medicina."*
        """)
    
    with col2:
        # Puedes cambiar estas URLs por fotos reales que tengas
        st.image("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?q=80&w=1000&auto=format&fit=crop", caption="Comer sano es vivir mejor", use_column_width=True)

    st.info("👈 Ve a la pestaña 'Mi Perfil' para comenzar.")

# =================================================
# 2. PERFIL DE USUARIO (CÁLCULO DE METAS)
# =================================================
elif menu == "👤 Mi Perfil & Metas":
    st.header("Configuración Personal")
    
    with st.form("perfil_form"):
        col1, col2 = st.columns(2)
        with col1:
            genero = st.selectbox("Género", ["Hombre", "Mujer"])
            edad = st.number_input("Edad", min_value=10, max_value=100, value=25)
            altura = st.number_input("Altura (cm)", min_value=100, max_value=250, value=170)
        with col2:
            peso = st.number_input("Peso (kg)", min_value=30, max_value=200, value=70)
            actividad = st.selectbox("Nivel de Actividad", ["Sedentario (Poco o nada)", "Ligero (1-3 días/sem)", "Moderado (3-5 días/sem)", "Activo (6-7 días/sem)", "Muy Activo (Trabajo físico/Atleta)"])
            objetivo = st.selectbox("Objetivo", ["Perder Grasa", "Mantener Peso", "Ganar Músculo", "Recomposición Corporal"])
        
        submit_btn = st.form_submit_button("Calcular Requerimientos")
    
    if submit_btn and api_key:
        with st.spinner("La IA está calculando tu plan ideal..."):
            prompt_perfil = f"""
            Actúa como un nutricionista deportivo experto.
            Datos del paciente: {genero}, {edad} años, {peso}kg, {altura}cm.
            Nivel de actividad: {actividad}.
            Objetivo: {objetivo}.
            
            Calcula sus macros diarios y agua recomendada.
            Responde SOLO con un objeto JSON (sin texto extra) con esta estructura exacta:
            {{
                "calorias": (numero entero),
                "proteinas": (numero entero en gramos),
                "grasas": (numero entero en gramos),
                "carbos": (numero entero en gramos),
                "agua_litros": (numero flotante),
                "consejo": "Una frase corta motivacional"
            }}
            """
            datos_calculados = consultar_gemini_json(prompt_perfil)
            
            if datos_calculados:
                st.session_state.usuario = datos_calculados
                st.success("¡Cálculo completado! Tus metas se han guardado.")

    # Mostrar resultados si ya existen
    if st.session_state.usuario:
        u = st.session_state.usuario
        st.divider()
        st.subheader("🎯 Tus Metas Diarias")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Calorías", f"{u['calorias']} kcal")
        c2.metric("Proteínas", f"{u['proteinas']} g")
        c3.metric("Grasas", f"{u['grasas']} g")
        c4.metric("Carbohidratos", f"{u['carbos']} g")
        st.info(f"💧 Meta de agua: {u['agua_litros']} Litros diarios. Consejo: {u['consejo']}")

# =================================================
# 3. ESCÁNER Y SEGUIMIENTO (TRACKING)
# =================================================
elif menu == "📸 Escáner de Comida":
    st.header("Registro de Comidas")
    
    if not st.session_state.usuario:
        st.warning("⚠️ Primero debes configurar tu perfil en la sección anterior para tener metas.")
        st.stop()
        
    metas = st.session_state.usuario
    actual = st.session_state.diario
    
    # --- BARRA DE PROGRESO ---
    st.subheader("Tu progreso hoy:")
    
    # Calorías
    col_prog1, col_prog2 = st.columns([3, 1])
    progreso_cal = min(actual['calorias'] / metas['calorias'], 1.0)
    col_prog1.progress(progreso_cal, text=f"Calorías: {actual['calorias']} / {metas['calorias']} kcal")
    
    # Alertas de estado
    if actual['calorias'] > metas['calorias']:
        col_prog2.error("¡Excedido!")
    elif actual['calorias'] >= metas['calorias'] * 0.9:
        col_prog2.success("¡Meta cumplida!")
    else:
        col_prog2.info("Falta comer")

    # Macros detallados
    c1, c2, c3 = st.columns(3)
    c1.metric("Proteínas", f"{actual['proteinas']}/{metas['proteinas']}g", delta=metas['proteinas']-actual['proteinas'], delta_color="normal")
    c2.metric("Grasas", f"{actual['grasas']}/{metas['grasas']}g", delta=metas['grasas']-actual['grasas'], delta_color="normal")
    c3.metric("Carbos", f"{actual['carbos']}/{metas['carbos']}g", delta=metas['carbos']-actual['carbos'], delta_color="normal")

    st.divider()

    # --- CÁMARA ---
    uploaded_file = st.file_uploader("📸 Sube una foto de tu comida", type=["jpg", "jpeg", "png"])
    
    if uploaded_file and api_key:
        image = Image.open(uploaded_file)
        st.image(image, caption="Analizando...", width=300)
        
        if st.button("➕ Agregar esta comida a mi día"):
            with st.spinner("Analizando ingredientes..."):
                prompt_comida = """
                Analiza esta imagen de comida. Estima los valores nutricionales totales del plato.
                Responde SOLO con un objeto JSON con esta estructura exacta (usa valores enteros estimados):
                {
                    "nombre_plato": "Nombre corto del plato",
                    "calorias": (numero entero),
                    "proteinas": (numero entero),
                    "grasas": (numero entero),
                    "carbos": (numero entero),
                    "es_saludable": (true/false)
                }
                """
                resultado_comida = consultar_gemini_json(prompt_comida, image)
                
                if resultado_comida:
                    # Actualizar estado (Sumar)
                    st.session_state.diario['calorias'] += resultado_comida['calorias']
                    st.session_state.diario['proteinas'] += resultado_comida['proteinas']
                    st.session_state.diario['grasas'] += resultado_comida['grasas']
                    st.session_state.diario['carbos'] += resultado_comida['carbos']
                    st.session_state.diario['historial'].append(resultado_comida)
                    
                    st.success(f"¡Añadido! {resultado_comida['nombre_plato']} ({resultado_comida['calorias']} kcal)")
                    st.rerun() # Recargar página para actualizar barras

    # --- HISTORIAL DEL DÍA ---
    if st.session_state.diario['historial']:
        with st.expander("Ver historial de comidas de hoy"):
            for plato in st.session_state.diario['historial']:

                st.write(f"- **{plato['nombre_plato']}**: {plato['calorias']} kcal (P: {plato['proteinas']}g | G: {plato['grasas']}g | C: {plato['carbos']}g)")
