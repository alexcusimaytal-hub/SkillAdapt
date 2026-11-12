import os
import streamlit as st
from google import genai

# =========================================================
# 1. CONFIGURACIÓN GENERAL Y ENLACES
# =========================================================
st.set_page_config(
    page_title="SkillAdapt | Plataforma de Capacitación Adaptativa",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL de tu Landing Page en Netlify (actualízala cuando Netlify te dé tu enlace)
LANDING_PAGE_URL = "https://tu-proyecto-skilladapt.netlify.app"

# =========================================================
# 2. CARGA DE ESTILOS (ALINEADOS CON LA LANDING PAGE)
# =========================================================
def cargar_estilos():
    rutas_css = [
        "assets/style.css",
        "../assets/style.css",
        "capacitador-ia/assets/style.css"
    ]
    for ruta in rutas_css:
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as archivo:
                st.markdown(f"<style>{archivo.read()}</style>", unsafe_allow_html=True)
            return

    # Respaldo automático con los colores exactos de landing.css
    st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: #0F172A;
        }
        .stApp { background-color: #F8FAFC; }
        .encabezado-app {
            background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
            color: #FFFFFF;
            padding: 2rem 2.5rem;
            border-radius: 14px;
            margin-bottom: 1.5rem;
            border-bottom: 4px solid #2563EB;
        }
        .encabezado-titulo { font-size: 1.9rem; font-weight: 700; margin-bottom: 0.3rem; color: #FFFFFF; }
        .encabezado-subtitulo { font-size: 1rem; color: #CBD5E1; margin-bottom: 1rem; }
        .etiqueta-modulo {
            background-color: #DBEAFE; color: #1D4ED8;
            padding: 5px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;
        }
        .tarjeta-blanca {
            background-color: #FFFFFF; border: 1px solid #E2E8F0;
            border-radius: 12px; padding: 1.4rem; height: 100%;
        }
        .tarjeta-borde-azul {
            background-color: #FFFFFF; border: 1px solid #E2E8F0;
            border-left: 4px solid #2563EB; border-radius: 8px;
            padding: 1rem 1.2rem; margin-bottom: 0.8rem;
        }
        .stButton > button {
            background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1;
            border-radius: 8px; font-weight: 600; padding: 0.6rem 1rem; width: 100%;
        }
        .stButton > button:hover { border-color: #2563EB; color: #2563EB; background-color: #F0F7FF; }
    </style>
    """, unsafe_allow_html=True)

cargar_estilos()

# =========================================================
# 3. LECTURA DE PARÁMETROS DESDE LA LANDING PAGE
# =========================================================
# Permite que los botones de Netlify abran el perfil o diagnóstico correspondiente
parametros_url = st.query_params
perfil_url = parametros_url.get("perfil", "Derecho Digital e IA")
accion_url = parametros_url.get("accion", "")

opciones_especialidad = [
    "Derecho Digital e IA",
    "Administración Robótica",
    "Atención al Cliente Inteligente"
]
indice_inicial = opciones_especialidad.index(perfil_url) if perfil_url in opciones_especialidad else 0

# =========================================================
# 4. GESTIÓN SEGURA DE API KEY Y BARRA LATERAL
# =========================================================
api_key = None
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.getenv("GEMINI_API_KEY")

with st.sidebar:
    # Cargar el logo si existe en la carpeta assets
    for ruta_logo in ["assets/logo.png", "../assets/logo.png"]:
        if os.path.exists(ruta_logo):
            st.image(ruta_logo, width=130)
            break

    st.markdown("### Panel de Control")
    st.caption("Configuración del perfil del estudiante")

    # Enlace para regresar a la Landing Page en Netlify
    st.markdown(f"[← Volver a la página principal]({LANDING_PAGE_URL})")
    st.divider()

    if not api_key:
        clave_ingresada = st.text_input("Clave de API (Gemini):", type="password")
        if clave_ingresada:
            api_key = clave_ingresada.strip()

    # Datos dinámicos del alumno (Memoria del sistema)
    st.markdown("**Datos del Estudiante**")
    nombre_estudiante = st.text_input("Nombre completo:", "Alex Ramos")
    especialidad = st.selectbox("Especialidad:", opciones_especialidad, index=indice_inicial)
    nivel_dominio = st.select_slider(
        "Nivel actual:",
        options=["Principiante (30%)", "Intermedio (70%)", "Avanzado (90%)"],
        value="Intermedio (70%)"
    )

    modulos_aprobados = ["Protección de Datos en IA", "Ética Algorítmica"]
    modulo_actual = "Contratos Inteligentes y Blockchain"

    st.info(f"**Módulo asignado hoy:**\n\n{modulo_actual}")

if not api_key:
    st.warning("Ingrese su clave de API en el panel lateral izquierdo para habilitar el tutor.")
    st.stop()

# =========================================================
# 5. CONEXIÓN CON GEMINI Y DETECCIÓN DE MODELO ACTIVO
# =========================================================
client = genai.Client(api_key=api_key)

def generar_respuesta_ia(cliente, mensaje_usuario: str, instrucciones_sistema: str) -> str:
    """Consulta los modelos disponibles en la cuenta y genera una respuesta estable."""
    modelos_disponibles = []
    try:
        for m in cliente.models.list():
            nombre = m.name.replace("models/", "")
            if "gemini" in nombre and "embed" not in nombre and "imagen" not in nombre:
                modelos_disponibles.append(nombre)
    except Exception:
        pass

    if not modelos_disponibles:
        modelos_disponibles = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]

    ultimo_error = None
    for modelo in modelos_disponibles:
        try:
            respuesta = cliente.models.generate_content(
                model=modelo,
                contents=mensaje_usuario,
                config={"system_instruction": instrucciones_sistema}
            )
            if respuesta and respuesta.text:
                return respuesta.text
        except Exception as error:
            ultimo_error = error
            continue

    raise ultimo_error if ultimo_error else Exception("No se pudo conectar con ningún modelo disponible.")

# Personalidad y reglas pedagógicas formales de SkillBot
INSTRUCCIONES_SKILLBOT = f"""
Eres 'SkillBot', el consultor y tutor especialista en reconversión laboral de la plataforma SkillAdapt.
Tu propósito es preparar a los profesionales para el mercado laboral hacia el año 2050.

PERFIL DEL ESTUDIANTE (Memoria activa):
- Nombre: {nombre_estudiante}
- Especialidad: {especialidad}
- Nivel de competencia: {nivel_dominio}
- Módulos aprobados: {', '.join(modulos_aprobados)}
- Módulo en curso: {modulo_actual}

DIRECTRICES DE COMUNICACIÓN:
1. Mantén un tono ejecutivo, claro, alentador y profesional. Evita el uso excesivo de emojis.
2. Haz referencia al progreso previo del estudiante (módulos aprobados y nivel actual) para demostrar continuidad.
3. Aplica aprendizaje activo: evita explicaciones teóricas extensas y plantea casos prácticos reales de la industria.
4. Si el usuario solicita su plan del día, dale la bienvenida formal, reconoce la aprobación de '{modulos_aprobados[-1]}' y presenta un caso breve sobre '{modulo_actual}'.
5. Finaliza cada intervención con una pregunta de evaluación o tres alternativas de decisión para medir su criterio profesional.
"""

# =========================================================
# 6. INTERFAZ PRINCIPAL DE LA APLICACIÓN
# =========================================================

# Encabezado superior (Hero interno)
st.markdown(f"""
<div class="encabezado-app">
    <div class="encabezado-titulo">SkillAdapt — Entorno de Capacitación Adaptativa</div>
    <div class="encabezado-subtitulo">Desarrollo de competencias estratégicas e inteligencia artificial hacia el 2050</div>
    <span class="etiqueta-modulo">Módulo Activo: {modulo_actual}</span>
</div>
""", unsafe_allow_html=True)

# Sección de Perfil y Metodología
col_perfil, col_valor = st.columns([1, 1])

with col_perfil:
    st.markdown("#### Perfil de Aprendizaje")
    st.markdown(f"""
    <div class="tarjeta-blanca">
        <p style="margin-bottom:8px;"><strong>Estudiante:</strong> {nombre_estudiante}</p>
        <p style="margin-bottom:8px;"><strong>Especialidad:</strong> {especialidad}</p>
        <p style="margin-bottom:8px;"><strong>Nivel alcanzado:</strong> <span style="color:#2563EB; font-weight:700;">{nivel_dominio}</span></p>
        <p style="margin-bottom:0;"><strong>Módulos aprobados:</strong> {', '.join(modulos_aprobados)}</p>
    </div>
    """, unsafe_allow_html=True)

with col_valor:
    st.markdown("#### Metodología SkillAdapt")
    st.markdown("""
    <div class="tarjeta-borde-azul">
        <strong>Rutas personalizadas:</strong> Formación enfocada exclusivamente en cerrar brechas técnicas reales sin teoría redundante.
    </div>
    <div class="tarjeta-borde-azul">
        <strong>Diagnóstico de automatización:</strong> Evaluación continua de tareas operativas frente a tecnologías emergentes.
    </div>
    """, unsafe_allow_html=True)

st.divider()

# =========================================================
# 7. MÓDULO DE TUTORÍA INTERACTIVA (SKILLBOT)
# =========================================================
st.markdown("#### Tutor Virtual: SkillBot")

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

consulta_pendiente = None

# Si el usuario viene desde el botón "Iniciar Diagnóstico Gratuito" de Netlify
if accion_url == "diagnostico" and "diagnostico_ejecutado" not in st.session_state:
    st.session_state.diagnostico_ejecutado = True
    consulta_pendiente = (
        f"Hola SkillBot. Vengo desde la página principal para realizar mi diagnóstico de riesgo "
        f"de automatización en mi especialidad de {especialidad}."
    )

# Botones de acceso rápido cuando el chat está vacío
if len(st.session_state.mensajes) == 0 and not consulta_pendiente:
    st.caption("Seleccione una opción para iniciar la sesión o escriba su consulta en la barra inferior:")
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Consultar plan de hoy", key="btn_plan"):
            consulta_pendiente = "Hola SkillBot, ¿qué tema y caso práctico me corresponde desarrollar hoy según mi avance?"
    with c2:
        if st.button("Evaluar riesgo de automatización", key="btn_riesgo"):
            consulta_pendiente = "Realiza un diagnóstico breve sobre qué tareas de mi especialidad tienen mayor riesgo de automatización hacia el 2050."
    with c3:
        if st.button("Iniciar caso práctico", key="btn_caso"):
            consulta_pendiente = f"Plantéame un caso práctico ejecutivo sobre {modulo_actual} con 3 alternativas de solución."

# Entrada de texto libre del usuario
texto_usuario = st.chat_input("Escriba su consulta o respuesta al caso práctico...")
if texto_usuario:
    consulta_pendiente = texto_usuario

# Mostrar historial de conversación
for msg in st.session_state.mensajes:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Procesar envío y generar respuesta
if consulta_pendiente:
    st.session_state.mensajes.append({"role": "user", "content": consulta_pendiente})
    with st.chat_message("user"):
        st.markdown(consulta_pendiente)

    with st.chat_message("assistant"):
        with st.spinner("Analizando perfil y preparando respuesta..."):
            try:
                respuesta_texto = generar_respuesta_ia(client, consulta_pendiente, INSTRUCCIONES_SKILLBOT)
                st.markdown(respuesta_texto)
                st.session_state.mensajes.append({"role": "assistant", "content": respuesta_texto})
                st.rerun()
            except Exception as e:
                st.error(f"No se pudo completar la consulta con el servicio de IA: {e}")