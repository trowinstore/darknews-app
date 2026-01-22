import streamlit as st
from google import genai
import asyncio
import edge_tts
import os
import tempfile
import requests
import xml.etree.ElementTree as ET

# Configuração da página para evitar erros de layout
st.set_page_config(page_title="DarkNews v7.5", layout="wide")

st.title("🏆 Gerador DarkNews Pro")
st.markdown("---")

# Barra Lateral
st.sidebar.header("Configurações")
api_key_env = st.secrets.get("GEMINI_API_KEY", "")
api_key = st.sidebar.text_input("Gemini API Key:", value=api_key_env, type="password")

# --- FUNÇÕES ---

def buscar_noticias_rss(time):
    # Uso do Google News RSS para evitar bloqueios de IP (403/429)
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
    # Limpeza de caracteres que o narrador tenta ler e falha
    texto_limpo = texto.replace("*", "").replace("#", "").replace("-", " ")
    # Limite de segurança para não travar o processo
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
                st.warning("Nenhuma notícia encontrada para este time.")

    if "noticias_encontradas" in st.session_state:
        titulos = [n["titulo"] for n in st.session_state.noticias_encontradas]
        escolha = st.selectbox("Selecione a matéria:", titulos)
        duracao = st.select_slider("Duração aproximada:", options=["1 min", "3 min", "5 min"])
        
        if st.button("🚀 GERAR PACOTE COMPLETO"):
            if not api_key:
                st.error("⚠️ Insira sua API KEY na barra lateral ou nos Secrets.")
            else:
                with st.spinner("Processando IA e Narração..."):
                    try:
                        # Inicialização do Cliente
                        client = genai.Client(api_key=api_key)
                        
                        prompt = f"""
                        Aja como roteirista de YouTube especializado em futebol.
                        Crie um roteiro de {duracao} sobre o {time_input} baseado na notícia: {escolha}.
                        O texto deve ser dinâmico para narração.
                        No final, sugira 5 títulos clickbait e descrição SEO.
                        """
                        
                        # CORREÇÃO DO ERRO 404: Nome do modelo sem o prefixo 'models/'
                        response = client.models.generate_content(
                            model="gemini-1.5-flash", 
                            contents=prompt
                        )
                        
                        roteiro_texto = response.text
                        st.session_state.roteiro_gerado = roteiro_texto
                        
                        # Geração de Áudio Temporário
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                            audio_path = tmp.name
                        
                        asyncio.run(gerar_audio(roteiro_texto, audio_path))
                        st.session_state.audio_gerado = audio_path
                        
                        st.success("✅ Gerado com sucesso!")

                    except Exception as e:
                        # Exibe o erro detalhado se algo falhar na API
                        st.error(f"Erro técnico: {str(e)}")

with col2:
    st.subheader("📺 Resultado Final")
    if "roteiro_gerado" in st.session_state:
        st.text_area("Roteiro Criado:", value=st.session_state.roteiro_gerado, height=400)
    
    if "audio_gerado" in st.session_state:
        st.audio(st.session_state.audio_gerado)
        with open(st.session_state.audio_gerado, "rb") as f:
            st.download_button("⬇️ Baixar Áudio (MP3)", f, file_name="narracao.mp3")

st.markdown("---")
st.caption("v7.5 | Streamlit Cloud Engine")
