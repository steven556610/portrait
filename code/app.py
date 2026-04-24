import os
import sys
import streamlit as st
from dotenv import load_dotenv

# --- 路徑設定 ---
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MODEL_DIR   = os.path.join(ROOT_DIR, "model")
REPORTS_DIR = os.path.join(ROOT_DIR, "data", "reports")
VIS_DIR     = os.path.join(ROOT_DIR, "visualize")

load_dotenv(os.path.join(ROOT_DIR, ".env"))
# API_KEY 已不再需要
# API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# -----------------------------------------------------------------------
# 工具函式
# -----------------------------------------------------------------------
def list_available_personas() -> list[str]:
    """列出 model/ 目錄下所有已建立 ChromaDB 的人物名稱。"""
    if not os.path.exists(MODEL_DIR):
        return []
    return sorted([
        d for d in os.listdir(MODEL_DIR)
        if os.path.isdir(os.path.join(MODEL_DIR, d, "chroma_db"))
    ])

def get_db_dir(person_name: str) -> str:
    return os.path.join(MODEL_DIR, person_name, "chroma_db")

def get_report_path(person_name: str) -> str:
    return os.path.join(REPORTS_DIR, f"{person_name}.md")

def get_wordcloud_path(person_name: str) -> str:
    path = os.path.join(VIS_DIR, f"{person_name}_wordcloud.png")
    return path if os.path.exists(path) else None

# -----------------------------------------------------------------------
# 頁面設定
# -----------------------------------------------------------------------
st.set_page_config(
    page_title="LINE 人物誌助理",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
    .stApp { background-color: #0f1117; }

    [data-testid="stSidebar"] {
        background-color: #1a1d27;
        border-right: 1px solid #2d3047;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 { color: #e8eaf6; }

    .source-chip {
        background: #1e2235;
        border: 1px solid #3d4166;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 4px 0;
        font-size: 0.82rem;
        color: #9fa8da;
        line-height: 1.5;
    }
    .hero-title {
        background: linear-gradient(135deg, #7986cb, #9c27b0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 1.8rem;
    }
    .persona-badge {
        background: linear-gradient(135deg, #3d4166, #2d3047);
        border: 1px solid #5c6bc0;
        border-radius: 20px;
        padding: 4px 16px;
        color: #c5cae9;
        font-size: 0.9rem;
        display: inline-block;
        margin-bottom: 8px;
    }
    .stButton > button {
        background: #1e2235;
        border: 1px solid #3d4166;
        border-radius: 20px;
        color: #c5cae9;
        font-size: 0.83rem;
        padding: 4px 14px;
        width: 100%;
        text-align: left;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: #2d3269;
        border-color: #7986cb;
        color: #ffffff;
    }
    hr { border-color: #2d3047; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------
# 載入 ChromaDB（依人物快取）
# -----------------------------------------------------------------------
@st.cache_resource(show_spinner="⚙️ 正在載入向量記憶庫…")
def load_db(person_name: str):
    from memory import load_vector_db
    return load_vector_db(get_db_dir(person_name))

# -----------------------------------------------------------------------
# RAG 查詢
# -----------------------------------------------------------------------
def rag_query(question: str, vector_db, k: int = 5):
    from langchain_community.chat_models import ChatOllama
    from langchain_core.prompts import ChatPromptTemplate

    docs = vector_db.similarity_search(question, k=k)
    context = "\n---\n".join([doc.page_content for doc in docs])

    llm = ChatOllama(model="qwen2.5:14b", temperature=0.3)
    prompt = ChatPromptTemplate.from_template(
        "你是一個專業的私人助理，協助使用者從 LINE 對話記錄中找出關於特定人物的資訊。\n"
        "請根據以下的【對話片段記憶】，用繁體中文準確且條理清晰地回答問題。\n"
        "如果記憶中缺乏相關資訊，請直接回答「根據現有記錄，無法找到相關資訊。」，絕不可自行捏造。\n\n"
        "【對話片段記憶】\n{context}\n\n"
        "問題：{question}"
    )
    chain = prompt | llm
    answer = chain.invoke({"context": context, "question": question}).content
    return answer, docs

# -----------------------------------------------------------------------
# 側邊欄：人物選擇 + Sources Panel
# -----------------------------------------------------------------------
with st.sidebar:
    st.markdown('<p class="hero-title">💬 人物誌助理</p>', unsafe_allow_html=True)
    st.caption("基於 LINE 對話記錄 × RAG × Gemini")
    st.divider()

    # 人物清單
    personas = list_available_personas()

    if not personas:
        st.error("尚未建立任何人物資料庫。\n請先執行：\n```\npython main.py --build-all\n```")
        st.stop()

    selected_persona = st.selectbox(
        "🧑 選擇對話對象",
        options=personas,
        key="persona_selector",
    )

    st.markdown(f'<div class="persona-badge">👤 {selected_persona}</div>', unsafe_allow_html=True)

    # 🚨 詐騙偵測風險警示 (Mockup)
    st.markdown("---")
    st.markdown("""
        <div style="background-color:#4a1c1c; border-left:4px solid #f44336; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
            <p style="color:#ffcdd2; margin: 0; font-weight: bold;">🔴 高風險警示 (Risk Score: 85/100)</p>
        </div>
    """, unsafe_allow_html=True)
    with st.expander("👉 查看警示詳細原因"):
        st.markdown(
            "⚠️ **高風險特徵檢測結果**\n"
            "- 對話中頻繁提及 `投資`、`虛擬貨幣` 等詞彙。\n"
            "- 存在引導匯款或詢問銀行帳戶的語句。\n"
            "- 提及「保證獲利」或「內線消息」。\n\n"
            "*(備註：此為風險模型預測範例，後續可串接外部詐騙知識圖譜進階判定)*"
        )
    st.divider()

    # 文字雲
    wc_path = get_wordcloud_path(selected_persona)
    if wc_path:
        st.subheader("🌐 對話文字雲")
        st.image(wc_path, use_container_width=True)
        st.divider()

    # Persona 報告
    st.subheader("📄 人物誌報告")
    rp = get_report_path(selected_persona)
    if os.path.exists(rp):
        with open(rp, "r", encoding="utf-8") as f:
            report_content = f.read()
        with st.expander("點擊展開完整報告", expanded=False):
            st.markdown(report_content)
    else:
        st.warning(f"找不到 {selected_persona} 的報告，請先執行 main.py")

# -----------------------------------------------------------------------
# 主畫面：Chat Panel
# -----------------------------------------------------------------------
# 切換人物時清空歷史
if st.session_state.get("last_persona") != selected_persona:
    st.session_state["messages"] = []
    st.session_state["last_persona"] = selected_persona

st.markdown(f'<p class="hero-title">💬 與「{selected_persona}」的對話記憶互動</p>',
            unsafe_allow_html=True)
st.caption("直接詢問關於此人的任何問題，AI 將從 LINE 對話記憶中搜尋並回答。")

# 建議問題
SUGGESTED = [
    f"{selected_persona} 的性格特質是什麼？",
    "她有哪些近期的目標或煩惱？",
    "她喜歡哪些食物或娛樂？",
    "她的工作或學業背景？",
    "她重要的朋友或人際關係？",
]

st.markdown("**✨ 建議問題**")
cols = st.columns(3)
for i, q in enumerate(SUGGESTED):
    if cols[i % 3].button(q, key=f"suggest_{selected_persona}_{i}"):
        st.session_state["pending_question"] = q

st.divider()

# 顯示歷史訊息
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"📎 查看來源片段 ({len(msg['sources'])} 段)"):
                for i, src in enumerate(msg["sources"]):
                    st.markdown(f'<div class="source-chip">📌 <b>來源 {i+1}</b><br>{src}</div>',
                                unsafe_allow_html=True)

# 處理輸入
pending = st.session_state.pop("pending_question", None)
user_input = st.chat_input("輸入你的問題…") or pending

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            vector_db = load_db(selected_persona)
            with st.spinner("🔍 正在從記憶庫搜尋相關對話…"):
                answer, docs = rag_query(user_input, vector_db)

            st.markdown(answer)

            source_texts = [doc.page_content for doc in docs]
            with st.expander(f"📎 查看來源片段 ({len(source_texts)} 段)"):
                for i, src in enumerate(source_texts):
                    st.markdown(f'<div class="source-chip">📌 <b>來源 {i+1}</b><br>{src}</div>',
                                unsafe_allow_html=True)

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": source_texts,
            })

        except FileNotFoundError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"發生錯誤：{e}")
