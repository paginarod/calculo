import streamlit as st
from groq import Groq
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io

st.set_page_config(page_title="Asistente de Cálculo Inteligente 🤓", page_icon="🤓", layout="centered")

# CONEXIÓN SEGURA: Ahora el programa busca la clave oculta de los "Secrets" de Streamlit
API_KEY = st.secrets["GROQ_API_KEY"]

@st.cache_resource
def inicializar_ia():
    return Groq(api_key=API_KEY)

client = inicializar_ia()

st.title("🤖 Asistente Virtual de Cálculo Inteligente")
st.markdown("---")

# CARGA INSTANTÁNEA DEL CEREBRO PRE-PROCESADO
@st.cache_data
def cargar_conocimiento():
    try:
        with open("cerebro_tutor.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

texto_contexto = cargar_conocimiento()

# PANEL LATERAL (Ajustado según tus indicaciones exactas)
with st.sidebar:
    st.header("📚 Biblioteca Personal")
    if texto_contexto:
        st.success("✅ Biblioteca cargada y lista")
    else:
        st.error("❌ No se encontró el archivo 'cerebro_tutor.txt'. Ejecuta EntrenarCerebro.py primero.")

    st.markdown("---")
    st.header("⚙️ Opciones")
    if st.button("🔗 Compartir esta aplicación"):
        st.info("¡Enlace copiado al portapapeles! Reenvíaselo a tus compañeros. 🚀")

# MEMORIA DEL CHAT CON EL MENSAJE ACTUALIZADO ("como tu prefieras")
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy un experto en cálculo. Dime tus dudas y yo las resuelvo. Puedes escribir o hablar como tu prefieras, estoy atento a tu respuesta."}
    ]

# Muestra los chats diferenciados por colores/iconos automáticamente sin poner nombres de roles
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

pregunta_usuario = None

# ZONA DE ENTRADA (Micrófono limpio colocado al lado de la barra de escritura)
st.markdown("---")
col1, col2, col3 = st.columns([8, 1, 1])
with col3:
    audio_bytes = audio_recorder(text="", recording_color="#e74c3c", neutral_color="#3498db", icon_size="2x")

if audio_bytes and "ultimo_audio" not in st.session_state:
    st.session_state["ultimo_audio"] = None

if audio_bytes and audio_bytes != st.session_state.get("ultimo_audio"):
    st.session_state["ultimo_audio"] = audio_bytes
    with st.spinner("Escuchando tu voz... 🎧"):
        try:
            transcripcion = client.audio.transcriptions.create(
                file=("audio.wav", audio_bytes), model="whisper-large-v3", language="es"
            )
            pregunta_usuario = transcripcion.text
        except Exception as e:
            st.error("Error al transcribir el audio: " + str(e))

# Barra de texto flotante nativa abajo
if texto_input := st.chat_input("Escribe tu duda o ejercicio aquí..."):
    pregunta_usuario = texto_input

# MOTOR DE PROCESAMIENTO
if pregunta_usuario:
    st.session_state.messages.append({"role": "user", "content": pregunta_usuario})
    with st.chat_message("user"):
        st.write(pregunta_usuario)

    with st.chat_message("assistant"):
        with st.spinner("Analizando tu biblioteca y resolviendo... 🧠"):
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
                    model="llama-3.1-8b-instant",
                    temperature=0.3
                )

                texto_tutor = respuesta_api.choices[0].message.content
                st.write(texto_tutor)
                st.session_state.messages.append({"role": "assistant", "content": texto_tutor})

                texto_limpio_para_leer = texto_tutor.replace('*', '').replace('$', ' ').replace('#', '')
                tts = gTTS(text=texto_limpio_para_leer, lang='es', tld='com.mx')
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                
                st.audio(audio_buffer, format="audio/mp3", autoplay=True)

            except Exception as e:
                st.error(f"❌ Error en el procesamiento: {e}")