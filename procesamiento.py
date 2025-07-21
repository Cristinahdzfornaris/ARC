
import requests
import json
import time
import re
import fitz  
import pandas as pd
import streamlit as st
import google.generativeai as genai
from google.api_core import exceptions

# --- FUNCIÓN PARA LM STUDIO
def extraer_info_con_lmstudio(texto_articulo, id_articulo, max_reintentos=2):
    """Usa un servidor local de LM Studio para la extracción."""
    st.info(f"Enviando '{id_articulo}' al modelo local. Esto puede tardar...")
    texto_contexto = texto_articulo.encode('utf-8', 'ignore').decode('utf-8')[:8000] 
    
    url = "http://localhost:1234/v1/chat/completions"
    headers = {"Content-Type": "application/json"}

    prompt = f"""
    Analiza el siguiente texto de un documento académico. Tu tarea es extraer la información en un formato JSON estricto.
    Reglas:
    1.  **titulo**: El título del artículo. Si no lo encuentras, usa el ID del artículo. String.
    2.  **autores**: Lista de strings con los nombres completos de los autores. Lista.
    3.  **afiliaciones**: Lista de strings con las afiliaciones únicas (universidades, etc.). Lista.
    4.  **palabras_clave**: Lista de strings con las palabras clave ('Keywords'). Si no hay, lista vacía.
    5.  **tematica**: Un string corto (2-5 palabras) resumiendo la temática. String.
    6.  **referencias**: Lista de strings. Cada string debe ser UNA referencia COMPLETA de la bibliografía.

    Tu respuesta DEBE SER ÚNICAMENTE UN OBJETO JSON VÁLIDO. No incluyas explicaciones.
    
    ID del Artículo: {id_articulo}
    TEXTO DEL ARTÍCULO:
    ---
    {texto_contexto}
    ---
    """

    payload = {
        "model": "local-model",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 4096, 
    }

    for intento in range(max_reintentos):
        try:
            
            response = requests.post(url, headers=headers, json=payload, timeout=180)
            
            
            response.raise_for_status()

            response_data = response.json()
            json_string = response_data['choices'][0]['message']['content']

            match = re.search(r'\{.*\}', json_string, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            else:
                raise ValueError("La respuesta del modelo local no contenía un JSON reconocible.")
        except requests.exceptions.RequestException as e:
            
            st.error(f"Error de conexión con LM Studio. ¿Está el servidor encendido y el n_ctx configurado? Error: {e}")
            return None
        except Exception as e:
            st.warning(f"Error en el intento {intento + 1} con LM Studio: {type(e).__name__}. Reintentando...")
            time.sleep(3)
    
    st.error(f"Falló la extracción para '{id_articulo}' con LM Studio después de {max_reintentos} intentos.")
    return None

# FUNCIÓN PARA GOOGLE GEMINI 
def extraer_info_con_gemini(texto_articulo, id_articulo, max_reintentos=3):
    """Usa la API de Google Gemini con reintentos inteligentes."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
    except (KeyError, FileNotFoundError):
        st.error("Error Crítico: La clave de API de Google no se encontró.")
        return None

    texto_contexto = texto_articulo.encode('utf-8', 'ignore').decode('utf-8')[:25000]
    generation_config = {"response_mime_type": "application/json"}
    model = genai.GenerativeModel("gemini-1.5-flash-latest", generation_config=generation_config)
    prompt = f"""
    Analiza el siguiente texto de un documento académico. Tu tarea es extraer la información en un formato JSON estricto.
    Reglas:
    1.  **titulo**: El título del artículo. Si no lo encuentras, usa el ID del artículo. String.
    2.  **autores**: Lista de strings con los nombres completos de los autores. Lista.
    3.  **afiliaciones**: Lista de strings con las afiliaciones únicas (universidades, etc.). Lista.
    4.  **palabras_clave**: Lista de strings con las palabras clave ('Keywords'). Si no hay, lista vacía.
    5.  **tematica**: Un string corto (2-5 palabras) resumiendo la temática. String.
    6.  **referencias**: Lista de strings. Cada string debe ser UNA referencia COMPLETA de la bibliografía.

    Tu respuesta DEBE SER ÚNICAMENTE UN OBJETO JSON VÁLIDO. No incluyas explicaciones.
    
    ID del Artículo: {id_articulo}
    TEXTO DEL ARTÍCULO:
    ---
    {texto_contexto}
    ---
    """

    for intento in range(max_reintentos):
        try:
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except exceptions.ResourceExhausted as e:
            pausa = 5 * (2 ** intento)
            st.warning(f"Límite de cuota de Gemini alcanzado. Esperando {pausa}s...")
            time.sleep(pausa)
        except Exception as e:
            st.error(f"Error inesperado con Gemini: {e}")
            return None
    st.error(f"Falló la extracción para '{id_articulo}' con Gemini por exceso de cuota.")
    return None

# --- FUNCIÓN PRINCIPAL DE PROCESAMIENTO ---
def procesar_archivos_pdf(archivos_subidos, motor_seleccionado):
    """Enruta el procesamiento al motor de IA correcto."""
    resultados = []
    total_archivos = len(archivos_subidos)
    progreso = st.progress(0, text="Iniciando procesamiento...")

    for i, archivo in enumerate(archivos_subidos):
        id_articulo = archivo.name.replace('.pdf', '')
        progreso.progress((i + 1) / total_archivos, text=f"Procesando: {id_articulo}")
        
        try:
            with fitz.open(stream=archivo.read(), filetype="pdf") as doc:
                texto_completo = "".join(page.get_text() for page in doc)
            
            info_extraida = None
            if motor_seleccionado == "LM Studio (Local)":
                info_extraida = extraer_info_con_lmstudio(texto_completo, id_articulo)
            elif motor_seleccionado == "Google Gemini":
                info_extraida = extraer_info_con_gemini(texto_completo, id_articulo)
            
            if info_extraida:
                info_extraida['id_articulo'] = id_articulo
                resultados.append(info_extraida)
                st.success(f"-> ¡Éxito en la extracción de {id_articulo}!")
            else:
                 st.warning(f"-> No se pudo extraer información de {id_articulo}.")
        except Exception as e:
            st.error(f"No se pudo procesar el PDF {archivo.name}. Error: {e}")

    return pd.DataFrame(resultados)