from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# 定義想要提取的資料結構
class Persona(BaseModel):
    personality: list = Field(description="性格特質、MBTI傾向、溝通風格或核心價值觀的清單，若無則傳回空陣列")
    relationships: list = Field(description="提及的重要家庭成員、朋友、同事或人際圈關係的清單，若無則傳回空陣列")
    likes: list = Field(description="包含喜歡吃什麼、做什麼、欣賞哪種特質的清單，若無則傳回空陣列")
    dislikes: list = Field(description="包含討厭、抗拒或不感興趣的事物與行為的清單，若無則傳回空陣列")
    experiences: list = Field(description="包含人生經歷、去過的地方、工作與學業過往的清單，若無則傳回空陣列")
    possessions: list = Field(description="包含擁有的重要物品或資產的清單，若無則傳回空陣列")
    interests: list = Field(description="包含感興趣的主題、影視音樂、遊戲或嗜好的清單，若無則傳回空陣列")
    goals_and_concerns: list = Field(description="包含現階段的人生規劃、近期目標、或是正在煩惱擔憂的事，若無則傳回空陣列")

def extract_info(text: str):
    """
    方案 B：核心資訊提取 (使用 LangChain + Ollama Qwen)
    優化提示詞，強調「長期價值」與「結構化」。
    """
    llm = ChatOllama(model="qwen2.5:14b", temperature=0.2)
    parser = JsonOutputParser(pydantic_object=Persona)
    
    # 這裡幫你整理和優化了提示詞 (Prompt)
    prompt = ChatPromptTemplate.from_template(
        "你是一個經驗豐富的心理學家與人物誌(Persona)分析專家。\n"
        "請閱讀以下 LINE 對話紀錄，提取關於該發言者的深度背景資訊。\n\n"
        "【重要處理原則】\n"
        "1. 請區分短期意圖（如：明天想吃壽司）與長期特質（如：是個海鮮控），僅保留具有「長期參考價值」的資訊。\n"
        "2. 不要捏造資訊，如果紀錄中完全沒有符合某個欄位的內容，請直接返回空陣列。\n"
        "3. 在「性格特質」與「近期煩惱」部分，可以根據對方的說話內容與遇到事件時的反應進行合理、適度的心理推論（例如：完美主義、易焦慮、喜歡照顧人等）。\n"
        "4. 請嚴格依照下方指定的 JSON 格式回傳，不要加入任何其他文字解釋。\n"
        "5. **⚠️非常重要：請務必全部使用「繁體中文」填寫分析內容，絕對不可以輸出英文。**\n\n"
        "【格式限制】\n"
        "{format_instructions}\n\n"
        "【對話內容】\n"
        "{context}"
    )
    
    chain = prompt | llm | parser
    return chain.invoke({
        "context": text, 
        "format_instructions": parser.get_format_instructions()
    })
