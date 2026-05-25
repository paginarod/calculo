import streamlit as st
from groq import Groq
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# 1. Configuración de la página
st.set_page_config(page_title="Asistente de Cálculo Inteligente 🤓", page_icon="🤓", layout="centered")

# 2. Conexión segura con Groq
API_KEY = st.secrets["GROQ_API_KEY"]

@st.cache_resource
def inicializar_ia():
    return Groq(api_key=API_KEY)

client = inicializar_ia()

def codificar_imagen(imagen_bytes):
    return base64.b64encode(imagen_bytes).decode('utf-8')

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

# Inicialización de variables globales del ciclo
audio_bytes = None
pregunta_usuario = None

# 4. Panel lateral (Aislamos el micrófono y el uploader aquí)
with st.sidebar:
    st.header("📚 Biblioteca Personal")
    if texto_contexto:
        st.success("✅ Biblioteca cargada y lista")
    else:
        st.error("❌ No se encontró el archivo 'cerebro_tutor.txt'.")

    st.markdown("---")
    st.header("🎤 Preguntar por Voz")
    audio_bytes = audio_recorder(text="Toca para hablar", recording_color="#e74c3c", neutral_color="#3498db", icon_size="2x")

    st.markdown("---")
    st.header("📸 Subir Ejercicio")
    imagen_subida = st.file_uploader("Sube la foto de tu problema", type=["png", "jpg", "jpeg"])
    if imagen_subida:
        st.image(imagen_subida, caption="Imagen cargada", use_container_width=True)

# 5. Memoria del chat en pantalla
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy un experto en cálculo. Puedes escribirme abajo, usar el micrófono de la izquierda o subir una imagen de tus problemas matemáticos."}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 6. Procesamiento de la entrada de audio si existe
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

# 7. Barra de texto flotante abajo en la pantalla principal
if texto_input := st.chat_input("Escribe tu duda o ejercicio aquí..."):
    pregunta_usuario = texto_input

# 8. Activación automática por pura imagen si no hay texto
if imagen_subida and not pregunta_usuario and "imagen_procesada" not in st.session_state:
    pregunta_usuario = "Por favor, resuelve y explícame el ejercicio matemático que aparece en esta imagen."
    st.session_state["imagen_procesada"] = True
elif not imagen_subida and "imagen_procesada" in st.session_state:
    del st.session_state["imagen_procesada"]

# 9. Motor de procesamiento principal de la Inteligencia Artificial
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

                contenido_mensaje = [{"type": "text", "text": pregunta_usuario}]

                if imagen_subida:
                    bytes_img = imagen_subida.getvalue()
                    base64_image = codificar_imagen(bytes_img)
                    contenido_mensaje.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    })

                respuesta_api = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": contenido_mensaje}
                    ],
                    model="llama-3.2-11b-vision",
                    temperature=0.3
                )

                texto_tutor = respuesta_api.choices[0].message.content
                st.write(texto_tutor)
                st.session_state.messages.append({"role": "assistant", "content": texto_tutor})

                # Generar audio en memoria limpia
                texto_limpio_para_leer = texto_tutor.replace('*', '').replace('$', ' ').replace('#', '')
                tts = gTTS(text=texto_limpio_para_leer, lang='es', tld='com.mx')
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                st.session_state["audio_reproducir"] = audio_buffer.getvalue()

            except Exception as e:
                st.error(f"❌ Error en el procesamiento: {e}")

# 10. Reproducción segura del audio al final para evitar errores en el navegador
if "audio_reproducir" in st.session_state and st.session_state["audio_reproducir"]:
    st.audio(st.session_state["audio_reproducir"], format="audio/mp3", autoplay=True)
    st.session_state["audio_reproducir"] = None
