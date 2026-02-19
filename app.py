import streamlit as st
import google.generativeai as genai
from PIL import Image
import io

# ... (保留您原本的 set_page_config 和樣式設定) ...

# --- 側邊欄增加 API Key 輸入與 AI 選項 ---
with st.sidebar:
    st.markdown("---")
    st.subheader("🤖 AI 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password")
    
    # 將 AI 選項加入原本的 app_mode 清單中
    # 注意：請將此選項加入您原本的 app_mode 列表最後
    # 例如： ["子宮內膜癌...", ..., "外陰癌 (Vulvar)", "🤖 AI 智慧判讀"]

# 假設您已經將 "🤖 AI 智慧判讀" 加入了 app_mode 的選項中
# ... (原本的 if/elif 判斷式) ...

# --- 新增：AI 智慧判讀區塊 ---
if app_mode == "🤖 AI 智慧判讀":
    st.header("🤖 AI 智慧病理報告判讀 (Experimental)")
    st.warning("⚠️ 注意：此功能僅供輔助，請勿上傳包含真實病患姓名、身分證號等隱私個資的圖片。AI 判讀結果需由醫師再次確認。")

    if not api_key:
        st.error("請先在側邊欄輸入 Google Gemini API Key 才能使用此功能。")
    else:
        # 設定 Gemini client
        genai.configure(api_key=api_key)
        
        # 檔案上傳區
        uploaded_files = st.file_uploader(
            "請上傳病理報告 (支援圖片 JPG/PNG 或 文字檔 TXT)", 
            accept_multiple_files=True, 
            type=['png', 'jpg', 'jpeg', 'txt']
        )

        # 選擇癌症類型以提供 AI 上下文
        cancer_context = st.selectbox("請選擇報告的癌症類型 (協助 AI 更精準對照)", 
            ["子宮內膜癌", "卵巢癌", "子宮頸癌", "子宮惡性肉瘤", "外陰癌", "陰道癌", "GTN", "自動判斷"])

        analyze_btn = st.button("開始 AI 分析")

        if analyze_btn and uploaded_files:
            with st.spinner('AI 正在仔細閱讀病理報告並進行分期運算...'):
                try:
                    # 準備 Prompt (指令)
                    model = genai.GenerativeModel('gemini-1.5-flash') # 使用 Flash 模型速度快且便宜，或改用 'gemini-1.5-pro' 更精準
                    
                    prompt_parts = [
                        f"""
                        你是一位專業的婦科腫瘤科醫師。請分析以下上傳的病理報告資料。
                        目前的癌症類型上下文為：{cancer_context}。
                        
                        請執行以下任務：
                        1. **摘要關鍵發現**：提取腫瘤大小(Tumor size)、侵犯深度(Invasion depth)、淋巴結狀態(Lymph node status)、遠端轉移(Metastasis)、組織學型態(Histology)等關鍵資訊。
                        2. **判定分期**：根據 FIGO (最新版) 與 AJCC TNM 系統進行分期判定。請詳細解釋判定的理由（例如：因為侵犯了膀胱黏膜，所以判定為 T4...）。
                        3. **表格整理**：請以 Markdown 表格列出 T, N, M 的判定結果。
                        
                        如果報告資訊不足以判定完整分期，請指出缺少哪些關鍵資訊。
                        請用繁體中文回答。
                        """
                    ]

                    # 處理上傳的檔案
                    for uploaded_file in uploaded_files:
                        if uploaded_file.type.startswith('image'):
                            image_data = Image.open(uploaded_file)
                            prompt_parts.append(image_data)
                        elif uploaded_file.type == 'text/plain':
                            text_data = uploaded_file.read().decode("utf-8")
                            prompt_parts.append(f"病理報告文字內容：\n{text_data}")

                    # 發送給 Gemini
                    response = model.generate_content(prompt_parts)
                    
                    # 顯示結果
                    st.markdown("### 📋 AI 分析結果")
                    st.markdown(response.text)
                    
                    st.success("分析完成！請核對上方資訊是否與您的臨床判斷一致。")

                except Exception as e:
                    st.error(f"發生錯誤：{str(e)}")
                    st.info("請確認 API Key 是否正確，或是圖片是否清晰。")
