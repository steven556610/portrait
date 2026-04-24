import os
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.llms import LlamaCpp
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings

EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def _get_embeddings():
    """取得統一的 Embedding 模型，確保 setup 與 load 使用相同設定。"""
    return HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)


def setup_vector_db(text_data: str, persist_dir: str = "../model/chroma_db"):
    """
    方案 C 基礎：對話切分並存入 Chroma DB 作為長期記憶。
    """
    if not text_data:
        raise ValueError("沒有可用的文字資料可以建立向量數據庫。")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        length_function=len
    )
    chunks = text_splitter.split_text(text_data)
    
    # 使用統一的 Embedding 模型
    embeddings = _get_embeddings()
    
    vector_db = Chroma.from_texts(
        texts=chunks, 
        embedding=embeddings, 
        persist_directory=persist_dir
    )
    return vector_db

def load_vector_db(persist_dir: str = "../model/chroma_db"):
    """
    直接從已儲存的 ChromaDB 目錄加載向量資料庫。
    不需要重新處理文字，適合 Streamlit App 等需要快速啟動的場景。
    """
    if not os.path.exists(persist_dir):
        raise FileNotFoundError(
            f"找不到向量資料庫目錄 '{persist_dir}'。\n"
            "請先執行 main.py 建立資料庫後再啟動 App。"
        )
    embeddings = _get_embeddings()
    return Chroma(persist_directory=persist_dir, embedding_function=embeddings)

def query_persona_rag_gemini(question: str, vector_db):
    \"\"\"使用 Ollama 進行 RAG 長期記憶查詢 (為了相容舊檔名暫不更名)\"\"\"
    llm = ChatOllama(model="qwen2.5:14b", temperature=0.3)
    
    # 尋找與問題最相關的 5 個對話片段
    docs = vector_db.similarity_search(question, k=5)
    context = "\n".join([doc.page_content for doc in docs])
    
    prompt = ChatPromptTemplate.from_template(
        "你是一個專業的私人助理。請根據以下的對話歷史記憶，用繁體中文準確回答使用者的問題。\n"
        "如果記憶中缺乏相關資訊，請直接回答「不知道」，絕不可自行捏造資訊。\n\n"
        "【對話歷史記憶】\n"
        "{context}\n\n"
        "問題：{question}"
    )
    chain = prompt | llm
    return chain.invoke({"context": context, "question": question}).content

def query_persona_rag_local(question: str, vector_db, local_model_path: str):
    """
    方案 C 擴充：使用地端 CPU 模型 (如 Llama-3-8B-Instruct GGUF) 進行記憶查詢。
    極度適合具有 32GB RAM 以及高度隱私要求的本地執行環境。
    """
    if not os.path.exists(local_model_path):
        return f"[錯誤] 找不到地端模型，請確認 {local_model_path} 是否存在。"
        
    llm = LlamaCpp(
        model_path=local_model_path,
        temperature=0.3,
        max_tokens=1000,
        n_ctx=4096,   # Context window
        n_batch=512,  # 批次處理大小
        verbose=False,
    )
    
    docs = vector_db.similarity_search(question, k=5)
    context = "\n".join([doc.page_content for doc in docs])
    
    template = """
    你是一個專業的私人助理。請閱讀以下的對話歷史記憶，用繁體中文準確回答使用者的問題。
    如果缺乏相關資訊，請回答「不知道」。
    
    【對話歷史記憶】
    {context}
    
    問題：{question}
    回答：
    """
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    return chain.invoke({"context": context, "question": question})
