import streamlit as st
from io import BytesIO
from PyPDF2 import PdfReader
import docx
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from config import OPENAI_API_KEY
from rag_memory import init_db, save_viability, search_similar
import speech_recognition as sr
from audio_pdf_generator import generate_pdf
from pydub import AudioSegment
import tempfile
import os

# Inicializa o banco de dados
init_db()

# -------------------------------
# CONFIGURAÇÃO INICIAL
# -------------------------------
st.set_page_config(page_title="Analisador de Viabilidades - NielsenIQ", layout="wide")

st.title("🤖 Analisador de Viabilidades NielsenIQ")
st.caption("Envie arquivos (.xlsx, .docx, .pdf) e converse com o assistente de IA sobre o conteúdo.")

# -------------------------------
# ENTRADA DE ÁUDIO DIRETA (MICROFONE)
# -------------------------------
st.subheader("🎤 Fale com o Chat")

if st.button("🎙️ Falar com o Chat"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Aguardando sua fala... Fale algo!")
        try:
            # Capturar áudio do microfone
            audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            st.info("🎙️ Processando sua fala...")
            
            # Reconhecer o texto do áudio
            recognized_text = recognizer.recognize_google(audio_data, language="pt-BR")
            
            # # Exibir o texto reconhecido
            # st.success(f"✅ Texto reconhecido:\n\n{recognized_text}")

            # Converter o texto reconhecido em Markdown
            markdown_text = f"# Texto Reconhecido\n\n{recognized_text}"
            st.markdown(markdown_text)

            # Gerar PDF a partir do Markdown
            output_path = "C:/Python311/Projeto_Chega_Viabilidades/Outputs"
            os.makedirs(output_path, exist_ok=True)
            pdf_path = generate_pdf(markdown_text, output_path)

            # Armazenar o caminho do PDF e o texto reconhecido no estado da sessão
            st.session_state["pdf_path"] = pdf_path
            st.session_state["recognized_text"] = recognized_text

            st.success(f"✅ PDF gerado com sucesso! [Baixar PDF](./{pdf_path})")

        except sr.UnknownValueError:
            st.error("❌ Não foi possível reconhecer sua fala. Tente novamente.")
        except sr.RequestError as e:
            st.error(f"❌ Erro ao acessar o serviço de reconhecimento de fala: {e}")
        except Exception as e:
            st.error(f"❌ Ocorreu um erro: {e}")

# -------------------------------
# SALVAR VIABILIDADE
# -------------------------------
if "pdf_path" in st.session_state and "recognized_text" in st.session_state:
    if st.button("Salvar Viabilidade"):
        vid = save_viability(
            title="Viabilidade Gerada por Áudio",
            client_name="Cliente X",
            viability_type="audio_to_pdf",
            text=st.session_state["recognized_text"],
            file_path=st.session_state["pdf_path"]
        )
        st.success(f"✅ PDF salvo no banco de dados com ID {vid}")

# -------------------------------
# SESSÃO DE ESTADO (memória do chat)
# -------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_text" not in st.session_state:
    st.session_state.document_text = ""

# -------------------------------
# FUNÇÕES DE EXTRAÇÃO DE TEXTO
# -------------------------------
def extract_text_from_pdf(file: BytesIO) -> str:
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file: BytesIO) -> str:
    doc = docx.Document(file)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_xlsx(file: BytesIO) -> str:
    dfs = pd.read_excel(file, sheet_name=None)
    text = ""
    for sheet, df in dfs.items():
        text += f"\n--- Sheet: {sheet} ---\n"
        text += df.to_string(index=False)
    return text

# -------------------------------
# UPLOAD DE ARQUIVOS
# -------------------------------
uploaded_files = st.file_uploader(
    "📎 Faça upload de arquivos de viabilidade (.xlsx, .docx, .pdf)",
    type=["pdf", "docx", "xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    all_text = ""
    for f in uploaded_files:
        if f.name.endswith(".pdf"):
            all_text += extract_text_from_pdf(f)
        elif f.name.endswith(".docx"):
            all_text += extract_text_from_docx(f)
        elif f.name.endswith(".xlsx"):
            all_text += extract_text_from_xlsx(f)
    st.session_state.document_text = all_text
    st.success("✅ Arquivos processados com sucesso!")
    with st.expander("📄 Visualizar texto extraído"):
        st.text_area("Conteúdo extraído:", all_text[:4000], height=300)


#--------------------------------
#Salvar Viabilidade
#-------------------------------
if uploaded_files and st.button("Salvar Viabilidade"):
    vid = save_viability(
        title="Nova Viabilidade",
        client_name="Cliente X",  # Substitua pelo nome do cliente, se necessário
        viability_type="questionnaire",  # Substitua pelo tipo de viabilidade, se necessário
        text=st.session_state.document_text,
        file_path=uploaded_files[0].name
    )
    st.success(f"✅ Viabilidade salva com ID {vid}")

# -------------------------------
# CONFIGURAÇÃO DO LLM
# -------------------------------
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.2, openai_api_key=OPENAI_API_KEY)

# -------------------------------
# EXIBIR HISTÓRICO DO CHAT
# -------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# -------------------------------
# INPUT DO USUÁRIO
# -------------------------------
if prompt := st.chat_input("Digite sua pergunta ou análise sobre os arquivos..."):
    # Adiciona a entrada do usuário ao estado da sessão
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Busca casos semelhantes no banco de dados
    similar_cases = search_similar(prompt)
    threshold = 1.0  # Limite de distância para filtrar casos relevantes
    filtered_cases = [s for s in similar_cases if s['distance'] < threshold]

    if filtered_cases:
        context_text = "\n\n".join([f"Trecho {i+1} (Relevância: {s['distance']:.2f}):\n{s['chunk_text']}" for i, s in enumerate(filtered_cases[:3])])
        st.info(f"🔎 {len(filtered_cases)} casos relevantes encontrados no histórico.")
    else:
        context_text = "Nenhum caso relevante encontrado."
        st.warning("Nenhum caso relevante encontrado no histórico.")

    # Construir contexto: casos semelhantes + documento
    context = st.session_state.document_text[:3000]  # Limitar o tamanho do texto do documento
    messages = [
        SystemMessage(content=(
            "Você é um especialista em viabilidades NielsenIQ. "
            "Use os casos semelhantes e o conteúdo do documento para responder à pergunta do usuário. "
            # "Seja direto e objetivo. "
            "Se os casos semelhantes forem insuficientes, baseie-se no conteúdo do documento."
        )),
        HumanMessage(content=f"Casos semelhantes:\n{context_text}\n\nConteúdo do documento:\n{context}"),
        HumanMessage(content=f"Pergunta: {prompt}")
    ]

    # Adicionar histórico recente ao contexto
    for m in st.session_state.messages[-3:]:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        else:
            messages.append(AIMessage(content=m["content"]))

    # Geração de resposta do assistente
    with st.chat_message("assistant"):
        with st.spinner("Analisando..."):
            try:
                response = llm.invoke(messages)  # Substituído para evitar aviso de depreciação
                st.markdown(response.content)
                st.session_state.messages.append({"role": "assistant", "content": response.content})
            except Exception as e:
                st.error(f"Erro ao gerar resposta: {e}")
else:
    st.warning("Por favor, insira uma pergunta ou análise para continuar.")