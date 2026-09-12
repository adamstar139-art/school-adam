import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import io

### ---------------------------------------------------------
### 1. إعدادات الصفحة وحماية الكود وشريط الأدوات بكلمة المرور (adam0000)
### ---------------------------------------------------------
st.set_page_config(
    page_title="نظام تحضير متوسطة الثغر النموذجية",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تهيئة حالة قفل أدوات التطوير والشريط العلوي
if 'dev_unlocked' not in st.session_state:
    st.session_state['dev_unlocked'] = False

# إخفاء شريط الأدوات وأيقونات التعديل كلياً بالـ CSS ما لم يتم إدخال كلمة المرور adam0000
if not st.session_state['dev_unlocked']:
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        div[data-testid="stToolbar"] {visibility: hidden;}
        div[data-testid="stHeader"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

# 📱 اختيار وضع العرض والتجاوب من الشريط الجانبي
st.sidebar.title("⚙️ وضع الشاشة والتصفح")
display_mode = st.sidebar.radio(
    "اختر طريقة العرض المناسبة لجهازك:", 
    ["⚡ تلقائي (متجاوب مع الشاشة)", "📱 وضع الجوال (Mobile)", "💻 وضع الكمبيوتر (Desktop)"]
)

is_mobile = (display_mode == "📱 وضع الجوال (Mobile)")

# قفل التعديل بكلمة المرور adam0000 في الشريط الجانبي
with st.sidebar.expander("🔐 فك قفل أدوات التعديل والكود"):
    pwd_dev = st.text_input("أدخل كلمة المرور (adam0000):", type="password", key="pwd_dev_input")
    if st.button("فك القفل"):
        if pwd_dev == "adam0000":
            st.session_state['dev_unlocked'] = True
            st.success("تم فك قفل الأدوات بنجاح!")
            st.rerun()
        else:
            st.error("كلمة المرور غير صحيحة!")

# CSS التجاوب والتصميم العالي التنسيق
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {{
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }}
    
    /* تصميم الترويسة الرئيسية */
    .header-box {{
        background: linear-gradient(135deg, #0F2552 0%, #1E3A8A 100%);
        color: white;
        padding: {'12px 15px' if is_mobile else '20px 30px'};
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(15, 37, 82, 0.2);
        margin-bottom: 20px;
        display: flex;
        flex-direction: {'column-reverse' if is_mobile else 'row'};
        align-items: center;
        justify-content: space-between;
        text-align: {'center' if is_mobile else 'right'};
        border-bottom: 4px solid #D97706;
        gap: 12px;
    }}
    .header-text {{
        text-align: {'center' if is_mobile else 'right'};
    }}
    .header-title {{
        font-size: {'19px' if is_mobile else '26px'};
        font-weight: 800;
        margin: 0;
        color: #FFFFFF;
    }}
    .header-subtitle {{
        font-size: {'12px' if is_mobile else '16px'};
        color: #E2E8F0;
        margin-top: 5px;
        font-weight: 600;
    }}
    
    /* بطاقات الطلاب والمعلمين */
    .student-card {{
        text-align: right;
        direction: rtl;
        padding: 4px 0;
    }}
    .student-name {{
        font-size: {'14px' if is_mobile else '15px'};
        font-weight: 700;
        color: #1E293B;
    }}
    .student-id {{
        font-size: {'11px' if is_mobile else '12px'};
        color: #64748B;
        font-weight: 600;
        display: block;
        margin-top: 2px;
    }}

    /* الهيكل الإداري وتوقيع المصمم في القائمة الجانبية */
    .sidebar-admin-box {{
        background-color: #F8FAFC;
        border-right: 4px solid #0F2552;
        border-radius: 10px;
        padding: 12px;
        margin-top: 15px;
        text-align: right;
        direction: rtl;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }}
    .sidebar-admin-title {{
        color: #0F2552;
        font-weight: 800;
        font-size: 14px;
        margin-bottom: 6px;
    }}
    .sidebar-admin-item {{
        font-size: 12px;
        color: #334155;
        margin: 4px 0;
    }}
    .designer-badge {{
        margin-top: 12px;
        padding: 8px 10px;
        background: linear-gradient(135deg, #0F2552 0%, #1E3A8A 100%);
        color: #F59E0B;
        font-size: 14px;
        font-weight: 800;
        text-align: center;
        border-radius: 8px;
        border: 1px solid #D97706;
        box-shadow: 0 3px 8px rgba(15, 37, 82, 0.25);
    }}

    @media (max-width: 768px) {{
        .header-box {{
            flex-direction: column-reverse !important;
            text-align: center !important;
            padding: 12px !important;
        }}
        .header-title {{ font-size: 19px !important; }}
        .header-subtitle {{ font-size: 12px !important; }}
        .stButton>button {{ width: 100% !important; }}
    }}
</style>
""", unsafe_allow_html=True)

### ---------------------------------------------------------
### 2. الترويسة والشعار المعتمد لمدارس الثغر
### ---------------------------------------------------------
header_html = """
<div class="header-box">
    <div class="header-text">
        <div class="header-title">متوسطة الثغر النموذجية الأهلية - بنين</div>
        <div class="header-subtitle">نظام رصد ومتابعة الحضور والغياب اليومي (1447 - 1448هـ)</div>
    </div>
    <div>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 220" width="140" height="60">
            <path d="M250 20 L400 100 L250 180 L100 100 Z" fill="#D97706" />
            <text x="250" y="115" font-family="'Cairo', sans-serif" font-size="32" font-weight="bold" fill="#FFFFFF" text-anchor="middle">الثغر</text>
        </svg>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

### ---------------------------------------------------------
### 3. دوال التحويل بين الهجري والميلادي
### ---------------------------------------------------------
def gregorian_to_hijri_approx(g_date):
    try:
        total_days = (g_date - date(2024, 1, 1)).days
        h_year = 1445 + int(total_days / 354.36)
        h_month = 1 + int((total_days % 354.36) / 29.5)
        if h_month > 12:
            h_month = 12
        h_day = 1 + int((total_days % 29.5))
        if h_day > 30:
            h_day = 30
            
        return f"{h_year}/{h_month:02d}/{h_day:02d} هـ"
    except:
        return f"{g_date.strftime('%Y/%m/%d')} هـ"

### ---------------------------------------------------------
### 4. قوائم المعلمين والطلاب والحصص
### ---------------------------------------------------------
TEACHERS_LIST = [
    "محمد سامي السعيد", "علي محمد معوض", "أحمد عبد الحميد سعيد", "محمد عبد المنعم أبو كيلة",
    "هيثم رضا عطية", "عماد الدين نصر كرم", "السيد الغريب بدوي", "محمد إبراهيم عبد الرحمن",
    "أسامة أحمد سالم", "عماد بكر عارف", "إبراهيم علي العتيبي", "عيسى خالد العويس", "زيد بن علي التميمي"
]

PERIODS_LIST = [f"الحصة {i}" for i in range(1, 8)]

STUDENTS_DB = {
    "الأول المتوسط": {
        "أول أول (فصل 1)": [
            {"id": "2395664317", "name": "بلال عبدالرزاق عيسى العيسى"},
            {"id": "1170970741", "name": "جاسر بن عبدالله بن منصور العطار الحارثي"},
            {"id": "1170582165", "name": "حسام بن محمد بن علي ال رايان البارقي"},
            {"id": "1169004353", "name": "ريان عبدالله جابر الأسمري"},
            {"id": "2446713998", "name": "زيد زياد عبد اللطيف أبو قبع"},
            {"id": "2527104554", "name": "سامي سعد عباس حمد"},
            {"id": "1170111759", "name": "سعد ناصر سعد السيف"},
            {"id": "1153310501", "name": "عبدالله بن سليمان بن عبدالله الراجحي"},
            {"id": "1170836520", "name": "عبدالله سعد بن محمد العيشان"},
            {"id": "1171448515", "name": "علي احمد علي كريري"},
            {"id": "1170853053", "name": "علي سعد علي القحطاني"},
            {"id": "1172018036", "name": "عمر عبدالله سعد الجبرين"},
            {"id": "2552851368", "name": "مازن اسلام احمد ابراهيم موسى"},
            {"id": "013609321", "name": "محمد أحمد علي عقيل"},
            {"id": "2502333707", "name": "محمد اسلام محمد دراز"},
            {"id": "2394606749", "name": "محمد اشرف مسعود ابواخاطر"},
            {"id": "1169174164", "name": "محمد نايف فراج الدعجاني"},
            {"id": "2380890976", "name": "وائل -- بولعيش"}
        ],
        "أول ثاني (فصل 2)": [
            {"id": "1167628468", "name": "ابراهيم بن محمد بن علي الوهيبي"},
            {"id": "1170348286", "name": "الوليد ابن خالد بن فهد العتيبي"},
            {"id": "1172433185", "name": "باسل محمد فرج الدوسري"},
            {"id": "1173391556", "name": "بسام بن عبدالكريم بن عبدالله الحرقان الدوسري"},
            {"id": "1169185053", "name": "تركي عبدالله مسفر الدوسري"},
            {"id": "1170108078", "name": "تميم فهد عبدالعزيز العزاز"},
            {"id": "1168982427", "name": "راكان عبدالله يحي كريري"},
            {"id": "1172590968", "name": "ريان عبدالله منصور السبر"},
            {"id": "2392863888", "name": "ريان وليد - حلاق"},
            {"id": "1170420473", "name": "سيف عبدالكريم بريك العصيمي"},
            {"id": "1168942108", "name": "صالح حسن فتحى سندى"},
            {"id": "1173182138", "name": "عبدالرحمن ابراهيم عبدالله الحضيف"},
            {"id": "1172448548", "name": "عبدالله صالح حمد الصفيان"},
            {"id": "1170000945", "name": "فهد ابن احمد بن فهد العثمان"},
            {"id": "1167092616", "name": "فهد عويض ثعيل المطيري"},
            {"id": "1170413171", "name": "فهد نايف فهد الحسينان"},
            {"id": "1170294118", "name": "فيصل موينع عبدالله بن موينع"},
            {"id": "1171524604", "name": "فيصل ناصر سيف العريفي"},
            {"id": "1170374993", "name": "مشاري عثمان سعد ناصر السعد"},
            {"id": "1170884165", "name": "يزن محمد علي اليحيى"},
            {"id": "1170548737", "name": "يوسف محمد عبدالله الدوسري"}
        ]
    },
    "الثاني المتوسط": {
        "ثاني أول (فصل 1)": [
            {"id": "1163613795", "name": "ابراهيم ياسر ابراهيم الحلوى"},
            {"id": "1163760935", "name": "احمد سامي بن احمد العمران"},
            {"id": "1153756612", "name": "الوليد عبدالله بن ابراهيم المبدل"},
            {"id": "1164269209", "name": "ذياب بن محمد بن ذياب بن مريطع القحطاني"},
            {"id": "1163187972", "name": "راكان سالم بن مسفر القحطاني"},
            {"id": "1167623758", "name": "سلطان عبدالله حسن القحطاني"},
            {"id": "1164769430", "name": "عبدالرحمن حمد بن محمد العريفي"},
            {"id": "1167893740", "name": "عبدالرحمن ربيع جابر خبراني"},
            {"id": "1159740032", "name": "عبدالعزيز سعود بن فهد العتيبي"},
            {"id": "1164277830", "name": "عبداللطيف ابراهيم محمد الطمره"},
            {"id": "1162761306", "name": "فهد عيسى محمد العيسى"},
            {"id": "1160901128", "name": "فيصل بن عبدالله بن سعود بن عبدالعزيز الجمعه"},
            {"id": "1162168627", "name": "مبارك صالح مبارك هليل"},
            {"id": "1163212978", "name": "محمد بن عبدالله بن حمد بن ناصر بن عمران"},
            {"id": "1161858301", "name": "محمد عبدالمحسن ناصر الحزام"},
            {"id": "1175902442", "name": "محمد فايز عبدالرحمن بن يوسف"},
            {"id": "1165686179", "name": "مشاري سلطان سالم الشمراني"},
            {"id": "1166040053", "name": "معاذ عبدالله سعود العريفي"},
            {"id": "1167081981", "name": "ناصر حسين محمد ال جبران"},
            {"id": "1163191222", "name": "يزيد بن طارق بن علي الحديثي"}
        ],
        "ثاني ثاني (فصل 2)": [
            {"id": "1166753291", "name": "ابراهيم بن مبارك بن راشد بن عبدالرحمن السبعان آل موينع"},
            {"id": "1167148251", "name": "حامد بن محمد بن حامد شباط"},
            {"id": "1164599977", "name": "حسام حسن محمد الشهري"},
            {"id": "1169057351", "name": "خالد تركي عايض القحطاني"},
            {"id": "1164120600", "name": "خالد داود بن عابد الحارثي"},
            {"id": "1165839455", "name": "سطام عبدالعزيز عبدالله العريفي"},
            {"id": "1171617069", "name": "سعود خالد عبدالله الحمد"},
            {"id": "1163778960", "name": "سعود سلطان بن خليل العتيبي"},
            {"id": "1163458878", "name": "سعود مشعل بن ابراهيم الشثري"},
            {"id": "1166582989", "name": "طلال محمد منير المهدرس"},
            {"id": "1165143783", "name": "عبدالكريم مساعد عبدالعزيز الهزاع"},
            {"id": "1165495258", "name": "عبدالله سامي سعد الحوشاني"},
            {"id": "013609088", "name": "علي أحمد علي عقيل"},
            {"id": "1164825802", "name": "عمر بن سعد بن هلال الشبانات"},
            {"id": "3787591993", "name": "عمر خالد عبدالله المهيني"},
            {"id": "1163537838", "name": "فارس مشعل عبدالله بن موينع"},
            {"id": "1164997858", "name": "مازن خالد دخيل المطيري"},
            {"id": "2348937422", "name": "مازن رفعت محمد حاج النيل"},
            {"id": "1166803245", "name": "نايف بن بندر بن خلفان العلوي"},
            {"id": "1165668417", "name": "نواف عبدالعزيز مرزوق المرزوق"},
            {"id": "1164387977", "name": "هادي سلطان هادي القحطاني"},
            {"id": "1165002153", "name": "يزيد بن حسين بن متعب بن محمد كعكم"}
        ],
        "ثاني ثالث (فصل 3)": [
            {"id": "1166911709", "name": "ثامر عمر ابراهيم عثمان"},
            {"id": "008464815", "name": "جهاد فارس عبدالقادر حتاوي"},
            {"id": "1164830562", "name": "خالد محمد عبدالكريم الخفاجي"},
            {"id": "1188914319", "name": "سعد ابن مسفر بن سعد القحطاني"},
            {"id": "1165099498", "name": "سعود بن عبدالله بن سعود السحامي"},
            {"id": "1167770468", "name": "سعود ناصر سنيف العريفي"},
            {"id": "2344500760", "name": "سعيد محمد - باوزير"},
            {"id": "1164983874", "name": "طلال بن فهد بن عطيه بالحكم الزهراني"},
            {"id": "2362260263", "name": "عبدالرحمن احمد جاسم الحمدي"},
            {"id": "1167153434", "name": "عبدالعزيز ماجد راشد الزير"},
            {"id": "1164512566", "name": "عبدالعزيز وليد ناصر بن سعران"},
            {"id": "1167267341", "name": "عبدالله بن بندر بن فهد المفيجل"},
            {"id": "1164747436", "name": "عبدالمجيد بن محمد بن مسعود آل عايض القحطاني"},
            {"id": "2358022958", "name": "عز الدين احمد محمد سعد"},
            {"id": "1167515020", "name": "عزام خالد شلهوب بن شلهوب"},
            {"id": "1164747014", "name": "عزام فهد احمد صلوي"},
            {"id": "4533080448", "name": "عمر وليد ياسين درويش علي"},
            {"id": "1163397811", "name": "فارس ابن محمد بن سالم بن نويشي الوهبي الحربي"},
            {"id": "1172720045", "name": "محمد بن علي محسن العثيميني"},
            {"id": "1171868639", "name": "وائل بن عبدالله بن عامر علي ال عبيد الغامدي"},
            {"id": "1166629798", "name": "يزيد بن حمد بن مترك بن محمد ال مسعود القحطاني"},
            {"id": "1167371093", "name": "يوسف عايد عواد البلوي"}
        ]
    },
    "الثالث المتوسط": {
        "ثالث أول (فصل 1)": [
            {"id": "1158966166", "name": "أصيل ناصر بن محمد مذكور"},
            {"id": "1162308223", "name": "خالد محمد مسدف معافا"},
            {"id": "1159155223", "name": "راشد سعيد راشد عبدالسلام"},
            {"id": "1161109093", "name": "راكان بن عبدالله بن سالم اليافعي"},
            {"id": "1160805899", "name": "زياد احمد بن علي اللحيد"},
            {"id": "1160267124", "name": "سطام محمد سعود الدوسري"},
            {"id": "1163270869", "name": "سلطان احمد صالح الفتوح"},
            {"id": "1160585624", "name": "عبدالعزيز عبدالله شراز المالكي"},
            {"id": "1160050678", "name": "عبدالعزيز عبدالله عايض الأسمري"},
            {"id": "1161021314", "name": "عبدالله عبيد عبدالله العتيبي"},
            {"id": "1160857700", "name": "عبدالله فهد جلوي سالم الشرعي"},
            {"id": "1161503857", "name": "علي ابراهيم علي الأسمري"},
            {"id": "2502333723", "name": "عماد الدين اسلام محمد دراز"},
            {"id": "1162454266", "name": "عمر فهد محمد السقامي"},
            {"id": "1161418593", "name": "فهد عبدالرحمن فهد العتيبي"},
            {"id": "1163074592", "name": "فيصل بن عبدالمحسن بن عايض العصيمي العتيبي"},
            {"id": "1165152107", "name": "فيصل محمد صالح الفتوح"},
            {"id": "1158815876", "name": "محمد سلطان عبدالعزيز العيد"},
            {"id": "1166075653", "name": "محمد مقعد ساير العتيبي"},
            {"id": "1160693949", "name": "مشاري ابراهيم عبداللطيف المغربي"},
            {"id": "1160803878", "name": "مشاري علي موسى عقيلي"},
            {"id": "1161661846", "name": "مهند عبدالله فهد الزكري"},
            {"id": "1159404795", "name": "نواف وليد حمد الشعلان"},
            {"id": "1168385894", "name": "يوسف نايف مقعد العتيبي"}
        ],
        "ثالث ثاني (فصل 2)": [
            {"id": "1156933093", "name": "تركي عبدالعزيز عبدالله المرزوق"},
            {"id": "1160223317", "name": "تركي عثمان عبدالعزيز العثمان"},
            {"id": "1159683497", "name": "راشد احمد فهد ال سعيد"},
            {"id": "2310646332", "name": "راكان ابراهيم محمد دبوان"},
            {"id": "1161397599", "name": "ريان ناصر عبدالرحمن المرشود"},
            {"id": "1163112129", "name": "صالح بن ممدوح بن صالح بن خالد الجويعي"},
            {"id": "2508581135", "name": "عبد الرحمن محمد صلاح بدر الدين"},
            {"id": "1162188872", "name": "عبدالعزيز تركي عبدالعزيز اللهيم"},
            {"id": "1161340763", "name": "عبدالعزيز عبدالمحسن فهد بن بديع"},
            {"id": "1171845140", "name": "عبدالله متعب بن عبدالرحمن الجبرين"},
            {"id": "1159200318", "name": "عبدالمحسن طارق بن عبدالرحمن العروان"},
            {"id": "1161333677", "name": "فارس وليد بن عبدالله الحوطي"},
            {"id": "1162461857", "name": "محمد خالد محمد بن مشرف"},
            {"id": "1161288897", "name": "محمد سعد بن محمد العيشان"},
            {"id": "1156334813", "name": "محمد عبدالعزيز محمد الخالدي"},
            {"id": "1162044851", "name": "مهند ماجد علي كعبي"},
            {"id": "1158021137", "name": "ناصر محمد عبدالله الزريعي"},
            {"id": "1161363443", "name": "نواف سعد بن علي القاسم"},
            {"id": "1162274086", "name": "ياسر تركي اسماعيل مسلمي"}
        ],
        "ثالث ثالث (فصل 3)": [
            {"id": "1163525544", "name": "ثامر وليد بن عبدالعزيز الطليحي"},
            {"id": "1160712996", "name": "خالد بن عبدالرؤوف بن عبدالرحمن بن عبدالله الشنير"},
            {"id": "1162560054", "name": "خالد عبدالله خالد الخالدي"},
            {"id": "1174188647", "name": "خالد محمد بن عبدالله ال درعان"},
            {"id": "1174226389", "name": "راشد صالح بن عبدالعزيز الحلوان"},
            {"id": "1167756897", "name": "رواد محمد إبراهيم الخليل"},
            {"id": "1159394046", "name": "صالح بن محمد بن صالح الميموني المطيري"},
            {"id": "1161085236", "name": "ضاري صالح مهنا العازمي"},
            {"id": "1158551372", "name": "عبدالرحمن بدر عبدالرحمن الطريقي"},
            {"id": "1195815558", "name": "عبدالرحمن خالد محمد سعيد"},
            {"id": "1158561843", "name": "عبدالله تركي عبدالله الأحمد"},
            {"id": "1159977451", "name": "عبدالله عبدالرحمن عبدالله النجراني"},
            {"id": "1162387458", "name": "علي بن خالد بن علي العجيري"},
            {"id": "1158128270", "name": "علي عبدالله علي ال حمود"},
            {"id": "1158198604", "name": "فهد بن خالد بن فهد بن عبدالعزيز الزيد"},
            {"id": "1159551264", "name": "فيصل عبدالرحمن عزيز القحطاني"},
            {"id": "1162325722", "name": "ماجد فهد عبدالعزيز الكثيري"},
            {"id": "1171918236", "name": "مازن خالد عبدربه الزهراني"},
            {"id": "1186515613", "name": "متعب مطر جمعان الدوسري"},
            {"id": "1159852746", "name": "نواف فهد بن ناصر القحطاني"},
            {"id": "1163027392", "name": "يوسف عبدالله عوض العتيبي"}
        ]
    }
}

### ---------------------------------------------------------
### 5. دوال توليد صفحات HTML للطباعة (للطلاب وللمعلمين)
### ---------------------------------------------------------
def generate_printable_html(df_subset, report_title):
    rows_html = ""
    for idx, row in enumerate(df_subset.to_dict('records'), 1):
        status_color = "#DC2626" if row['الحالة'] == "غائب" else "#D97706" if row['الحالة'] in ["خارج الفصل", "خالد الفصل"] else "#CA8A04" if row['الحالة'] == "متأخر" else "#16A34A"
        teacher = row.get('اسم المعلم', 'غير محدد')
        rows_html += f"""
        <tr>
            <td>{idx}</td>
            <td style="text-align: right;"><b>{row['اسم الطالب']}</b><br><small style="color: #64748B;">الهوية: {row['رقم الطالب']}</small></td>
            <td>{row['الصف']}</td>
            <td>{row['الفصل']}</td>
            <td>{row['الحصة']}</td>
            <td>{teacher}</td>
            <td style="color: {status_color}; font-weight: bold;">{row['الحالة']}</td>
        </tr>
        """
        
    html_code = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
    <meta charset="utf-8">
    <title>{report_title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
        body {{ font-family: 'Cairo', sans-serif; text-align: right; padding: 20px; background-color: #FFFFFF; color: #1E293B; }}
        .header {{ text-align: center; border-bottom: 3px solid #0F2552; padding-bottom: 12px; margin-bottom: 20px; }}
        h2 {{ color: #0F2552; margin: 5px; font-weight: 800; font-size: 22px; }}
        h4 {{ color: #4B5563; margin: 5px; font-weight: 700; font-size: 16px; }}
        .info {{ background-color: #F1F5F9; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: 700; border: 1px solid #CBD5E1; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #CBD5E1; padding: 10px; text-align: center; font-size: 13px; }}
        th {{ background-color: #0F2552; color: white; font-weight: 700; }}
        tr:nth-child(even) {{ background-color: #F8FAFC; }}
        .footer-credits {{ margin-top: 40px; border-top: 2px solid #E2E8F0; padding-top: 20px; text-align: center; }}
        .designer-title-print {{
            margin-top: 15px;
            padding: 10px 20px;
            background-color: #0F2552;
            color: #F59E0B;
            font-size: 16px;
            font-weight: 800;
            border-radius: 8px;
            display: inline-block;
            border: 1px solid #D97706;
        }}
        @media print {{
            .no-print {{ display: none; }}
        }}
    </style>
    </head>
    <body>
    <div class="no-print" style="text-align: center; margin-bottom: 20px;">
        <button onclick="window.print()" style="background-color: #0F2552; color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer;">
            🖨️ طباعة التقرير / حفظ كـ PDF
        </button>
    </div>
    <div class="header">
        <h2>متوسطة الثغر النموذجية الأهلية - بنين</h2>
        <h4>{report_title}</h4>
    </div>
    <div class="info">
        التاريخ: {date.today()} | إجمالي السجلات: {len(df_subset)} طالب
    </div>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>اسم الطالب ورقم الهوية</th>
                <th>الصف</th>
                <th>الفصل</th>
                <th>الحصة</th>
                <th>اسم المعلم</th>
                <th>الحالة</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="footer-credits">
        <table style="border: none; width: 100%;">
            <tr style="background: none;">
                <td style="border: none; font-weight: bold;">مدير المدرسة: إبراهيم بن موسى التميمي</td>
                <td style="border: none; font-weight: bold;">وكيل الشؤون التعليمية: محمد مبروك السيد</td>
                <td style="border: none; font-weight: bold;">وكيل شؤون الطلاب: صالح بن عبدالله الدعجاني</td>
            </tr>
        </table>
        <div class="designer-title-print">
            ✨ تصميم الأستاذ: محمد سامي السعيد ✨
        </div>
    </div>
    </body>
    </html>
    """
    return html_code

def generate_teacher_range_report_html(teacher_summary_list, start_d, end_d, cal_system):
    rows_html = ""
    for idx, rec in enumerate(teacher_summary_list, 1):
        absent_cnt = rec.get('عدد مرات الغياب', 0)
        late_cnt = rec.get('عدد مرات التأخر', 0)
        present_cnt = rec.get('عدد أيام الحضور', 0)
        
        absent_style = f"color: #DC2626; font-weight: bold;" if absent_cnt > 0 else "color: #16A34A;"
        late_style = f"color: #CA8A04; font-weight: bold;" if late_cnt > 0 else "color: #16A34A;"
        
        rows_html += f"""
        <tr>
            <td>{idx}</td>
            <td style="text-align: right; font-weight: bold;">{rec['اسم المعلم']}</td>
            <td style="color: #16A34A; font-weight: bold;">{present_cnt} يوم</td>
            <td style="{absent_style}">{absent_cnt} مرة</td>
            <td style="{late_style}">{late_cnt} مرة</td>
            <td>{rec.get('إجمالي الحصص المرصودة', 0)} حصة</td>
        </tr>
        """

    start_disp = gregorian_to_hijri_approx(start_d) if cal_system == "هجري" else str(start_d)
    end_disp = gregorian_to_hijri_approx(end_d) if cal_system == "هجري" else str(end_d)

    html_code = f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
    <meta charset="utf-8">
    <title>تقرير حضور وغياب المعلمين للفترة</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
        body {{ font-family: 'Cairo', sans-serif; text-align: right; padding: 20px; background-color: #FFFFFF; color: #1E293B; }}
        .header {{ text-align: center; border-bottom: 3px solid #0F2552; padding-bottom: 12px; margin-bottom: 20px; }}
        h2 {{ color: #0F2552; margin: 5px; font-weight: 800; font-size: 22px; }}
        h4 {{ color: #4B5563; margin: 5px; font-weight: 700; font-size: 16px; }}
        .info {{ background-color: #F1F5F9; padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: 700; border: 1px solid #CBD5E1; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #CBD5E1; padding: 10px; text-align: center; font-size: 14px; }}
        th {{ background-color: #0F2552; color: white; font-weight: 700; }}
        tr:nth-child(even) {{ background-color: #F8FAFC; }}
        .footer-credits {{ margin-top: 40px; border-top: 2px solid #E2E8F0; padding-top: 20px; text-align: center; }}
        .designer-title-print {{
            margin-top: 15px;
            padding: 10px 20px;
            background-color: #0F2552;
            color: #F59E0B;
            font-size: 16px;
            font-weight: 800;
            border-radius: 8px;
            display: inline-block;
            border: 1px solid #D97706;
        }}
        @media print {{
            .no-print {{ display: none; }}
        }}
    </style>
    </head>
    <body>
    <div class="no-print" style="text-align: center; margin-bottom: 20px;">
        <button onclick="window.print()" style="background-color: #0F2552; color: white; padding: 12px 30px; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer;">
            🖨️ طباعة التقرير / حفظ كـ PDF
        </button>
    </div>
    <div class="header">
        <h2>متوسطة الثغر النموذجية الأهلية - بنين</h2>
        <h4>تقرير ملخص إحصائيات المعلمين بالفترة ({cal_system})</h4>
    </div>
    <div class="info">
        الفترة من: {start_disp} إلى: {end_disp} | إجمالي عدد المعلمين: {len(teacher_summary_list)} معلم
    </div>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>اسم المعلم</th>
                <th>أيام الحضور</th>
                <th>عدد مرات الغياب</th>
                <th>عدد مرات التأخر</th>
                <th>إجمالي الحصص والمرصودات</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="footer-credits">
        <table style="border: none; width: 100%;">
            <tr style="background: none;">
                <td style="border: none; font-weight: bold;">مدير المدرسة: إبراهيم بن موسى التميمي</td>
                <td style="border: none; font-weight: bold;">وكيل الشؤون التعليمية: محمد مبروك السيد</td>
                <td style="border: none; font-weight: bold;">وكيل شؤون الطلاب: صالح بن عبدالله الدعجاني</td>
            </tr>
        </table>
        <div class="designer-title-print">
            ✨ تصميم الأستاذ: محمد سامي السعيد ✨
        </div>
    </div>
    </body>
    </html>
    """
    return html_code

### ---------------------------------------------------------
### 6. تهيئة ذاكرة البيانات (Students & Teachers Logs)
### ---------------------------------------------------------
if 'attendance_data' not in st.session_state:
    st.session_state['attendance_data'] = []

if 'teacher_daily_logs' not in st.session_state:
    st.session_state['teacher_daily_logs'] = [
        {
            "التاريخ": str(date.today()),
            "التاريخ_الهجري": gregorian_to_hijri_approx(date.today()),
            "اسم المعلم": t,
            "الحالة": "حاضر",
            "الحصص المرصودة": 0,
            "ملاحظات": "رصد اعتيادي"
        } for t in TEACHERS_LIST
    ]

if 'teacher_status_db' not in st.session_state:
    st.session_state['teacher_status_db'] = {t: "حاضر" for t in TEACHERS_LIST}

if 'search_teacher_started' not in st.session_state:
    st.session_state['search_teacher_started'] = False

### ---------------------------------------------------------
### 7. القائمة الجانبية
### ---------------------------------------------------------
st.sidebar.title("📌 نظام المتابعة")
role = st.sidebar.radio("اختر لوحة التحكم:", ["👨‍🏫 حساب المعلم (رصد الحضور)", "👔 حساب الوكيل والمدير (المتابعة والتصدير)"])

### ---------------------------------------------------------
### 8. واجهة المعلم (رصد حضور الطلاب)
### ---------------------------------------------------------
if role == "👨‍🏫 حساب المعلم (رصد الحضور)":
    st.subheader("📋 رصد حضور وغياب الطلاب")
    
    col_t, col_g, col_s, col_p, col_d = st.columns(5)
    with col_t:
        teacher_name = st.selectbox("اسم المعلم:", TEACHERS_LIST)
    with col_g:
        grade = st.selectbox("الصف الدراسي:", list(STUDENTS_DB.keys()))
    with col_s:
        section = st.selectbox("الفصل:", list(STUDENTS_DB[grade].keys()))
    with col_p:
        period = st.selectbox("الحصة:", PERIODS_LIST)
    with col_d:
        att_date = st.date_input("التاريخ:", date.today())

    students_list = STUDENTS_DB[grade][section]

    st.info(f"👨‍🏫 **المعلم:** {teacher_name} | 🏫 **الفصل:** {grade} - {section} | ⏰ **الحصة:** {period} | 📅 **التاريخ:** {att_date}")
    st.write("---")

    attendance_records = {}

    for idx, student in enumerate(students_list, 1):
        c_num, c_name, c_status = st.columns([0.5, 3.5, 3])
        c_num.write(f"**{idx}**")
        
        c_name.markdown(
            f"""
            <div class="student-card">
                <span class="student-name">{student['name']}</span>
                <span class="student-id">رقم الطالب/الهوية: {student['id']}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        status = c_status.radio(
            "حالة الحضور:",
            ["حاضر", "غائب", "خارج الفصل", "متأخر"],
            key=f"{teacher_name}_{grade}_{section}_{period}_{student['id']}",
            horizontal=True
        )
        attendance_records[student['id']] = {
            "name": student['name'],
            "status": status
        }

    st.write("---")
    if st.button("💾 حفظ وإرسال كشف الحضور", type="primary", use_container_width=True):
        for st_id, info in attendance_records.items():
            st.session_state['attendance_data'].append({
                "التاريخ": str(att_date),
                "اسم المعلم": teacher_name,
                "الصف": grade,
                "الفصل": section,
                "الحصة": period,
                "رقم الطالب": st_id,
                "اسم الطالب": info['name'],
                "الحالة": info['status']
            })
        st.success(f"تم حفظ حضور فصل ({section}) بنجاح بواسطة المعلم {teacher_name}!")

### ---------------------------------------------------------
### 9. واجهة الوكيل والمدير (الإحصائيات ورصد وحفظ وتعديل المعلمين)
### ---------------------------------------------------------
else:
    st.subheader("👔 لوحة الوكيل والمدير (المتابعة الإدارية والطباعة والتعديل)")
    
    if 'admin_authenticated' not in st.session_state:
        st.session_state['admin_authenticated'] = False
        
    if not st.session_state['admin_authenticated']:
        st.warning("🔒 هذه اللوحة مخصصة لإدارة المدرسة فقط. يرجى إدخال كلمة المرور للمتابعة:")
        pwd_input = st.text_input("كلمة المرور:", type="password")
        if st.button("تسجيل الدخول"):
            if pwd_input == "adam112233":
                st.session_state['admin_authenticated'] = True
                st.success("تم الدخول بنجاح!")
                st.rerun()
            else:
                st.error("كلمة المرور غير صحيحة! يرجى التأكد وإعادة المحاولة.")
    else:
        col_admin_top1, col_admin_top2 = st.columns(2)
        with col_admin_top2:
            if st.button("🚪 تسجيل الخروج", use_container_width=True):
                st.session_state['admin_authenticated'] = False
                st.rerun()

        st.write("---")
        
        df = pd.DataFrame(st.session_state['attendance_data'])
        
        # 🗑️ إدارة حذف تقارير الطلاب وتقارير المعلمين (3 خيارات: يومي / أسبوعي / شهري)
        col_del1, col_del2 = st.columns(2)
        
        with col_del1:
            with st.expander("🗑️ إدارة حذف تقارير حضور الطلاب"):
                st.warning("⚠️ اختر نطاق الحذف المطلوبة لكشوف الطلاب:")
                del_st_scope = st.radio(
                    "نطاق حذف الطلاب:",
                    ["📅 يومي (اليوم)", "🗓️ أسبوعي (آخر 7 أيام)", "📆 شهري / شامل السجل"],
                    key="del_st_scope"
                )
                conf_st_del = st.checkbox("أؤكد حذف سجلات الطلاب", key="conf_st_del")
                if st.button("🚨 حذف تقارير الطلاب", type="primary", key="btn_del_st"):
                    if conf_st_del:
                        today_str = str(date.today())
                        if "يومي" in del_st_scope:
                            st.session_state['attendance_data'] = [r for r in st.session_state['attendance_data'] if r.get('التاريخ') != today_str]
                        elif "أسبوعي" in del_st_scope:
                            seven_days_ago = date.today() - timedelta(days=7)
                            st.session_state['attendance_data'] = [
                                r for r in st.session_state['attendance_data'] 
                                if datetime.strptime(r.get('التاريخ'), "%Y-%m-%d").date() < seven_days_ago
                            ]
                        else:
                            st.session_state['attendance_data'] = []
                        st.success("🗑️ تم تنفيذ عملية الحذف لسجلات الطلاب بنجاح!")
                        st.rerun()
                    else:
                        st.error("يرجى التأشير على التأكيد أولاً.")

        with col_del2:
            with st.expander("🗑️ إدارة حذف تقارير حضور المعلمين"):
                st.warning("⚠️ اختر نطاق الحذف المطلوب لسجلات تقارير المعلمين:")
                del_tc_scope = st.radio(
                    "نطاق حذف المعلمين:",
                    ["📅 يومي (اليوم)", "🗓️ أسبوعي (آخر 7 أيام)", "📆 شهري / شامل السجل"],
                    key="del_tc_scope"
                )
                conf_tc_del = st.checkbox("أؤكد حذف سجلات المعلمين", key="conf_tc_del")
                if st.button("🚨 حذف تقارير المعلمين", type="primary", key="btn_del_tc"):
                    if conf_tc_del:
                        today_str = str(date.today())
                        if "يومي" in del_tc_scope:
                            st.session_state['teacher_daily_logs'] = [r for r in st.session_state['teacher_daily_logs'] if r.get('التاريخ') != today_str]
                        elif "أسبوعي" in del_tc_scope:
                            seven_days_ago = date.today() - timedelta(days=7)
                            st.session_state['teacher_daily_logs'] = [
                                r for r in st.session_state['teacher_daily_logs'] 
                                if datetime.strptime(r.get('التاريخ'), "%Y-%m-%d").date() < seven_days_ago
                            ]
                        else:
                            st.session_state['teacher_daily_logs'] = []
                        st.success("🗑️ تم تنفيذ عملية الحذف لسجلات المعلمين بنجاح!")
                        st.rerun()
                    else:
                        st.error("يرجى التأشير على التأكيد أولاً.")

        st.write("---")
        
        # 🎯 القوائم المنسدلة الموحدة لصفحة المدير (الصف، الفصل، الحصة)
        st.markdown("### 🔍 فلترة وتخصيص بيانات التقارير والطباعة")
        col_f_date, col_f_grade, col_f_sec, col_f_period = st.columns(4)
        
        with col_f_date:
            unique_dates = ["الكل"] + (sorted(list(df['التاريخ'].unique())) if not df.empty else [str(date.today())])
            filter_date = st.selectbox("📅 اختر التاريخ:", unique_dates)
            
        with col_f_grade:
            all_grades = list(STUDENTS_DB.keys())
            filter_grade = st.selectbox("🏫 اختر الصف الدراسي:", ["الكل"] + all_grades)
            
        with col_f_sec:
            if filter_grade != "الكل":
                available_sections = list(STUDENTS_DB[filter_grade].keys())
                filter_section = st.selectbox("🚪 اختر الفصل:", ["الكل"] + available_sections)
            else:
                all_sections = []
                for g in STUDENTS_DB:
                    all_sections.extend(list(STUDENTS_DB[g].keys()))
                filter_section = st.selectbox("🚪 اختر الفصل:", ["الكل"] + sorted(list(set(all_sections))))
                
        with col_f_period:
            filter_period = st.selectbox("⏰ اختر الحصة:", ["الكل"] + PERIODS_LIST)

        df_filtered = df.copy() if not df.empty else pd.DataFrame()
        if not df_filtered.empty:
            if filter_date != "الكل":
                df_filtered = df_filtered[df_filtered['التاريخ'] == filter_date]
            if filter_grade != "الكل":
                df_filtered = df_filtered[df_filtered['الصف'] == filter_grade]
            if filter_section != "الكل":
                df_filtered = df_filtered[df_filtered['الفصل'] == filter_section]
            if filter_period != "الكل":
                df_filtered = df_filtered[df_filtered['الحصة'] == filter_period]

        tab_teachers, tab_absent, tab_out, tab_late, tab_all = st.tabs([
            "👨‍🏫 إحصائية وتقارير وتعديل المعلمين",
            "🔴 كشف الطلاب الغائبين", 
            "🟠 كشف الطلاب خارج الفصل", 
            "🟡 كشف المتأخرين عن الحصة", 
            "📋 السجل العام الشامل"
        ])
        
        # ---------------------------------------------------------
        # 1. إحصائيات المعلمين وزر بدء التقرير وعرض عدد مرات الغياب والتأخر
        # ---------------------------------------------------------
        with tab_teachers:
            st.markdown("### 👨‍🏫 إحصائية وحالة حضور وغياب كادر المعلمين")
            
            teacher_session_counts = {}
            if not df.empty:
                t_grouped = df.groupby('اسم المعلم')['الحصة'].nunique()
                teacher_session_counts = t_grouped.to_dict()

            st.markdown("#### ⚙️ رصد وتحديد حالة المعلمين اليومية:")
            
            teachers_summary_data = {}
            
            for t_name in TEACHERS_LIST:
                c_name_t, c_status_t, c_info_t = st.columns([2.5, 3, 2.5])
                c_name_t.markdown(f"**{t_name}**")
                
                cur_status = st.session_state['teacher_status_db'].get(t_name, "حاضر")
                new_status = c_status_t.radio(
                    f"حالة المعلم {t_name}:",
                    ["حاضر", "غائب", "متأخر"],
                    index=["حاضر", "غائب", "متأخر"].index(cur_status),
                    key=f"t_status_{t_name}",
                    horizontal=True
                )
                st.session_state['teacher_status_db'][t_name] = new_status
                
                sessions_done = teacher_session_counts.get(t_name, 0)
                c_info_t.write(f"الحصص المرصودة: `{sessions_done} حصة`")
                
                teachers_summary_data[t_name] = {
                    "status": new_status,
                    "sessions": sessions_done
                }

            st.write("---")
            
            # 💾 زر حفظ وإرسال كشف حضور المعلمين
            if st.button("💾 حفظ وإرسال كشف حضور المعلمين", type="primary", use_container_width=True, key="btn_save_send_teachers"):
                today_str = str(date.today())
                st.session_state['teacher_daily_logs'] = [r for r in st.session_state['teacher_daily_logs'] if r.get('التاريخ') != today_str]
                for t_name, info in teachers_summary_data.items():
                    st.session_state['teacher_daily_logs'].append({
                        "التاريخ": today_str,
                        "التاريخ_الهجري": gregorian_to_hijri_approx(date.today()),
                        "اسم المعلم": t_name,
                        "الحالة": info['status'],
                        "الحصص المرصودة": info['sessions'],
                        "ملاحظات": "تم الحفظ والإرسال"
                    })
                st.success("✨ تم حفظ وإرسال كشف حضور وغياب المعلمين بنجاح!")

            st.write("---")

            # ✏️ قسم أيقونة وتعديل سجلات رصد المعلمين اليومي
            with st.expander("✏️ أيقونة وتعديل حالة المعلمين وتوثيق الملاحظات اليومية"):
                st.info("💡 يمكنك تعديل حالة أي معلم أو إضافة ملاحظة ثم الضغط على حفظ التعديلات.")
                edit_date = st.date_input("اختر تاريخ التعديل:", date.today(), key="edit_t_date")
                
                today_logs = [r for r in st.session_state['teacher_daily_logs'] if r['التاريخ'] == str(edit_date)]
                if not today_logs:
                    today_logs = [
                        {
                            "التاريخ": str(edit_date),
                            "التاريخ_الهجري": gregorian_to_hijri_approx(edit_date),
                            "اسم المعلم": t,
                            "الحالة": "حاضر",
                            "الحصص المرصودة": teacher_session_counts.get(t, 0),
                            "ملاحظات": "-"
                        } for t in TEACHERS_LIST
                    ]

                updated_logs = []
                for t_log in today_logs:
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"**{t_log['اسم المعلم']}**")
                    new_st = c2.radio(
                        f"حالة {t_log['اسم المعلم']}",
                        ["حاضر", "غائب", "متأخر"],
                        index=["حاضر", "غائب", "متأخر"].index(t_log['الحالة']),
                        key=f"edit_st_{t_log['اسم المعلم']}_{edit_date}",
                        horizontal=True
                    )
                    new_note = c3.text_input(f"ملاحظة المعلم {t_log['اسم المعلم']}", value=t_log.get('ملاحظات', '-'), key=f"note_{t_log['اسم المعلم']}_{edit_date}")
                    
                    updated_logs.append({
                        "التاريخ": str(edit_date),
                        "التاريخ_الهجري": gregorian_to_hijri_approx(edit_date),
                        "اسم المعلم": t_log['اسم المعلم'],
                        "الحالة": new_st,
                        "الحصص المرصودة": t_log.get('الحصص المرصودة', 0),
                        "ملاحظات": new_note
                    })
                
                if st.button("💾 حفظ وتحديث تعديلات المعلمين", type="primary", key="btn_update_edited_teachers"):
                    st.session_state['teacher_daily_logs'] = [r for r in st.session_state['teacher_daily_logs'] if r['التاريخ'] != str(edit_date)]
                    st.session_state['teacher_daily_logs'].extend(updated_logs)
                    st.success("✨ تم حفظ وتعديل سجلات المعلمين بنجاح!")
                    st.rerun()

            st.write("---")
            
            # 🖨️ قسم اختيار الفترة الزمنية مع زر (▶️ بدء) وحساب عدد الغياب والتأخر
            st.markdown("### 🖨️ تقرير ملخص إحصائيات المعلمين للفترة (مع عدد مرات الغياب والتأخر)")
            
            col_r1, col_r2, col_r3, col_r4 = st.columns([2.5, 2.5, 2.5, 2.5])
            with col_r1:
                start_report_date = st.date_input("من تاريخ:", date.today() - timedelta(days=7), key="rep_start_date")
            with col_r2:
                end_report_date = st.date_input("إلى تاريخ:", date.today(), key="rep_end_date")
            with col_r3:
                calendar_type = st.radio("نظام التاريخ للتقرير:", ["ميلادي 📅", "هجري 🌙"], horizontal=True)
            with col_r4:
                st.write("")
                st.write("")
                btn_start_search = st.button("▶️ بدء عرض التقرير", type="primary", use_container_width=True)

            if btn_start_search:
                st.session_state['search_teacher_started'] = True

            # عرض التقرير فقط عند النقر على أيقونة/زر بدء
            if st.session_state.get('search_teacher_started', False):
                teacher_summary_list = []
                
                for t in TEACHERS_LIST:
                    t_logs = []
                    for r in st.session_state['teacher_daily_logs']:
                        if r['اسم المعلم'] == t:
                            try:
                                r_d = datetime.strptime(r['التاريخ'], "%Y-%m-%d").date()
                                if start_report_date <= r_d <= end_report_date:
                                    t_logs.append(r)
                            except:
                                pass
                    
                    p_cnt = sum(1 for x in t_logs if x['الحالة'] == "حاضر")
                    a_cnt = sum(1 for x in t_logs if x['الحالة'] == "غائب")
                    l_cnt = sum(1 for x in t_logs if x['الحالة'] == "متأخر")
                    tot_sess = sum(x.get('الحصص المرصودة', 0) for x in t_logs)
                    
                    teacher_summary_list.append({
                        "اسم المعلم": t,
                        "عدد أيام الحضور": p_cnt,
                        "عدد مرات الغياب": a_cnt,
                        "عدد مرات التأخر": l_cnt,
                        "إجمالي الحصص المرصودة": tot_sess
                    })

                df_t_summary = pd.DataFrame(teacher_summary_list)
                
                st.markdown(f"#### 📊 بيانات إحصائية المعلمين من `{start_report_date}` إلى `{end_report_date}`:")
                st.dataframe(df_t_summary, use_container_width=True)

                cal_sys_name = "هجري" if "هجري" in calendar_type else "ميلادي"
                html_t_range = generate_teacher_range_report_html(teacher_summary_list, start_report_date, end_report_date, cal_sys_name)
                
                teacher_range_excel_buffer = io.BytesIO()
                with pd.ExcelWriter(teacher_range_excel_buffer, engine='openpyxl') as writer:
                    df_t_summary.to_excel(writer, sheet_name='ملخص إحصائيات المعلمين', index=False)
                t_excel_data = teacher_range_excel_buffer.getvalue()

                col_down_t1, col_down_t2, col_down_t3 = st.columns(3)
                
                col_down_t1.download_button(
                    label="📊 حفظ تقرير الفترة (Excel)",
                    data=t_excel_data,
                    file_name=f"تقرير_إحصائيات_المعلمين_من_{start_report_date}_إلى_{end_report_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                col_down_t2.download_button(
                    label="📄 حفظ تقرير الفترة (CSV)",
                    data=df_t_summary.to_csv(index=False).encode('utf-8-sig'),
                    file_name=f"تقرير_إحصائيات_المعلمين_من_{start_report_date}_إلى_{end_report_date}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                col_down_t3.download_button(
                    label="🖨️ طباعة تقرير المعلمين للفترة (PDF)",
                    data=html_t_range.encode('utf-8'),
                    file_name=f"تقرير_إحصائيات_المعلمين_{cal_sys_name}_{start_report_date}_إلى_{end_report_date}.html",
                    mime="text/html",
                    key="btn_print_t_range",
                    use_container_width=True
                )
            else:
                st.info("👈 اختر نطاق التاريخ المطلوبة (من / إلى)، ثم انقر على زر **`▶️ بدء عرض التقرير`** للبدء وعرض البيانات.")

        # ---------------------------------------------------------
        # 2. كشف الطلاب الغائبين
        # ---------------------------------------------------------
        with tab_absent:
            if not df_filtered.empty:
                df_absent = df_filtered[df_filtered['الحالة'] == 'غائب']
                st.markdown(f"### 🔴 قائمة أسماء الطلاب الغائبين (`العدد: {len(df_absent)} طالب`)")
                if not df_absent.empty:
                    st.dataframe(df_absent[['اسم الطالب', 'رقم الطالب', 'الصف', 'الفصل', 'الحصة', 'اسم المعلم', 'التاريخ']], use_container_width=True)
                    
                    title_suffix = f" - (الصف: {filter_grade} | الفصل: {filter_section} | الحصة: {filter_period} | التاريخ: {filter_date})"
                    html_absent = generate_printable_html(df_absent, f"كشف أسماء الطلاب الغائبين {title_suffix}")
                    st.download_button(
                        label="🖨️ فتح صفحة طباعة كشف الغائبين (PDF)",
                        data=html_absent.encode('utf-8'),
                        file_name=f"كشف_الطلاب_الغائبين_{date.today()}.html",
                        mime="text/html",
                        key="btn_print_absent"
                    )
                else:
                    st.success("🎉 لا يوجد طلاب غائبون ضمن خيارات التصفية المحددة!")
            else:
                st.info("لا توجد بيانات مرصودة تطابق الفلترة المحددة.")

        # ---------------------------------------------------------
        # 3. كشف الطلاب خارج الفصل
        # ---------------------------------------------------------
        with tab_out:
            if not df_filtered.empty:
                df_out = df_filtered[df_filtered['الحالة'] == 'خارج الفصل']
                st.markdown(f"### 🟠 قائمة أسماء الطلاب خارج الفصل (`العدد: {len(df_out)} طالب`)")
                if not df_out.empty:
                    st.dataframe(df_out[['اسم الطالب', 'رقم الطالب', 'الصف', 'الفصل', 'الحصة', 'اسم المعلم', 'التاريخ']], use_container_width=True)
                    
                    title_suffix = f" - (الصف: {filter_grade} | الفصل: {filter_section} | الحصة: {filter_period} | التاريخ: {filter_date})"
                    html_out = generate_printable_html(df_out, f"كشف الطلاب خارج الفصل {title_suffix}")
                    st.download_button(
                        label="🖨️ فتح صفحة طباعة كشف خارج الفصل (PDF)",
                        data=html_out.encode('utf-8'),
                        file_name=f"كشف_الطلاب_خارج_الفصل_{date.today()}.html",
                        mime="text/html",
                        key="btn_print_out"
                    )
                else:
                    st.success("✅ لا يوجد طلاب خارج الفصل ضمن خيارات التصفية المحددة!")
            else:
                st.info("لا توجد بيانات مرصودة تطابق الفلترة المحددة.")

        # ---------------------------------------------------------
        # 4. كشف المتأخرين
        # ---------------------------------------------------------
        with tab_late:
            if not df_filtered.empty:
                df_late = df_filtered[df_filtered['الحالة'] == 'متأخر']
                st.markdown(f"### 🟡 قائمة أسماء الطلاب المتأخرين (`العدد: {len(df_late)} طالب`)")
                if not df_late.empty:
                    st.dataframe(df_late[['اسم الطالب', 'رقم الطالب', 'الصف', 'الفصل', 'الحصة', 'اسم المعلم', 'التاريخ']], use_container_width=True)
                    
                    title_suffix = f" - (الصف: {filter_grade} | الفصل: {filter_section} | الحصة: {filter_period} | التاريخ: {filter_date})"
                    html_late = generate_printable_html(df_late, f"كشف الطلاب المتأخرين {title_suffix}")
                    st.download_button(
                        label="🖨️ فتح صفحة طباعة كشف المتأخرين (PDF)",
                        data=html_late.encode('utf-8'),
                        file_name=f"كشف_الطلاب_المتأخرين_{date.today()}.html",
                        mime="text/html",
                        key="btn_print_late"
                    )
                else:
                    st.success("✨ لا يوجد طلاب متأخرون ضمن خيارات التصفية المحددة!")
            else:
                st.info("لا توجد بيانات مرصودة تطابق الفلترة المحددة.")

        # ---------------------------------------------------------
        # 5. السجل العام والتصدير
        # ---------------------------------------------------------
        with tab_all:
            if not df_filtered.empty:
                st.markdown("### 📋 السجل العام الشامل للبيانات المفلترة")
                st.dataframe(df_filtered, use_container_width=True)
                
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df_filtered.to_excel(writer, sheet_name='السجل المفلتر', index=False)
                    df_filtered[df_filtered['الحالة'] == 'غائب'].to_excel(writer, sheet_name='كشف الغياب', index=False)
                    df_filtered[df_filtered['الحالة'] == 'خارج الفصل'].to_excel(writer, sheet_name='خارج الفصل', index=False)
                    df_filtered[df_filtered['الحالة'] == 'متأخر'].to_excel(writer, sheet_name='كشف المتأخرين', index=False)
                    
                excel_data = excel_buffer.getvalue()
                
                col_down1, col_down2 = st.columns(2)
                col_down1.download_button(
                    label="📊 تحميل التقرير المفلتر (Excel)",
                    data=excel_data,
                    file_name=f"تقرير_حضور_مفلتر_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                col_down2.download_button(
                    label="📄 تحميل التقرير كملف CSV",
                    data=df_filtered.to_csv(index=False).encode('utf-8-sig'),
                    file_name=f"تقرير_حضور_مفلتر_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
                title_suffix = f" - (الصف: {filter_grade} | الفصل: {filter_section} | الحصة: {filter_period} | التاريخ: {filter_date})"
                html_full = generate_printable_html(df_filtered, f"التقرير الشامل لحضور وغياب الطلاب {title_suffix}")
                st.download_button(
                    label="🖨️ فتح صفحة طباعة السجل العام (PDF)",
                    data=html_full.encode('utf-8'),
                    file_name=f"التقرير_اليومي_الشامل_{date.today()}.html",
                    mime="text/html",
                    key="btn_print_full"
                )
            else:
                st.info("لا توجد بيانات حضور مرصودة في السجل اليومي.")

### ---------------------------------------------------------
### 10. الهيكل الإداري وتوقيع المصمم البارز في الشريط الجانبي
### ---------------------------------------------------------
st.sidebar.markdown("""
<div class="sidebar-admin-box">
    <div class="sidebar-admin-title">🏫 الهيكل الإداري للمدرسة</div>
    <div class="sidebar-admin-item"><b>مدير المدرسة:</b> إبراهيم بن موسى التميمي</div>
    <div class="sidebar-admin-item"><b>وكيل الشؤون التعليمية:</b> محمد مبروك السيد</div>
    <div class="sidebar-admin-item"><b>وكيل شؤون الطلاب:</b> صالح بن عبدالله الدعجاني</div>
    <div class="designer-badge">
        ✨ تصميم الأستاذ: محمد سامي السعيد ✨
    </div>
</div>
""", unsafe_allow_html=True)
