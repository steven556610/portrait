# Portrait - LINE 聊天記錄人物誌分析器

這是一個基於 **LangChain** 構建的 LINE 聊天記錄分析專案。它可以幫助你把龐雜的 LINE 聊天內容提煉為結構化的人物誌 (Persona) 資料，甚至提供類似「記憶」的自然語言互動介面。

## 🔒 隱私與資安聲明 (必讀)
**請注意！** LINE 對話紀錄包含高度隱私與您的個人資料。
本專案的 `.gitignore` 已經預設排除了 `data/` (存放原絕對話與報告)、`model/` (存放向量資料庫) 以及 `.env` (存放API金鑰)，以確保您的隱私不會被意外上傳到外部資料庫。
**在將此專案 Push 到 GitHub 等公開平台時，請務必確認沒有任何含有個人資訊的檔案被加入版控系統中！** 所有分析過程與對話內容依賴皆應於本地端環境中執行。

## 功能亮點
* **視覺化分析:** 加入了 `wordcloud` 與 `jieba` 分詞技術，在進行 AI 解析前，會先萃取對話高頻詞彙，並渲染出專屬的文字雲報表儲存至 `visualize/` 目錄。
* **核心抽取能力:** 使用 Google 的 `gemini-2.5-flash` 從聊天的龐大紀錄中，精準提取目標對象的八個維度：性格特質、近期目標、喜好、厭惡、過往經歷、人際網絡、擁有資產、興趣嗜好。
* **專屬向量記憶庫:** 將匯出的對話切分成段落，存取至地端的 ChromaDB 向量庫，讓 AI 擁有針對特定人物的「長期記憶」。
* **互動式對話介面:** 提供 Streamlit 打造的 NotebookLM 風格互動網頁，你可以直接用自然語言與已儲存的專屬記憶進行查詢、互動。

## 目錄結構
```
portrait/
├── code/
│   ├── preprocess.py        # 資料清洗與文字過濾模組
│   ├── extractor.py         # Gemini JSON 解析與屬性提取
│   ├── memory.py            # RAG 向量記憶引擎模組
│   ├── visualize.py         # 文字雲生成模組
│   ├── main.py              # 主程式 Orchestrator (分析與建庫入口)
│   └── app.py               # Streamlit 互動介面入口
├── data/
│   ├── (這裡放你的 LINE .txt) # ★ 從 LINE 匯出的文字資料檔案請放在這
│   └── reports/             # 自動生成的人物誌分析 Markdown 報告存放處
├── model/                   
│   └── chroma_db/           # ChromaDB 建立的對話記憶向量庫目錄
├── visualize/               # 存放自動生成的對話文字雲圖片
├── README.md                # 專案說明書
├── requirements.txt         # 執行專案所需的依賴套件清單
└── .env                     # 存放環境變數 (需自行建立以放置 API_KEY)
```

## 🚀 快速上手教學

### 1. 安裝環境與套件
建議使用虛擬環境 (如 conda、venv) 來管理專案依賴。
```powershell
# 如果你有使用 Conda
# conda create -n portrait python=3.10
# conda activate portrait

# 安裝所需依賴套件
pip install -r requirements.txt
```

### 2. 環境變數設定
在專案的 **根目錄** (亦即與 README.md 同一層) 下建立一個名為 `.env` 的純文字檔案，寫入你的 Gemini API Key：
```env
GOOGLE_API_KEY=你的實體_GEMINI_API_KEY
```
*(注意：此檔案已被 `.gitignore` 略過，請放心寫入您的 Key 不會被上傳)*

### 3. 如何放置你的 LINE 對話記錄？
1. 從手機版或電腦版的 LINE 中，將你想分析的歷史對話紀錄匯出為純文字 (`.txt`) 格式。
2. 將這些 `.txt` 檔案直接放入專案下的 `data/` 目錄中。
    * 範例檔名：`[LINE] 聊天紀錄.txt` 或 `小白.txt`

### 4. 執行分析與建立記憶庫
將資料檔放好後，執行主程式，它會自動為你解析人物並建立資料庫：
```powershell
cd code
python main.py --build-all
```
系統將依序自動完成：
- 由檔名與內容解析人物對象。
- 在 `model/<人名>/chroma_db/` 獨立建立個人專屬的記憶片段向量庫。
- 於 `data/reports/` 產出個人專屬人物誌分析報告 (`.md`)。
- 於 `visualize/` 產生該人物的對話文字雲圖像。

### 5. 啟動互動式對話介面 (Web UI)
待記憶庫建立與分析分析皆完成後，你可以隨時啟動網頁介面來「查詢」內容：
```powershell
cd code
streamlit run app.py
```
執行後，瀏覽器將自動為您開啟 `http://localhost:8501`。
- **選擇對象**：從左側側邊欄選擇你要對話的人物。
- **檢視報告**：側邊欄會即時顯示針對該目標預先解析好的摘要報告。
- **開始聊天**：在聊天框輸入具體問題，例如：「她最近有提到想吃什麼嗎？」或「她的興趣是什麼？」，AI 將會根據專屬向量庫給出經過整理的答案並附上來源參考！
