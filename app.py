import streamlit as st
import google.generativeai as genai
import asyncio, edge_tts, os, tempfile, requests
import xml.etree.ElementTree as ET

st.set_page_config(page_title="DarkNews Final", layout="wide")
st.title("🏆 Gerador DarkNews Pro")

api_key = st.sidebar.text_input("Gemini API Key:", type="password")

# --- BUSCA RSS ---
def buscar_noticias(time):
    url = f"https://news.google.com/rss/search?q={time}+noticias+futebol+when:1d&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        return [{"titulo": i.find('title').text.split(" - ")[0], "link": i.find('link').text} for i in root.findall('.//item')[:10]]
    except: return []

# --- INTERFACE ---
col1, col2 = st.columns([1, 1])

with col1:
    time_input = st.text_input("⚽ Time:", "Corinthians")
    if st.button("🔍 1. Buscar Notícias"):
        st.session_state.resultados = buscar_noticias(time_input)

    if "resultados" in st.session_state:
        escolha = st.selectbox("2. Escolha a matéria:", [n["titulo"] for n in st.session_state.resultados])
        
        if st.button("🚀 3. GERAR TUDO"):
            if not api_key:
                st.error("Insira a chave na lateral!")
            else:
                with st.spinner("IA a tentar conectar..."):
                    genai.configure(api_key=api_key)
                    
                    # LISTA DE MODELOS PARA TENTAR ESCAPAR DO ERRO 404
                    modelos_para_testar = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]
                    sucesso = False
                    
                    for nome_modelo in modelos_para_testar:
                        try:
                            model = genai.GenerativeModel(nome_modelo)
                            response = model.generate_content(f"Roteiro de youtube sobre: {escolha}")
                            st.session_state.roteiro = response.text
                            
                            # Gerar Áudio
                            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                            async def narrar():
                                comm = edge_tts.Communicate(response.text[:2000], "pt-BR-AntonioNeural")
                                await comm.save(tmp.name)
                            asyncio.run(narrar())
                            st.session_state.audio_path = tmp.name
                            
                            sucesso = True
                            st.success(f"Conectado via {nome_modelo}!")
                            break # Para no primeiro que funcionar
                        except Exception as e:
                            continue # Tenta o próximo modelo se der 404
                    
                    if not sucesso:
                        st.error("O Google ainda recusa a conexão. Verifique se a sua chave API é do 'Google AI Studio'.")

with col2:
    if "roteiro" in st.session_state:
        st.text_area("Roteiro:", value=st.session_state.roteiro, height=400)
    if "audio_path" in st.session_state:
        st.audio(st.session_state.audio_path)
