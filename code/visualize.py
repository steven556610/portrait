import os
import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def generate_wordcloud(text_data: str, output_dir: str = "../visualize/", filename: str = "wordcloud.png"):
    """
    從文字資料產生文字雲，並將圖片存檔。
    """
    if not text_data.strip():
        print("[警告] 沒有可用的文字產生文字雲。")
        return
        
    # 確保資料夾存在
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)
    
    # 1. 使用 jieba 進行中文斷詞
    print("[文字雲] 正在進行中文斷詞...")
    words = jieba.cut(text_data, cut_all=False)
    
    # 過濾一些常見無意義的停用詞與單個字 (可以根據需求再擴充)
    stop_words = set(['的', '我', '你', '他', '是', '了', '在', '也', '有', '就', '不', '看', '去', '都', '好', '想', '要', '這', '說', '嗎', '吧', '啊', '哦', '嗯', '那', '跟', '會', '還', '因為', '所以', '不過', '還是', '可是', '其實', '然後', '大家', '知道'])
    filtered_words = [w for w in words if w not in stop_words and len(w) > 1]
    text_joined = " ".join(filtered_words)
    
    if not text_joined.strip():
        print("[警告] 過濾後沒有足夠的文字可以產生文字雲。")
        return
        
    print("[文字雲] 正在繪製並儲存圖片...")
    # 2. 定義字體路徑 (準備中文字體才不會有亂碼)
    # Windows 預設通常有微軟正黑體 (msjh.ttc) 或標楷體 (kaiu.ttf)
    font_path = "C:\\Windows\\Fonts\\msjh.ttc" 
    if not os.path.exists(font_path):
        font_path = "C:\\Windows\\Fonts\\kaiu.ttf"
        if not os.path.exists(font_path):
            font_path = None # 若都沒有就只能用預設(可能會有方塊亂碼)
            
    # 3. 產生文字雲
    wc = WordCloud(
        font_path=font_path,
        background_color="white",
        width=1000,
        height=800,
        max_words=150,
        colormap="plasma" # 配色方案
    )
    wc.generate(text_joined)
    
    # 4. 存檔
    plt.figure(figsize=(10, 8))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ 文字雲已成功儲存至 {output_path}")
