import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import requests
import xml.etree.ElementTree as ET

st.set_page_config(page_title="DarkNews v7.6", layout="wide")

st.title("🏆 Gerador DarkNews Pro")
st.markdown("---")

# Barra Lateral
st.sidebar.header("Configurações")
api_key_env = st.secrets.get("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input("Gemini API Key:", value=api_key_env, type="password")

# --- FUNÇÃO DE BUSCA ---
def buscar_noticias(time):
    url = f"https://news.google.com/rss/search?q={time}+noticias+futebol+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        return [{"titulo": i.find('title').text.split(" - ")[0], "link": i.find('link').text} for i in root.findall('.//item')[:10]]
    except:
        return []

# --- FUNÇÃO DE ÁUDIO ---
async def gerar_audio(texto, path):
    # Remove carácteres que podem bugar a voz
    texto_limpo = texto.replace("*", "").replace("#", "").replace("-", " ")
    communicate = edge_tts.Communicate(texto_limpo[:2500], "pt-BR-AntonioNeural")
    await communicate.save(path)

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    time_input = st.text_input("⚽ Digite o Time:", "Corinthians")
    if st.button("🔍 Buscar Notícias"):
        st.session_state.resultados = buscar_noticias(time_input)

    if "resultados" in st.session_state:
        escolha = st.selectbox("Escolha a matéria:", [n["titulo"] for n in st.session_state.resultados])
        
        if st.button("🚀 GERAR PACOTE COMPLETO"):
            if not api_key:
                st.error("⚠️ Insira a API KEY na barra lateral!")
            else:
                with st.spinner("IA criando roteiro e áudio..."):
                    try:
                        # O SEGREDO: Na biblioteca google-genai, o modelo é apenas "gemini-1.5-flash"
                        # SEM o prefixo "models/". Isso evita o erro 404 que você viu.
                        client = genai.Client(api_key=api_key)
                        
                        response = client.models.generate_content(
                            model="gemini-1.5-flash", 
                            contents=f"Crie um roteiro para youtube sobre o {time_input} baseado em: {escolha}"
                        )
                        
                        st.session_state.roteiro = response.text
                        
                        # Criar arquivo de áudio
                        tmp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                        asyncio.run(gerar_audio(response.text, tmp_audio.name))
                        st.session_state.audio_path = tmp_audio.name
                        st.success("✅ Sucesso!")
                    except Exception as e:
                        st.error(f"Erro detalhado: {e}")

with col2:
    if "roteiro" in st.session_state:
        st.subheader("📝 Roteiro Gerado")
        st.text_area("", value=st.session_state.roteiro, height=400)
    
    if "audio_path" in st.session_state:
        st.subheader("🎤 Narração")
        st.audio(st.session_state.audio_path)
