import streamlit as st
from google import genai
import asyncio, edge_tts, os, tempfile, requests
import xml.etree.ElementTree as ET

st.set_page_config(page_title="DarkNews v7.7", layout="wide")

st.title("🏆 Gerador DarkNews Pro")
st.markdown("---")

# Barra Lateral
st.sidebar.header("Configurações")
api_key_env = st.secrets.get("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input("Gemini API Key:", value=api_key_env, type="password")

# --- BUSCA RSS ---
def buscar_noticias(time):
    url = f"https://news.google.com/rss/search?q={time}+noticias+futebol+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        noticias = []
        for item in root.findall('.//item')[:10]:
            titulo = item.find('title').text.split(" - ")[0]
            noticias.append({"titulo": titulo, "link": item.find('link').text})
        return noticias
    except:
        return []

# --- ÁUDIO ---
async def gerar_audio(texto, path):
    # Remove marcações de texto que a IA gera (como asteriscos) para não bugar a voz
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
                with st.spinner("IA processando roteiro e voz..."):
                    try:
                        # CLIENTE DA API
                        client = genai.Client(api_key=api_key)
                        
                        # CHAMADA CORRIGIDA: apenas o nome do modelo, sem 'models/'
                        # Isso resolve o erro 404 de uma vez por todas
                        response = client.models.generate_content(
                            model="gemini-1.5-flash", 
                            contents=f"Crie um roteiro de vídeo narrado para youtube sobre o {time_input}. Notícia: {escolha}"
                        )
                        
                        st.session_state.roteiro = response.text
                        
                        # Gerar Áudio
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                        asyncio.run(gerar_audio(response.text, tmp.name))
                        st.session_state.audio_path = tmp.name
                        st.success("✅ Gerado com sucesso!")
                        
                    except Exception as e:
                        st.error(f"Erro Detalhado: {str(e)}")

with col2:
    if "roteiro" in st.session_state:
        st.subheader("📝 Roteiro Gerado")
        st.text_area("", value=st.session_state.roteiro, height=400)
    
    if "audio_path" in st.session_state:
        st.subheader("🎤 Narração")
        st.audio(st.session_state.audio_path)
        with open(st.session_state.audio_path, "rb") as f:
            st.download_button("⬇️ Baixar Áudio", f, file_name="noticia.mp3")
