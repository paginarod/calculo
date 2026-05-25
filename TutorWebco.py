# ... (Todo tu código anterior se mantiene igual arriba)

# MOTOR DE PROCESAMIENTO
if pregunta_usuario:
    st.session_state.messages.append({"role": "user", "content": pregunta_usuario})
    with st.chat_message("user"):
        st.write(pregunta_usuario)

    with st.chat_message("assistant"):
        with st.spinner("Analizando tus datos y resolviendo... 🧠"):
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
                    model="llama-3.2-11b-vision-preview",
                    temperature=0.3
                )

                texto_tutor = respuesta_api.choices[0].message.content
                st.write(texto_tutor)
                st.session_state.messages.append({"role": "assistant", "content": texto_tutor})

                # --- FIX PARA EL ERROR REMOVECHILD ---
                # Generamos el audio pero lo guardamos en el estado antes de renderizarlo directamente
                texto_limpio_para_leer = texto_tutor.replace('*', '').replace('$', ' ').replace('#', '')
                tts = gTTS(text=texto_limpio_para_leer, lang='es', tld='com.mx')
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                
                # Almacenamos los bytes en el session_state para evitar que el renderizado rompa el DOM
                st.session_state["audio_reproducir"] = audio_buffer.getvalue()

            except Exception as e:
                st.error(f"❌ Error en el procesamiento: {e}")

# Modificación aquí: El reproductor se ejecuta fuera del bloque del spinner de forma segura
if "audio_reproducir" in st.session_state and st.session_state["audio_reproducir"]:
    st.audio(st.session_state["audio_reproducir"], format="audio/mp3", autoplay=True)
    # Limpiamos el estado para que no se cicle infinitamente
    st.session_state["audio_reproducir"] = None
