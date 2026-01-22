import streamlit as st
import google.generativeai as genai

st.title("Teste de Conexão Gemini")
key = st.text_input("Cole sua NOVA chave aqui:", type="password")

if st.button("Testar Agora"):
    try:
        genai.configure(api_key=key)
        # Forçando o modelo 1.5-flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Diga: Olá, a conexão funciona!")
        st.success(response.text)
    except Exception as e:
        st.error(f"Erro Real da API: {e}")
