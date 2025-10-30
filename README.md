# LLMs_RAG

Este projeto é um **Analisador de Viabilidades** que utiliza **Modelos de Linguagem Natural (LLMs)** e **Recuperação de Dados com Geração de Respostas (RAG)** para processar arquivos, realizar buscas semânticas e interagir com o usuário por meio de um assistente de IA. O sistema suporta entrada de áudio, geração de PDFs e armazenamento de dados em um banco de dados SQLite.

---

## **Arquivos do Projeto**

### **1. `app.py`**
O arquivo principal do projeto, responsável por configurar a interface do usuário com **Streamlit** e integrar as funcionalidades do sistema.

#### **Principais Funcionalidades:**
- **Entrada de Áudio Direta**:
  - Permite que o usuário fale diretamente com o assistente.
  - O áudio é processado, convertido em texto e exibido na interface.
  - O texto reconhecido pode ser salvo como um PDF e armazenado no banco de dados.

- **Upload de Arquivos**:
  - Suporta arquivos nos formatos `.pdf`, `.docx` e `.xlsx`.
  - Extrai o texto dos arquivos enviados e o disponibiliza para análise.

- **Chat com o Assistente**:
  - O usuário pode fazer perguntas ou análises sobre os arquivos enviados.
  - O sistema utiliza um modelo de linguagem (LLM) para responder com base nos dados extraídos e em casos semelhantes armazenados no banco de dados.

- **Busca de Casos Semelhantes**:
  - Realiza buscas semânticas no banco de dados para encontrar informações relevantes relacionadas à consulta do usuário.

- **Geração de PDFs**:
  - O texto reconhecido do áudio ou extraído dos arquivos pode ser salvo como um PDF.

- **Armazenamento no Banco de Dados**:
  - As viabilidades e os arquivos processados são armazenados no banco de dados SQLite.

---

### **2. `rag_memory.py`**
Este arquivo contém as funções principais para gerenciar o banco de dados, gerar embeddings e realizar buscas semânticas.

#### **Principais Funcionalidades:**
- **Inicialização do Banco de Dados (`init_db`)**:
  - Cria as tabelas necessárias no banco de dados SQLite:
    - `viabilities`: Armazena informações sobre as viabilidades processadas.
    - `embeddings`: Armazena os embeddings gerados para os textos.
    - `chat_logs`: Armazena o histórico de mensagens do chat.

- **Geração de Embeddings (`generate_embedding`)**:
  - Utiliza a API da OpenAI para gerar embeddings semânticos para os textos.

- **Salvar Viabilidade (`save_viability`)**:
  - Divide o texto em chunks, gera embeddings para cada chunk e salva as informações no banco de dados.

- **Busca Semântica (`search_similar`)**:
  - Utiliza o índice FAISS para realizar buscas rápidas e encontrar textos semelhantes no banco de dados com base em uma consulta.

---

### **3. `audio_pdf_generator.py`**
Este arquivo é responsável por gerar arquivos PDF a partir de texto em Markdown.

#### **Principais Funcionalidades:**
- **Geração de PDFs (`generate_pdf`)**:
  - Recebe um texto em formato Markdown e o converte em um arquivo PDF.
  - Salva o PDF no diretório especificado.

---

## **Como Funciona o Sistema**

1. **Entrada de Dados**:
   - O usuário pode enviar arquivos (`.pdf`, `.docx`, `.xlsx`) ou falar diretamente com o assistente.
   - O texto dos arquivos ou do áudio é processado e exibido na interface.

2. **Processamento e Armazenamento**:
   - O texto é dividido em chunks e embeddings são gerados para cada chunk.
   - As informações são armazenadas no banco de dados SQLite.

3. **Interação com o Assistente**:
   - O usuário pode fazer perguntas ou análises sobre os dados enviados.
   - O sistema utiliza um modelo de linguagem (LLM) para responder com base nos dados extraídos e em casos semelhantes encontrados no banco de dados.

4. **Busca Semântica**:
   - O sistema realiza buscas semânticas no banco de dados para encontrar informações relevantes relacionadas à consulta do usuário.

5. **Geração de PDFs**:
   - O texto reconhecido do áudio ou extraído dos arquivos pode ser salvo como um PDF.

---

## **Como Executar o Projeto**

### **Pré-requisitos**
- Python 3.11 ou superior
- Ambiente virtual configurado
- Dependências instaladas (listadas no `requirements.txt`)

### **Passos para Execução**
1. Clone o repositório:
   ```bash
   git clone https://github.com/Noah1803/LLMs_RAG.git
   cd LLMs_RAG