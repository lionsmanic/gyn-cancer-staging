import streamlit as st
import requests
import json
import base64
from PIL import Image
import io

# ... (保留前面的程式碼) ...

# --- 修改後的 AI 區塊 (不使用 google-generative-ai 套件) ---
if app_mode == "🤖 AI 智慧判讀":
    st.header("🤖 AI 智慧病理報告判讀 (Direct API Mode)")
    st.warning("⚠️ 注意：此功能僅供輔助，請勿上傳包含真實病患姓名、身分證號等隱私個資的圖片。")

    if not api_key:
        st.error("請先在側邊欄輸入 Gemini API Key。")
    else:
        # 檔案上傳
        uploaded_files = st.file_uploader(
            "請上傳病理報告 (圖片)", 
            accept_multiple_files=True, 
            type=['png', 'jpg', 'jpeg']
        )
        
        cancer_context = st.selectbox("癌症類型上下文", 
            ["子宮內膜癌", "卵巢癌", "子宮頸癌", "子宮惡性肉瘤", "外陰癌", "陰道癌", "GTN", "自動判斷"])

        analyze_btn = st.button("開始 AI 分析")

        if analyze_btn and uploaded_files:
            with st.spinner('AI 正在分析 (Direct API)...'):
                try:
                    # 準備 Prompt
                    prompt_text = f"""
                    你是一位專業的婦科腫瘤科醫師。目前的癌症類型上下文為：{cancer_context}。
                    請分析圖片中的病理報告，提取腫瘤大小、侵犯深度、淋巴結狀態、遠端轉移等資訊。
                    根據 FIGO 與 AJCC TNM 系統判定分期，並以 Markdown 表格呈現 T, N, M 結果。
                    請用繁體中文回答。
                    """

                    # 構建 Request Body
                    contents_parts = [{"text": prompt_text}]
                    
                    for uploaded_file in uploaded_files:
                        # 轉成 base64
                        bytes_data = uploaded_file.getvalue()
                        base64_image = base64.b64encode(bytes_data).decode('utf-8')
                        contents_parts.append({
                            "inline_data": {
                                "mime_type": uploaded_file.type,
                                "data": base64_image
                            }
                        })

                    payload = {
                        "contents": [{"parts": contents_parts}]
                    }

                    # 直接呼叫 API
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    
                    response = requests.post(url, headers=headers, data=json.dumps(payload))
                    
                    if response.status_code == 200:
                        result = response.json()
                        try:
                            answer = result['candidates'][0]['content']['parts'][0]['text']
                            st.markdown("### 📋 AI 分析結果")
                            st.markdown(answer)
                        except:
                            st.error("無法解析 AI 回傳的資料")
                            st.json(result)
                    else:
                        st.error(f"API 呼叫失敗: {response.status_code}")
                        st.text(response.text)

                except Exception as e:
                    st.error(f"發生錯誤：{str(e)}")
