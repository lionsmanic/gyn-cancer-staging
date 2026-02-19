import streamlit as st
import requests
import json
import base64
from PIL import Image
import io

# 設定頁面配置
st.set_page_config(
    page_title="婦癌分期輔助系統",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 標題樣式
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    h1 {
        color: #2c3e50;
    }
    .stButton>button {
        width: 100%;
        background-color: #008080;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 婦癌臨床分期輔助系統")
st.markdown("### Integrated Gynecologic Oncology Staging Tool")

# 側邊欄導航
with st.sidebar:
    st.title("導航選單")
    app_mode = st.radio("請選擇功能：",
        ["子宮內膜癌 (Endometrial)", 
         "卵巢癌 (Ovarian)", 
         "子宮頸癌 (Cervical)", 
         "子宮惡性肉瘤 (Sarcoma)", 
         "外陰黑色素瘤 (Vulvar Melanoma)", 
         "陰道癌 (Vaginal)", 
         "妊娠滋養層細胞腫瘤 (GTN)",
         "外陰癌 (Vulvar)",
         "🤖 AI 智慧判讀 (Beta)"]
    )
    
    st.markdown("---")
    st.subheader("🤖 AI 設定")
    api_key = st.text_input("輸入 Gemini API Key", type="password", help="請輸入 Google Gemini API Key 以啟用 AI 判讀功能")
    
    # 測試按鈕 (保留供除錯用)
    if api_key:
        if st.button("🔍 測試 API Key"):
            try:
                test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
                test_res = requests.get(test_url)
                if test_res.status_code == 200:
                    models = test_res.json().get('models', [])
                    model_names = [m['name'].replace('models/', '') for m in models if 'gemini' in m['name']]
                    st.success("✅ API Key 有效！")
                    st.json(model_names) # 顯示支援的模型清單
                else:
                    st.error(f"❌ API Key 無效 (Code: {test_res.status_code})")
            except Exception as e:
                st.error(f"連線錯誤: {e}")

    st.info("資料來源：根據 FIGO 與 AJCC TNM 系統整合。")

# --- 1. 子宮內膜癌 ---
if app_mode == "子宮內膜癌 (Endometrial)":
    st.header("子宮內膜癌分期 (Endometrial Cancer)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        histology_type = st.radio("組織學型態", 
            ['非兇險 (non-aggressive): Low grade (G1/G2) endometrioid',
             '兇險 (aggressive): Serous, Clear cell, Undifferentiated, Carcinosarcoma, High-grade endometrioid (G3)'])
        
        myometrial_invasion = st.radio("子宮肌層侵犯深度", ['無侵犯', '<50%', '≥50%'])
        
        lvsi = st.radio("血管或淋巴管侵犯 (LVSI)", 
            ['無侵犯', '輕微侵犯(focal)', '大量侵犯(extensive, ≥5 vessels)'])
        
        lymph_node_size = st.radio("淋巴結轉移大小", 
            ['無', '微轉移 (micrometastasis): 0.2-2 mm', '巨轉移 (macrometastasis): >2 mm'])

    with col2:
        st.subheader("侵犯範圍勾選")
        cervical_stroma = st.checkbox('宮頸間質侵犯')
        ovarian_tubal = st.checkbox('卵巢或輸卵管侵犯')
        ovarian_limited = st.checkbox('卵巢腫瘤單側侷限無破裂')
        serosa = st.checkbox('漿膜侵犯')
        vaginal_parametrial = st.checkbox('陰道或子宮旁侵犯')
        pelvic_peritoneum = st.checkbox('骨盆腹膜侵犯')
        upper_abd_peritoneum = st.checkbox('骨盆以上腹腔腹膜侵犯')
        bladder_intestinal = st.checkbox('膀胱或腸黏膜侵犯')
        distant_meta = st.checkbox('遠處轉移 (含腹腔外淋巴結、肺、肝、腦、骨等)')
        
        st.subheader("淋巴結與分子特徵")
        pelvic_ln = st.checkbox('骨盆淋巴結轉移')
        pa_ln = st.checkbox('主動脈旁淋巴結轉移')
        pole_mut = st.checkbox('POLE mutation')
        p53_abn = st.checkbox('p53 abnormal')

    if st.button("計算分期"):
        T_stage = 'T1a' if myometrial_invasion in ['無侵犯', '<50%'] else 'T1b'
        N_stage = 'N0'
        M_stage = 'M0'

        if cervical_stroma: T_stage = 'T2'
        if serosa or ovarian_tubal or ovarian_limited: T_stage = 'T3a'
        if vaginal_parametrial or pelvic_peritoneum: T_stage = 'T3b'
        if bladder_intestinal: T_stage = 'T4'

        if pelvic_ln: N_stage = 'N1mi' if '微轉移' in lymph_node_size else 'N1a'
        if pa_ln: N_stage = 'N2mi' if '微轉移' in lymph_node_size else 'N2a'
        
        if distant_meta: M_stage = 'M1'

        result = ""
        if pole_mut and T_stage in ['T1a', 'T1b', 'T2'] and N_stage == 'N0' and M_stage == 'M0':
            result = f'FIGO stage IAmPOLEmut, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif p53_abn and T_stage in ['T1a', 'T1b', 'T2'] and N_stage == 'N0' and M_stage == 'M0':
            result = f'FIGO stage IICmp53abn, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif distant_meta:
            result = f'FIGO stage 4C, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif upper_abd_peritoneum:
            result = f'FIGO stage 4B, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif T_stage == 'T4':
            result = f'FIGO stage 4A, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif N_stage == 'N2mi':
            result = f'FIGO stage 3C2i, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif N_stage == 'N2a':
            result = f'FIGO stage 3C2ii, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif N_stage == 'N1mi':
            result = f'FIGO stage 3C1i, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif N_stage == 'N1a':
            result = f'FIGO stage 3C1ii, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif serosa:
            result = f'FIGO stage 3A2, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif ovarian_tubal or ovarian_limited:
            if ovarian_limited and myometrial_invasion in ['無侵犯', '<50%'] and lvsi in ['無侵犯', '輕微侵犯(focal)'] and not any([serosa, vaginal_parametrial, pelvic_peritoneum, pelvic_ln, pa_ln, bladder_intestinal, distant_meta, upper_abd_peritoneum]):
                result = f'FIGO stage 1A3, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
            else:
                result = f'FIGO stage 3A1, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif vaginal_parametrial and not any([pelvic_peritoneum, pelvic_ln, pa_ln, upper_abd_peritoneum, bladder_intestinal, distant_meta]):
            result = f'FIGO stage 3B1, AJCC TNM stage T3b {N_stage} {M_stage}'
        elif pelvic_peritoneum and not any([pelvic_ln, pa_ln, upper_abd_peritoneum, bladder_intestinal, distant_meta]):
            result = f'FIGO stage 3B2, AJCC TNM stage T3b {N_stage} {M_stage}'
        elif histology_type.startswith('兇險') and myometrial_invasion != '無侵犯':
            result = f'FIGO stage 2C, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif cervical_stroma:
             if histology_type.startswith('非兇險'):
                result = f'FIGO stage 2A, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif lvsi.startswith('大量侵犯') and histology_type.startswith('非兇險'):
            result = f'FIGO stage 2B, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif histology_type.startswith('非兇險'):
            if myometrial_invasion == '≥50%':
                result = f'FIGO stage 1B, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
            elif myometrial_invasion == '<50%' and '大量侵犯' not in lvsi:
                result = f'FIGO stage 1A2, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
            elif myometrial_invasion == '無侵犯' and '大量侵犯' not in lvsi:
                result = f'FIGO stage 1A1, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        elif histology_type.startswith('兇險') and myometrial_invasion == '無侵犯':
            result = f'FIGO stage 1C, AJCC TNM stage {T_stage} {N_stage} {M_stage}'
        else:
            result = '需進一步評估 (資料組合未涵蓋於標準路徑)'

        st.success(f"判定結果：{result}")

# --- 2. 卵巢癌 ---
elif app_mode == "卵巢癌 (Ovarian)":
    st.header("卵巢癌分期 (Ovarian Cancer)")
    
    TNM_dict = {
        "單側卵巢、輸卵管未破裂 (T1a)": "T1a", "雙側卵巢、輸卵管未破裂 (T1b)": "T1b",
        "手術時腫瘤溢出 (T1c1)": "T1c1", "術前破裂或腫瘤於卵巢、輸卵管表面 (T1c2)": "T1c2",
        "腹水或腹膜沖洗細胞學陽性 (T1c3)": "T1c3", "子宮或輸卵管轉移 (T2a)": "T2a",
        "其他骨盆組織轉移 (T2b)": "T2b", "腹腔顯微轉移 (T3a)": "T3a",
        "腹腔轉移 ≤ 2 cm (T3b)": "T3b", "腹腔轉移 > 2 cm (T3c)": "T3c",
        "無淋巴結轉移 (N0)": "N0", "腹膜後淋巴結轉移 ≤ 10 mm (N1a)": "N1a",
        "腹膜後淋巴結轉移 > 10 mm (N1b)": "N1b", "無遠端轉移 (M0)": "M0",
        "胸水細胞學陽性 (M1a)": "M1a", "肝脾實質或腹外器官轉移 (M1b)": "M1b"
    }

    t_input = st.selectbox("原發腫瘤 (Primary Tumor)", list(TNM_dict.keys())[:10])
    n_input = st.selectbox("淋巴結轉移 (Lymph Nodes)", list(TNM_dict.keys())[10:13])
    m_input = st.selectbox("遠端轉移 (Metastasis)", list(TNM_dict.keys())[13:])

    if st.button("計算分期"):
        stage = "請確認輸入資料是否完整或正確"
        if m_input == "胸水細胞學陽性 (M1a)": stage = "Stage IVA"
        elif m_input == "肝脾實質或腹外器官轉移 (M1b)": stage = "Stage IVB"
        elif n_input == "腹膜後淋巴結轉移 ≤ 10 mm (N1a)": stage = "Stage IIIA1i"
        elif n_input == "腹膜後淋巴結轉移 > 10 mm (N1b)": stage = "Stage IIIA1ii"
        elif t_input == "腹腔顯微轉移 (T3a)": stage = "Stage IIIA2"
        elif t_input == "腹腔轉移 ≤ 2 cm (T3b)": stage = "Stage IIIB"
        elif t_input == "腹腔轉移 > 2 cm (T3c)": stage = "Stage IIIC"
        elif t_input == "子宮或輸卵管轉移 (T2a)": stage = "Stage IIA"
        elif t_input == "其他骨盆組織轉移 (T2b)": stage = "Stage IIB"
        elif t_input == "單側卵巢、輸卵管未破裂 (T1a)": stage = "Stage IA"
        elif t_input == "雙側卵巢、輸卵管未破裂 (T1b)": stage = "Stage IB"
        elif t_input == "手術時腫瘤溢出 (T1c1)": stage = "Stage IC1"
        elif t_input == "術前破裂或腫瘤於卵巢、輸卵管表面 (T1c2)": stage = "Stage IC2"
        elif t_input == "腹水或腹膜沖洗細胞學陽性 (T1c3)": stage = "Stage IC3"
        
        tnm_res = f"{TNM_dict[t_input]} {TNM_dict[n_input]} {TNM_dict[m_input]}"
        st.success(f"{stage}")
        st.info(f"AJCC TNM: {tnm_res}")

# --- 3. 子宮頸癌 ---
elif app_mode == "子宮頸癌 (Cervical)":
    st.header("子宮頸癌分期 (Cervical Cancer)")
    
    t_ops = [
        "T1a1: Stromal invasion <3 mm", "T1a2: Stromal invasion 3-5 mm",
        "T1b1: Invasion ≥5 mm depth, <2 cm dimension", "T1b2: Dimension 2-4 cm",
        "T1b3: Dimension ≥4 cm", "T2a1: Vaginal involvement <4 cm",
        "T2a2: Vaginal involvement ≥4 cm", "T2b: Parametrial invasion",
        "T3a: Lower third vagina", "T3b: Pelvic wall/hydronephrosis",
        "T3c1: Pelvic LN metastasis", "T3c2: Paraaortic LN metastasis",
        "T4: Beyond true pelvis or biopsy-proven bladder/rectum mucosal involvement"
    ]
    n_ops = ["N0: No regional LN metastasis", "N0(i+): Isolated tumor cells ≤0.2 mm", "N1: Regional LN metastasis"]
    m_ops = ["M0: No distant metastasis", "M1: Distant metastasis"]

    t_val = st.selectbox("T Stage", t_ops)
    n_val = st.selectbox("N Stage", n_ops)
    m_val = st.selectbox("M Stage", m_ops)

    if st.button("計算分期"):
        T_code = t_val.split(':')[0]
        N_code = n_val.split(':')[0]
        M_code = m_val.split(':')[0]
        
        ajcc_stage = f"{T_code} {N_code} {M_code}"
        figo_stage = 'Cannot classify'

        if t_val.startswith('T4'):
            figo_stage = 'Stage IVA' if m_val.startswith('M0') else 'Stage IVB'
        elif m_val.startswith('M1'):
            figo_stage = 'Stage IVB'
        elif n_val.startswith(('N1', 'N0(i+)')):
            figo_stage = 'Stage IIIC'
        else:
            figo_dict = {
                'T1a1': 'Stage IA1', 'T1a2': 'Stage IA2', 'T1b1': 'Stage IB1',
                'T1b2': 'Stage IB2', 'T1b3': 'Stage IB3', 'T2a1': 'Stage IIA1',
                'T2a2': 'Stage IIA2', 'T2b': 'Stage IIB', 'T3a': 'Stage IIIA',
                'T3b': 'Stage IIIB', 'T3c1': 'Stage IIIC1', 'T3c2': 'Stage IIIC2'
            }
            figo_stage = figo_dict.get(T_code, 'Cannot classify')
        
        st.success(f"FIGO Stage: {figo_stage}")
        st.info(f"AJCC Stage: {ajcc_stage}")

# --- 4. 子宮惡性肉瘤 ---
elif app_mode == "子宮惡性肉瘤 (Sarcoma)":
    st.header("子宮惡性肉瘤分期 (Uterine Sarcoma)")
    
    sarcoma_type = st.radio("Sarcoma Type", 
                            ['Leiomyosarcoma', 'Endometrial Stromal Sarcoma', 'Mullerian Adenosarcoma'])

    t_choices = []
    if sarcoma_type in ['Leiomyosarcoma', 'Endometrial Stromal Sarcoma']:
        t_choices = ['T1a (≤5 cm)', 'T1b (>5 cm)', 'T2a (adnexa)', 'T2b (pelvic tissues)',
                     'T3a (one abdominal site)', 'T3b (>one abdominal site)', 'T4 (bladder/rectum)']
    else:
        t_choices = ['T1a (endometrium/endocervix)', 'T1b (≤half myometrial invasion)',
                     'T1c (>half myometrial invasion)', 'T2a (adnexa)', 'T2b (pelvic tissues)',
                     'T3a (one abdominal site)', 'T3b (>one abdominal site)', 'T4 (bladder/rectum)']
    
    col1, col2 = st.columns(2)
    with col1:
        t_stage = st.selectbox("T Stage", t_choices)
    with col2:
        n_stage = st.selectbox("N Stage", ['N0 (No regional lymph node metastasis)', 'N1 (Regional lymph node metastasis)'])
        m_stage = st.selectbox("M Stage", ['M0 (No distant metastasis)', 'M1 (Distant metastasis)'])

    if st.button("計算分期"):
        tnm = f"AJCC TNM: {t_stage.split()[0]} {n_stage.split()[0]} {m_stage.split()[0]}"
        result_stage = ""

        if m_stage.startswith("M1"):
            result_stage = "FIGO Stage: IVB"
        elif n_stage.startswith("N1"):
            result_stage = "FIGO Stage: IIIC"
        else:
            stages_map = {
                'Leiomyosarcoma': {
                    'T1a (≤5 cm)': "IA", 'T1b (>5 cm)': "IB", 'T2a (adnexa)': "IIA",
                    'T2b (pelvic tissues)': "IIB", 'T3a (one abdominal site)': "IIIA",
                    'T3b (>one abdominal site)': "IIIB", 'T4 (bladder/rectum)': "IVA"
                },
                'Endometrial Stromal Sarcoma': {
                    'T1a (≤5 cm)': "IA", 'T1b (>5 cm)': "IB", 'T2a (adnexa)': "IIA",
                    'T2b (pelvic tissues)': "IIB", 'T3a (one abdominal site)': "IIIA",
                    'T3b (>one abdominal site)': "IIIB", 'T4 (bladder/rectum)': "IVA"
                },
                'Mullerian Adenosarcoma': {
                    'T1a (endometrium/endocervix)': "IA", 'T1b (≤half myometrial invasion)': "IB",
                    'T1c (>half myometrial invasion)': "IC", 'T2a (adnexa)': "IIA",
                    'T2b (pelvic tissues)': "IIB", 'T3a (one abdominal site)': "IIIA",
                    'T3b (>one abdominal site)': "IIIB", 'T4 (bladder/rectum)': "IVA"
                }
            }
            result_stage = f"FIGO Stage: {stages_map[sarcoma_type].get(t_stage, 'Stage Not Defined')}"
        
        st.success(result_stage)
        st.info(tnm)

# --- 5. 外陰黑色素瘤 ---
elif app_mode == "外陰黑色素瘤 (Vulvar Melanoma)":
    st.header("外陰黑色素瘤分期 (Vulvar Melanoma)")
    
    t_ops = ["Tis (原位癌)", "T1a (腫瘤<0.8mm，無潰瘍)", "T1b (腫瘤<0.8mm，有潰瘍或0.8-1.0mm無論有無潰瘍)",
             "T2a (腫瘤>1.0-2.0mm，無潰瘍)", "T2b (腫瘤>1.0-2.0mm，有潰瘍)", "T3a (腫瘤>2.0-4.0mm，無潰瘍)",
             "T3b (腫瘤>2.0-4.0mm，有潰瘍)", "T4a (腫瘤>4.0mm，無潰瘍)", "T4b (腫瘤>4.0mm，有潰瘍)"]
    n_ops = ["N0 (無區域淋巴結轉移)", "N1a (單一隱匿性轉移淋巴結)", "N1b (單一臨床偵測淋巴結)",
             "N1c (無淋巴結轉移但有衛星或微衛星轉移)", "N2a (2-3個隱匿性轉移淋巴結)", "N2b (2-3個淋巴結中至少一個臨床偵測)",
             "N2c (一個臨床或隱匿性淋巴結且有衛星或微衛星轉移)", "N3a (≥4個隱匿性轉移淋巴結)",
             "N3b (≥4個淋巴結中至少一個臨床偵測)", "N3c (≥2個臨床或隱匿性淋巴結或有融合淋巴結或衛星轉移)"]
    m_ops = ["M0 (無遠處轉移)", "M1a(0) (皮膚、軟組織或非區域淋巴結轉移，LDH不升高)", "M1a(1) (皮膚、軟組織或非區域淋巴結轉移，LDH升高)",
             "M1b(0) (肺轉移，LDH不升高)", "M1b(1) (肺轉移，LDH升高)", "M1c(0) (非中樞內臟器官轉移，LDH不升高)",
             "M1c(1) (非中樞內臟器官轉移，LDH升高)", "M1d(0) (中樞神經系統轉移，LDH正常)", "M1d(1) (中樞神經系統轉移，LDH升高)"]

    t_in = st.selectbox("T分類", t_ops)
    n_in = st.selectbox("N分類", n_ops)
    m_in = st.selectbox("M分類", m_ops)

    if st.button("計算分期"):
        T_code = t_in.split(" ")[0]
        N_code = n_in.split(" ")[0]
        M_code = m_in.split(" ")[0]

        stage = "未分類"
        if T_code == "Tis" and N_code == "N0" and M_code == "M0": stage = "Stage 0"
        elif T_code == "T1a" and N_code == "N0" and M_code == "M0": stage = "Stage IA"
        elif T_code in ["T1b", "T2a"] and N_code == "N0" and M_code == "M0": stage = "Stage IB"
        elif T_code in ["T2b", "T3a"] and N_code == "N0" and M_code == "M0": stage = "Stage IIA"
        elif T_code in ["T3b", "T4a"] and N_code == "N0" and M_code == "M0": stage = "Stage IIB"
        elif T_code == "T4b" and N_code == "N0" and M_code == "M0": stage = "Stage IIC"
        elif N_code != "N0" and M_code == "M0": stage = "Stage III"
        elif M_code.startswith("M1"): stage = "Stage IV"

        st.success(f"AJCC 分期: {stage}")
        st.info(f"Code: {T_code} {N_code} {M_code}")

# --- 6. 陰道癌 ---
elif app_mode == "陰道癌 (Vaginal)":
    st.header("陰道癌分期 (Vaginal Cancer)")
    
    t_map = {
        "T1a": "腫瘤侷限於陰道，且最大直徑 ≤ 2.0 cm", "T1b": "腫瘤侷限於陰道，且最大直徑 > 2.0 cm",
        "T2a": "腫瘤穿透陰道壁，但未達骨盆壁，且最大直徑 ≤ 2.0 cm", "T2b": "腫瘤穿透陰道壁，但未達骨盆壁，且最大直徑 > 2.0 cm",
        "T3": "腫瘤已達骨盆壁或引起腎積水或腎功能異常", "T4": "腫瘤侵犯膀胱或直腸，或超出骨盆腔"
    }
    n_map = {
        "N0": "無區域淋巴結轉移", "N1": "有區域淋巴結轉移，骨盆或鼠蹊區"
    }
    m_map = {
        "M0": "無遠處轉移", "M1": "有遠處轉移，如肺、肝或骨骼"
    }

    T = st.selectbox("腫瘤大小與侵犯範圍 (T)", [f"{k} ({v})" for k, v in t_map.items()])
    N = st.selectbox("鄰近淋巴結轉移情形 (N)", [f"{k} ({v})" for k, v in n_map.items()])
    M = st.selectbox("遠處轉移情形 (M)", [f"{k} ({v})" for k, v in m_map.items()])

    if st.button("計算分期"):
        T_val = T.split()[0]
        N_val = N.split()[0]
        M_val = M.split()[0]
        
        res = "資料不足或不符合分期標準"
        if M_val == "M1": res = "FIGO Stage IVB"
        elif T_val == "T4" and M_val == "M0": res = "FIGO Stage IVA"
        elif ((T_val in ["T1a", "T1b", "T2a", "T2b", "T3"] and N_val == "N1" and M_val == "M0") or
              (T_val == "T3" and N_val == "N0" and M_val == "M0")):
            res = "FIGO Stage III"
        elif T_val in ["T2a", "T2b"] and N_val == "N0" and M_val == "M0":
            res = "FIGO Stage II"
        elif T_val in ["T1a", "T1b"] and N_val == "N0" and M_val == "M0":
            res = "FIGO Stage I"
        
        st.success(res)
        st.info(f"AJCC TNM: {T_val} {N_val} {M_val}")

# --- 7. GTN ---
elif app_mode == "妊娠滋養層細胞腫瘤 (GTN)":
    st.header("GTN 分期及風險評估")

    col1, col2 = st.columns(2)
    with col1:
        T = st.radio("T分類", ['T1 (腫瘤侷限於子宮)', 'T2 (腫瘤延伸至其他生殖器官)'])
        M = st.radio("M分類", ['M0 (無遠處轉移)', 'M1a (肺轉移)', 'M1b (其他遠處轉移)'])
        age = st.selectbox("年齡", ["0(無)", "1(≥40歲)"])
        ant_preg = st.selectbox("前次懷孕", ["0(葡萄胎)", "1(流產)", "2(足月妊娠)"])
        
    with col2:
        interval = st.selectbox("距前次妊娠時間", ["0(<4個月)", "1(4-6個月)", "2(7-12個月)", "4(>12個月)"])
        hcg = st.selectbox("治療前hCG數值(IU/mL)", ["0(<10^3)", "1(10^3-10^4)", "2(10^4-10^5)", "4(≥10^5)"])
        size = st.selectbox("腫瘤最大直徑", ["0(<3cm)", "1(3-5cm)", "2(>5cm)"])
        site = st.selectbox("轉移位置", ["0(無轉移或僅肺)", "1(脾臟/腎臟)", "2(腸胃道)", "4(腦/肝臟)"])
        number = st.selectbox("轉移病灶數量", ["0(無)", "1(1-4處)", "2(5-8處)", "4(>8處)"])
        chemo = st.selectbox("化療失敗次數", ["0(無)", "2(單一藥物)", "4(兩種以上藥物)"])

    if st.button("計算風險與分期"):
        stage = "Unknown"
        if M.startswith('M0'):
            if T.startswith('T1'): stage = "FIGO stage I"
            elif T.startswith('T2'): stage = "FIGO stage II"
        elif M.startswith('M1a'): stage = "FIGO stage III"
        elif M.startswith('M1b'): stage = "FIGO stage IV"

        items = [age, ant_preg, interval, hcg, size, site, number, chemo]
        score = sum([int(i.split('(')[0]) for i in items])
        category = "低風險" if score < 7 else "高風險"
        
        st.success(f"{stage}")
        st.warning(f"風險分數: {score} ({category})")

# --- 8. 外陰癌 ---
elif app_mode == "外陰癌 (Vulvar)":
    st.header("外陰癌分期 (Vulvar Cancer)")

    t_det = {
        'Tis': '原位癌', 'T1a': '病灶 ≤ 2公分，浸潤深度 ≤ 1.0毫米',
        'T1b': '病灶 > 2公分或浸潤深度 > 1.0毫米',
        'T2': '腫瘤延伸至鄰近會陰結構 (下1/3尿道、下1/3陰道或肛門)',
        'T3': '腫瘤侵犯上2/3尿道、上2/3陰道、膀胱黏膜、直腸黏膜或固定於骨盆骨'
    }
    n_det = {
        'N0': '無區域淋巴結轉移', 'N1a': '1或2個淋巴結轉移，各<5毫米',
        'N1b': '1個淋巴結轉移 ≥5毫米', 'N2a': '3個或以上淋巴結轉移，各<5毫米',
        'N2b': '2個或以上淋巴結轉移 ≥5毫米', 'N2c': '淋巴結轉移伴隨外囊侵犯',
        'N3': '固定或潰瘍性淋巴結轉移'
    }
    m_det = {'M0': '無遠處轉移', 'M1': '有遠處轉移(包含骨盆淋巴結轉移)'}

    t_sel = st.selectbox("T分期", [f"{k}: {v}" for k, v in t_det.items()])
    n_sel = st.selectbox("N分期", [f"{k}: {v}" for k, v in n_det.items()])
    m_sel = st.selectbox("M分期", [f"{k}: {v}" for k, v in m_det.items()])

    if st.button("計算分期"):
        T = t_sel.split(':')[0]
        N = n_sel.split(':')[0]
        M = m_sel.split(':')[0]
        
        figo_staging = {
            ('Tis', 'N0', 'M0'): 'Stage 0', ('T1a', 'N0', 'M0'): 'Stage IA',
            ('T1b', 'N0', 'M0'): 'Stage IB', ('T2', 'N0', 'M0'): 'Stage II',
            ('T1a', 'N1a', 'M0'): 'Stage IIIA', ('T1b', 'N1a', 'M0'): 'Stage IIIA',
            ('T2', 'N1a', 'M0'): 'Stage IIIA', ('T1a', 'N1b', 'M0'): 'Stage IIIA',
            ('T1b', 'N1b', 'M0'): 'Stage IIIA', ('T2', 'N1b', 'M0'): 'Stage IIIA',
            ('T1a', 'N2a', 'M0'): 'Stage IIIB', ('T1b', 'N2a', 'M0'): 'Stage IIIB',
            ('T2', 'N2a', 'M0'): 'Stage IIIB', ('T1a', 'N2b', 'M0'): 'Stage IIIB',
            ('T1b', 'N2b', 'M0'): 'Stage IIIB', ('T2', 'N2b', 'M0'): 'Stage IIIB',
            ('T1a', 'N2c', 'M0'): 'Stage IIIC', ('T1b', 'N2c', 'M0'): 'Stage IIIC',
            ('T2', 'N2c', 'M0'): 'Stage IIIC', ('T1a', 'N3', 'M0'): 'Stage IVA',
            ('T1b', 'N3', 'M0'): 'Stage IVA', ('T2', 'N3', 'M0'): 'Stage IVA',
            ('T3', 'any', 'M0'): 'Stage IVA', ('any', 'any', 'M1'): 'Stage IVB'
        }

        figo_result = '未知分期'
        for special_key in figo_staging.keys():
            T_match = (special_key[0] == T or special_key[0] == 'any')
            N_match = (special_key[1] == N or special_key[1] == 'any')
            M_match = (special_key[2] == M or special_key[2] == 'any')
            if T_match and N_match and M_match:
                figo_result = figo_staging[special_key]
                break
        
        st.success(f"FIGO分期: {figo_result}")
        st.info(f"AJCC TNM: {T}{N}{M}")

# --- 9. AI 智慧判讀 (REST API Mode) ---
elif app_mode == "🤖 AI 智慧判讀 (Beta)":
    st.header("🤖 AI 智慧病理報告判讀 (Direct API Mode)")
    st.warning("⚠️ 注意：此功能僅供輔助，請勿上傳包含真實病患姓名、身分證號等隱私個資的圖片。")

    if not api_key:
        st.error("請先在側邊欄輸入 Google Gemini API Key 才能使用此功能。")
    else:
        # 檔案上傳
        uploaded_files = st.file_uploader(
            "請上傳病理報告 (支援圖片 JPG/PNG)", 
            accept_multiple_files=True, 
            type=['png', 'jpg', 'jpeg']
        )
        
        cancer_context = st.selectbox("癌症類型上下文", 
            ["子宮內膜癌", "卵巢癌", "子宮頸癌", "子宮惡性肉瘤", "外陰癌", "陰道癌", "GTN", "自動判斷"])

        analyze_btn = st.button("開始 AI 分析")

        if analyze_btn and uploaded_files:
            with st.spinner('AI 正在仔細閱讀病理報告並進行分期運算...'):
                try:
                    # 1. 準備 Prompt
                    prompt_text = f"""
                    你是一位專業的婦科腫瘤科醫師。目前的癌症類型上下文為：{cancer_context}。
                    請分析圖片中的病理報告，執行以下任務：
                    1. 摘要關鍵發現：提取腫瘤大小(Tumor size)、侵犯深度(Invasion depth)、淋巴結狀態(Lymph node status)、遠端轉移(Metastasis)、組織學型態(Histology)等關鍵資訊。
                    2. 判定分期：根據 FIGO (最新版) 與 AJCC TNM 系統進行分期判定。請詳細解釋判定的理由。
                    3. 表格整理：請以 Markdown 表格列出 T, N, M 的判定結果。
                    如果報告資訊不足以判定完整分期，請指出缺少哪些關鍵資訊。
                    請用繁體中文回答。
                    """

                    # 2. 構建 Request Body (多模態輸入)
                    contents_parts = [{"text": prompt_text}]
                    
                    for uploaded_file in uploaded_files:
                        # 將圖片轉為 base64
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

                    # 3. 直接呼叫 API (更新為 gemini-2.5-flash)
                    # 您的 API Key 權限非常高，可以使用最新的 2.5 版！
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    
                    response = requests.post(url, headers=headers, data=json.dumps(payload))
                    
                    # 4. 處理回應
                    if response.status_code == 200:
                        result = response.json()
                        try:
                            # 解析 Gemini 的 JSON 結構
                            answer = result['candidates'][0]['content']['parts'][0]['text']
                            st.markdown("### 📋 AI 分析結果 (Model: Gemini 2.5 Flash)")
                            st.markdown(answer)
                        except KeyError:
                            st.error("無法解析 AI 回傳的資料，可能內容被阻擋或格式錯誤。")
                            st.json(result)
                    else:
                        st.error(f"API 呼叫失敗 (Status Code: {response.status_code})")
                        st.text("錯誤訊息如下：")
                        st.json(response.json())
                        st.info("💡 建議：請確認 API Key 是否正確。")

                except Exception as e:
                    st.error(f"發生錯誤：{str(e)}")
