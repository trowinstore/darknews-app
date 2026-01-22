import streamlit as st
import google.generativeai as genai
import asyncio, edge_tts, os, tempfile, requests
import xml.etree.ElementTree as ET

st.set_page_config(page_title="DarkNews v7.8", layout="wide")
st.title("🏆 Gerador DarkNews Pro")

# Barra Lateral
st.sidebar.header("Configurações")
api_key = st.sidebar.text_input("Gemini API Key:", type="password")

# --- BUSCA RSS ---
def buscar_noticias(time):
    url = f"https://news.google.com/rss/search?q={time}+noticias+futebol+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        return [{"titulo": i.find('title').text.split(" - ")[0], "link": i.find('link').text} for i in root.findall('.//item')[:10]]
    except:
        return []

# --- ÁUDIO ---
async def gerar_audio(texto, path):
    texto_puro = texto.replace("*", "").replace("#", "").replace("-", " ")
    communicate = edge_tts.Communicate(texto_puro[:2000], "pt-BR-AntonioNeural")
    await communicate.save(path)

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    time_input = st.text_input("⚽ Digite o Time:", "Corinthians")
    if st.button("🔍 1. Buscar Notícias"):
        st.session_state.resultados = buscar_noticias(time_input)

    if "resultados" in st.session_state:
        titulos = [n["titulo"] for n in st.session_state.resultados]
        escolha = st.selectbox("2. Escolha a matéria:", titulos)
        
        if st.button("🚀 3. GERAR PACOTE COMPLETO"):
            if not api_key:
                st.error("⚠️ Coloque sua API KEY na lateral!")
            else:
                with st.spinner("IA processando..."):
                    try:
                        # CONFIGURAÇÃO DA BIBLIOTECA CLÁSSICA
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"Crie um roteiro de vídeo narrado para youtube sobre o {time_input}. Notícia: {escolha}"
                        
                        # GERAÇÃO DE TEXTO
                        response = model.generate_content(prompt)
                        roteiro = response.text
                        st.session_state.roteiro = roteiro
                        
                        # GERAR ÁUDIO
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                        asyncio.run(gerar_audio(roteiro, tmp.name))
                        st.session_state.audio_path = tmp.name
                        st.success("✅ Sucesso Total!")
                        
                    except Exception as e:
                        st.error(f"Erro Detalhado: {str(e)}")

with col2:
    if "roteiro" in st.session_state:
        st.subheader("📝 Roteiro Gerado")
        st.text_area("", value=st.session_state.roteiro, height=400)
    
    if "audio_path" in st.session_state:
        st.subheader("🎤 Narração")
        st.audio(st.session_state.audio_path)
