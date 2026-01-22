import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import requests
import xml.etree.ElementTree as ET

# Configuração da página
st.set_page_config(page_title="DarkNews v7.5", layout="wide")

st.title("🏆 Gerador DarkNews Pro")
st.markdown("---")

# Barra Lateral para Configurações
st.sidebar.header("Configurações")
# Tenta pegar a chave dos Secrets do Streamlit, se não existir, deixa em branco para preenchimento manual
api_key_env = st.secrets.get("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input("Gemini API Key:", value=api_key_env, type="password")

# --- FUNÇÕES ---

def buscar_noticias_rss(time):
    url = f"https://news.google.com/rss/search?q={time}+noticias+futebol+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        links_data = []
        for item in root.findall('.//item')[:10]:
            titulo = item.find('title').text.split(" - ")[0]
            link = item.find('link').text
            links_data.append({"titulo": titulo, "link": link})
        return links_data
    except Exception as e:
        st.error(f"Erro ao buscar notícias: {e}")
        return []

async def gerar_audio(texto, path):
    # Filtra o texto para evitar carácteres especiais que quebram a voz
    texto_limpo = texto.replace("*", "").replace("#", "")
    communicate = edge_tts.Communicate(texto_limpo[:2500], "pt-BR-AntonioNeural")
    await communicate.save(path)

# --- INTERFACE ---

col1, col2 = st.columns([1, 1])

with col1:
    time_input = st.text_input("⚽ Digite o Time:", "Corinthians")
    
    if st.button("🔍 Buscar Notícias"):
        with st.spinner("Buscando notícias recentes..."):
            resultados = buscar_noticias_rss(time_input)
            if resultados:
                st.session_state.noticias_encontradas = resultados
            else:
                st.warning("Nenhuma notícia encontrada.")

    if "noticias_encontradas" in st.session_state:
        titulos = [n["titulo"] for n in st.session_state.noticias_encontradas]
        escolha = st.selectbox("Selecione a matéria para o roteiro:", titulos)
        duracao = st.select_slider("Duração do vídeo:", options=["1 min", "3 min", "5 min"])
        
        if st.button("🚀 GERAR PACOTE COMPLETO"):
            if not api_key:
                st.error("⚠️ Você precisa da API KEY (cole na barra lateral ou configure nos Secrets).")
            else:
                with st.spinner("A IA está escrevendo e narrando..."):
                    try:
                        # 1. Configura Cliente Gemini
                        client = genai.Client(api_key=api_key)
                        
                        # 2. Gera Roteiro
                        prompt_final = f"""
                        Aja como um roteirista de canal Dark de futebol no YouTube.
                        Crie um roteiro de {duracao} sobre o {time_input} baseado nesta notícia: {escolha}.
                        O roteiro deve ser instigante, polêmico e manter o público preso.
                        No final, dê 5 sugestões de títulos clickbait.
                        Separe o texto da narração claramente.
                        """
                        
                        # Chamada do modelo corrigida para evitar erro 404
                        response = client.models.generate_content(
                            model="gemini-1.5-flash", 
                            contents=prompt_final
                        )
                        
                        roteiro_texto = response.text
                        st.session_state.roteiro_gerado = roteiro_texto
                        
                        # 3. Gera Áudio
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                            audio_path = tmp.name
                        
                        # Executa a narração
                        asyncio.run(gerar_audio(roteiro_texto, audio_path))
                        st.session_state.audio_gerado = audio_path
                        
                        st.success("✅ Tudo pronto!")

                    except Exception as e:
                        st.error(f"Erro na geração: {str(e)}")

with col2:
    st.subheader("📺 Resultado")
    if "roteiro_gerado" in st.session_state:
        st.text_area("Roteiro e Títulos:", value=st.session_state.roteiro_gerado, height=450)
    
    if "audio_gerado" in st.session_state:
        st.audio(st.session_state.audio_gerado)
        with open(st.session_state.audio_gerado, "rb") as f:
            st.download_button("⬇️ Baixar Narração (MP3)", f, file_name="narracao_dark.mp3")

st.markdown("---")
st.caption("DarkNews v7.5 - Operando via Streamlit Cloud")
