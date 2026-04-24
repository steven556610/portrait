import os
import sys
import glob
from dotenv import load_dotenv

from preprocess import preprocess_line_data, extract_person_name_from_filename, YOUR_NAMES
from extractor import extract_info
from memory import setup_vector_db, query_persona_rag_gemini
from visualize import generate_wordcloud

load_dotenv()

# -----------------------------------------------------------------------
# 輸出路徑設定
# -----------------------------------------------------------------------
ROOT_DIR     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA_DIR     = os.path.join(ROOT_DIR, "data")
REPORTS_DIR  = os.path.join(DATA_DIR, "reports")
MODEL_DIR    = os.path.join(ROOT_DIR, "model")
VIS_DIR      = os.path.join(ROOT_DIR, "visualize")

# 每個人的向量庫存放於 model/<人名>/chroma_db
def get_db_dir(person_name: str) -> str:
    return os.path.join(MODEL_DIR, person_name, "chroma_db")

def get_report_path(person_name: str) -> str:
    return os.path.join(REPORTS_DIR, f"{person_name}.md")

# -----------------------------------------------------------------------
# Markdown 報告寫入
# -----------------------------------------------------------------------
def save_to_markdown(data: dict, output_path: str, person_name: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# 深度人物誌 (Persona) 分析報告：{person_name}\n\n")
        f.write(f"## 💡 核心性格與價值觀\n- {', '.join(data.get('personality', []))}\n\n")
        f.write(f"## 🎯 近期目標與煩惱\n- {', '.join(data.get('goals_and_concerns', []))}\n\n")
        f.write(f"## 🍔 飲食與一般喜好\n- 喜歡：{', '.join(data.get('likes', []))}\n- 不喜歡：{', '.join(data.get('dislikes', []))}\n\n")
        f.write(f"## 📖 興趣與嗜好\n- {', '.join(data.get('interests', []))}\n\n")
        f.write(f"## 🏃 經歷與過往\n- {', '.join(data.get('experiences', []))}\n\n")
        f.write(f"## 👥 人際網絡\n- {', '.join(data.get('relationships', []))}\n\n")
        f.write(f"## 🎒 擁有資產與標誌性物品\n- {', '.join(data.get('possessions', []))}\n\n")
    print(f"  ✅ 報告已儲存至 {output_path}")

# -----------------------------------------------------------------------
# 單一人物完整分析流程
# -----------------------------------------------------------------------
def build_persona(file_path: str, max_chars: int = 240000):
    person_name = extract_person_name_from_filename(file_path)
    db_dir      = get_db_dir(person_name)
    report_path = get_report_path(person_name)

    print(f"\n{'='*55}")
    print(f"  🔍 分析對象: {person_name}")
    print(f"{'='*55}")

    # [1] 預處理
    print("  [1/4] 萃取對話文字...")
    text_data = preprocess_line_data(file_path)
    if not text_data:
        print(f"  ⚠️  未能從 {file_path} 擷取到有效訊息，略過。")
        return

    # 截取最大字元數，避免超出 Token 限制
    if len(text_data) > max_chars:
        print(f"  ℹ️  文字過長 ({len(text_data):,} 字)，截取前 {max_chars:,} 字進行分析。")
        text_data = text_data[:max_chars]
    else:
        print(f"  ✓  擷取 {len(text_data):,} 字元的有效訊息。")

    # [2] 文字雲
    print("  [2/4] 繪製文字雲...")
    os.makedirs(VIS_DIR, exist_ok=True)
    generate_wordcloud(text_data, output_dir=VIS_DIR,
                       filename=f"{person_name}_wordcloud.png")

    # [3] Ollama 萃取
    print("  [3/4] Ollama (Local) 結構化萃取...")
    extracted_data = extract_info(text_data)
    save_to_markdown(extracted_data, report_path, person_name)

    # [4] 建立 ChromaDB
    print(f"  [4/4] 建立向量記憶庫 -> {db_dir} ...")
    os.makedirs(os.path.dirname(db_dir), exist_ok=True)
    setup_vector_db(text_data, db_dir)
    print(f"  ✅ {person_name} 資料庫建立完成！")

# -----------------------------------------------------------------------
# CLI 入口
# -----------------------------------------------------------------------
if __name__ == "__main__":
    # API_KEY 已不再強制需要，改用在地端 Ollama
    # API_KEY = os.environ.get("GOOGLE_API_KEY", "")

    build_all = "--build-all" in sys.argv

    if build_all:
        # 自動掃描所有 LINE 對話檔
        pattern = os.path.join(DATA_DIR, "[LINE]*.txt") 
        # 也匹配帶空格的格式
        pattern2 = os.path.join(DATA_DIR, "[[]LINE[]]*.txt")
        files = glob.glob(os.path.join(DATA_DIR, "*.txt"))
        line_files = [f for f in files if os.path.basename(f).startswith("[LINE]")]

        if not line_files:
            print("[錯誤] 在 data/ 目錄下找不到任何 [LINE]*.txt 檔案")
            sys.exit(1)

        print(f"=== 批次建立模式：共發現 {len(line_files)} 個對話檔案 ===")
        for i, fpath in enumerate(line_files, 1):
            print(f"\n[{i}/{len(line_files)}] {os.path.basename(fpath)}")
            try:
                build_persona(fpath)
            except Exception as e:
                print(f"  ❌ 發生錯誤：{e}")
        print("\n\n🎉 所有對象分析完畢！")

    else:
        # 單人模式（與原本相同）
        DATA_PATH   = "../data/[LINE]家妤☆.txt"
        person_name = extract_person_name_from_filename(DATA_PATH)
        db_dir      = get_db_dir(person_name)

        print("=== Address Line Content - 人物誌整合分析系統 ===")
        print(f"目標對象：{person_name}")
        print(f"你的名字過濾清單：{YOUR_NAMES}")

        text_data = preprocess_line_data(DATA_PATH)
        if not text_data:
            print("[錯誤] 無法擷取有效訊息")
            sys.exit(1)

        print(f"擷取 {len(text_data):,} 字元 | 開始全流程分析...")
        build_persona(os.path.join(os.path.dirname(__file__), DATA_PATH))

        # RAG 測試查詢
        from memory import load_vector_db
        vector_db = load_vector_db(db_dir)
        question = "她最近有說喜歡吃什麼或討厭什麼嗎？"
        print(f"\n🧐 測試問題: {question}")
        answer = query_persona_rag_gemini(question, vector_db)
        print(f"🤖 回答: {answer}")
