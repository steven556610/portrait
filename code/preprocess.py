import os
import re

# 你在不同對話中可能使用的顯示名稱清單（全部列在這裡）
YOUR_NAMES = ['小王']

def extract_person_name_from_filename(filename: str) -> str:
    """
    從 LINE 匯出的檔名中解析對象姓名。
    例如：
      '[LINE]小白.txt'                   -> '小白'
    """
    basename = os.path.basename(filename)
    # 格式一：[LINE] 與XXX的聊天.txt
    match = re.search(r'與(.+?)的聊天', basename)
    if match:
        return match.group(1).strip()
    # 格式二：[LINE]XXX.txt（無「與…的聊天」）
    match = re.search(r'\[LINE\](.+?)\.txt', basename)
    if match:
        return match.group(1).strip()
    # Fallback：直接取副檔名前的名稱
    return os.path.splitext(basename)[0].strip()


def preprocess_line_data(file_path: str, target_name: str = None,
                         your_names: list = None) -> str:
    """
    從 LINE 匯出檔中提取特定對象的發言。

    Args:
        file_path:    LINE 匯出的 .txt 檔路徑
        target_name:  想擷取的對象名稱。若為 None，則自動從檔名解析。
        your_names:   要排除的你自己的名字清單（多個別名都可以列進來）。
                      預設使用模組層級的 YOUR_NAMES。
    """
    if target_name is None:
        target_name = extract_person_name_from_filename(file_path)

    if your_names is None:
        your_names = YOUR_NAMES

    cleaned_messages = []
    skip_keywords = ["貼圖", "圖片", "照片", "已收回訊息", "語音訊息", "視訊通話", "通話時間"]

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # 排除你自己的訊息
            is_your_message = any(name in line for name in your_names)
            if is_your_message:
                continue

            # 判斷是否包含目標對象名稱
            if target_name in line:
                parts = line.split(target_name, 1)
                if len(parts) == 2:
                    message = parts[1].strip()
                    # 過濾系統型訊息
                    if message and not any(kw in message for kw in skip_keywords):
                        cleaned_messages.append(message)

    return "\n".join(cleaned_messages)
