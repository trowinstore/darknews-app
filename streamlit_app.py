import streamlit as st
from google import genai
import asyncio, edge_tts, os, tempfile, requests
import xml.etree.ElementTree as ET

st.set_page_config(page_title="DarkNews v1", page_icon="🏆")

st.title("🏆 Gerador DarkNews")

# A Chave entra na barra lateral ou nos Secrets do Streamlit
api_key = st.sidebar.text_input("Cole sua Gemini API Key:", type="password")

time = st.text_input("Time de Futebol:", "Corinthians")

if st.button("🔍 Buscar Notícias"):
    url = f"https://news.google.com/rss/search?q={time}+noticias+futebol&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    res = requests.get(url)
    root = ET.fromstring(res.content)
    
    st.session_state.noticias = []
    for item in root.findall('.//item')[:5]:
        st.session_state.noticias.append(item.find('title').text)

if "noticias" in st.session_state:
    escolha = st.selectbox("Selecione a Notícia:", st.session_state.noticias)
    
    if st.button("🚀 Gerar Pacote Completo"):
        if not api_key:
            st.error("Falta a API KEY!")
        else:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=f"Gere um roteiro narrado sobre: {escolha}"
                )
                roteiro = response.text
                st.write(roteiro)

                # Áudio
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    async def speak():
                        await edge_tts.Communicate(roteiro[:1000], "pt-BR-AntonioNeural").save(tmp.name)
                    asyncio.run(speak())
                    st.audio(tmp.name)
            except Exception as e:
                st.error(f"Erro: {e}")