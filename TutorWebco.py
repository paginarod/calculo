import streamlit as st
from groq import Groq
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64
import easyocr
import numpy as np
from PIL import Image

# 1. Configuración de la página
st.set_page_config(page_title="Asistente de Cálculo 🤓", page_icon="🤓", layout="centered")

# 2. Conexión segura con Groq
API_KEY = st.secrets["GROQ_API_KEY"]

@st.cache_resource
def inicializar_ia():
    return Groq(api_key=API_KEY)

@st.cache_resource
def inicializar_lector():
    return easyocr.Reader(['es', 'en'], gpu=False)

client = inicializar_ia()
reader = inicializar_lector()

st.title("🤖 Asistente Virtual de Cálculo Inteligente")
st.markdown("---")

# 3. Carga de la biblioteca
@st.cache_data
def cargar_conocimiento():
    try:
        with open("cerebro_tutor.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

texto_contexto = cargar_conocimiento()

audio_bytes = None
pregunta_usuario = None
texto_extraido_imagen = ""

# 4. Panel lateral (Ahora solo para el estado de la biblioteca)
with st.sidebar:
    st.header("Universidad Mariano Galvez")
    if texto_contexto:
        st.success("✅ PRIMER COMPAÑERO ")
        st.success("✅ SEGUNDO COMPAÑERO ")
        st.success("✅ Hector Eduardo Rodriguez Sis 2990-18-4883 ")
        st.success("✅ CUARTO COMPAÑERO ")
        st.success("✅ QUINTO COMPAÑERO ")

    else:
        st.error("❌ No se encontró el archivo 'cerebro_tutor.txt'.")

# 5. Memoria del chat en pantalla
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy un experto en cálculo. Puedes escribirme aquí abajo, presionar el micrófono para hablar o subir una foto de tu ejercicio."}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

st.markdown("---")

# 6 y 7. Zona de entrada unificada (Abajo en la pantalla principal)
# Creamos 3 columnas: una pequeña para audio, una pequeña para foto, y una grande para texto
col_audio, col_foto, col_texto = st.columns([1, 1, 5], vertical_alignment="bottom")

with col_audio:
    audio_bytes = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#3498db", icon_size="2x")

with col_foto:
    # Usamos un cargador compacto limitando el espacio visual
    imagen_subida = st.file_uploader("📷", type=["png", "jpg", "jpeg"], label_visibility="collapsed")

with col_texto:
    texto_input = st.chat_input("Escribe tu duda o ejercicio aquí...")

# Muestra un resumen de la imagen si se subió una
if imagen_subida:
    st.info("📸 Imagen cargada listo para procesar.")
    with st.spinner("Leyendo el problema matemático de la imagen... 🔍"):
        try:
            image = Image.open(imagen_subida)
            img_np = np.array(image)
            resultados = reader.readtext(img_np, detail=0)
            if resultados:
                texto_extraido_imagen = " ".join(resultados)
        except Exception as e:
            st.warning(f"Nota del lector visual: {e}")

# Procesamiento de audio
if audio_bytes:
    if "ultimo_audio" not in st.session_state:
        st.session_state["ultimo_audio"] = None
    
    if audio_bytes != st.session_state["ultimo_audio"]:
        st.session_state["ultimo_audio"] = audio_bytes
        with st.spinner("Transcribiendo voz... 🎧"):
            try:
                transcripcion = client.audio.transcriptions.create(
                    file=("audio.wav", audio_bytes), model="whisper-large-v3", language="es"
                )
                pregunta_usuario = transcripcion.text
            except Exception as e:
                st.error("Error de audio: " + str(e))

# Asignar texto de la barra si existe
if texto_input:
    pregunta_usuario = texto_input

# 8. Combinar texto e imagen de forma segura
if texto_extraido_imagen and not pregunta_usuario:
    if "img_leida" not in st.session_state or st.session_state.get("ultima_img") != texto_extraido_imagen:
        pregunta_usuario = f"Resuelve paso a paso el siguiente ejercicio extraído de la imagen: {texto_extraido_imagen}"
        st.session_state["img_leida"] = True
        st.session_state["ultima_img"] = texto_extraido_imagen

# 9. Motor de procesamiento principal
if pregunta_usuario:
    st.session_state.messages.append({"role": "user", "content": pregunta_usuario})
    with st.chat_message("user"):
        st.write(pregunta_usuario)

    with st.chat_message("assistant"):
        with st.spinner("Resolviendo... 🧠"):
            try:
                contexto_recortado = ""
                if texto_contexto:
                    palabras_clave = [p.lower() for p in pregunta_usuario.split() if len(p) > 4]
                    lineas = texto_contexto.split('\n')
                    fragmentos_encontrados = []
                    for linea in lineas:
                        if any(kw in linea.lower() for kw in palabras_clave):
                            fragmentos_encontrados.append(linea)
                        if len('\n'.join(fragmentos_encontrados)) > 6000:
                            break
                    contexto_recortado = '\n'.join(fragmentos_encontrados)
                    if not contexto_recortado:
                        contexto_recortado = texto_contexto[:6000]

                prompt_sistema = (
                    "Eres un profesor de cálculo universitario experto, sumamente paciente y con perfecta ortografía.\n"
                    "Es un requerimiento MANDATORIO que uses formato LaTeX para envolver CUALQUIER fórmula matemática o variable. "
                    "Usa $ para fórmulas en línea y $$ para ecuaciones centradas independientes.\n\n"
                    f"Utiliza este contexto extraído de sus libros cargados para responder si es relevante:\n{contexto_recortado}"
                )

                respuesta_api = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": pregunta_usuario}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.3
                )

                texto_tutor = respuesta_api.choices[0].message.content
                st.write(texto_tutor)
                st.session_state.messages.append({"role": "assistant", "content": texto_tutor})

                # Generar audio
                texto_limpio_para_leer = texto_tutor.replace('*', '').replace('$', ' ').replace('#', '')
                tts = gTTS(text=texto_limpio_para_leer, lang='es', tld='com.mx')
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                st.session_state["audio_reproducir"] = audio_buffer.getvalue()

            except Exception as e:
                st.error(f"❌ Error en el procesamiento: {e}")

# 10. Reproducción del audio
if "audio_reproducir" in st.session_state and st.session_state["audio_reproducir"]:
    st.audio(st.session_state["audio_reproducir"], format="audio/mp3", autoplay=True)
    st.session_state["audio_reproducir"] = None
