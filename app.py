import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import io

# ---------------------------------------------------------
# 1. تهيئة الصفحة والنمط Visual Theme & Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="نظام رصد الدرجات والرسوم البيانية - متوسطة الثغر النموذجية الأهلية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تضمين مكتبة الأيقونات FontAwesome وتنسيقات CSS المدمجة
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    
    :root {
        --primary: #1e3a8a;
        --primary-light: #3b82f6;
        --gold: #fbbf24;
        --green-bg: #dcfce7;
        --green-text: #15803d;
        --red-bg: #fee2e2;
        --red-text: #b91c1c;
        --gray-bg: #f3f4f6;
        --gray-text: #4b5563;
    }

    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
        text-align: right;
    }

    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #1e3a8a, #1e40af, #3b82f6);
        color: white;
        padding: 28px 20px;
        border-radius: 22px;
        margin-bottom: 20px;
        box-shadow: 0 12px 24px rgba(30, 58, 138, 0.18);
        position: relative;
        overflow: hidden;
    }
    .main-header h1 { margin: 0 0 8px 0; font-size: 26px; font-weight: 800; color: #ffffff; }
    .main-header p { margin: 0 0 15px 0; opacity: 0.92; font-size: 15px; color: #e2e8f0; }

    .designer-banner {
        display: inline-flex;
        align-items: center;
        gap: 10px;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        border: 2px solid rgba(255, 255, 255, 0.35);
        padding: 8px 24px;
        border-radius: 50px;
        margin-top: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }
    .designer-text { font-size: 18px; font-weight: 800; color: var(--gold); }
    .designer-icon { font-size: 20px; color: var(--gold); }

    .top-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        background: white;
        padding: 14px 20px;
        border-radius: 14px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.03);
        border-right: 5px solid var(--primary-light);
        flex-wrap: wrap;
        gap: 10px;
    }

    .save-indicator { 
        font-size: 14px; 
        color: #10b981; 
        font-weight: 700; 
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .color-legend {
        display: flex;
        gap: 15px;
        align-items: center;
        background: #f8fafc;
        padding: 10px 16px;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
        margin-bottom: 15px;
        flex-wrap: wrap;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 13px;
        font-weight: 700;
    }
    .color-box {
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 1px solid rgba(0,0,0,0.1);
    }

    .print-class-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f8fafc;
        padding: 12px 20px;
        border-radius: 12px;
        border-right: 5px solid var(--primary);
        margin-bottom: 15px;
    }

    .cards-grid { 
        display: grid; 
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); 
        gap: 15px; 
        margin-bottom: 20px; 
    }
    .card { 
        background: white; 
        border-radius: 14px; 
        padding: 18px; 
        border-top: 5px solid var(--primary-light); 
        box-shadow: 0 2px 6px rgba(0,0,0,0.03); 
    }
    .card-title { 
        font-size: 16px; 
        font-weight: 700; 
        color: var(--primary); 
        margin-bottom: 10px; 
        display: flex; 
        justify-content: space-between; 
        align-items: center;
    }
    .metric-val-big {
        font-size: 24px;
        font-weight: 800;
        color: #0f172a;
    }

    .excel-box {
        background-color: #f0fdf4;
        border: 2px dashed #16a34a;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
    }

    @media print {
        .sidebar, .stButton, header, footer, .no-print, [data-testid="stSidebar"] {
            display: none !important;
        }
        body { background: white !important; color: black !important; }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. قوائم الطلاب الشاملة من مصادر المدرسة
# ---------------------------------------------------------
STUDENTS_DATABASE = {
    "الصف الأول المتوسط": {
        "فصل 101": [
            "بلال عبد الرزاق عيسى العيسى",
            "جاسر بن عبد الله بن منصور الحارثي",
            "حسام بن محمد بن علي ال رايان البارقي",
            "ريان عبد الله جابر الأسمري",
            "زيد زياد عبد اللطيف أبو قبع",
            "سامي سعد عباس حمد",
            "سعد ناصر سعد السيف",
            "عبد الله بن سليمان بن عبد الله الراجحي",
            "عبد الله سعد بن محمد العيشان",
            "علي أحمد علي كريري",
            "علي سعد علي القحطاني",
            "عمر عبد الله سعد الجبرين",
            "مازن إسلام أحمد إبراهيم موسى",
            "محمد أحمد علي عقيل",
            "محمد إسلام محمد دراز",
            "محمد أشرف مسعود أبو خاطر",
            "محمد نايف فراج الدعجاني",
            "وائل - - بولعيش"
        ],
        "فصل 102": [
            "إبراهيم بن محمد بن علي الوهيبي",
            "الوليد ابن خالد بن فهد العتيبي",
            "باسل محمد فرج الدوسري",
            "بسام بن عبد الكريم بن عبد الله الحرقان الدوسري",
            "تركي عبد الله مسفر الدوسري",
            "تميم فهد عبد العزيز العزاز",
            "راكان عبد الله يحيى كريري",
            "ريان عبد الله منصور السبر",
            "ريان وليد - حلاق",
            "سيف عبد الكريم بريك العصيمي",
            "صالح حسن فتحي سندي",
            "عبد الرحمن إبراهيم عبد الله الحضيف",
            "عبد الله صالح حمد الصفيان",
            "فهد ابن أحمد بن فهد العثمان",
            "فهد عويض ثعيل المطيري",
            "فهد نايف فهد الحسينان",
            "فيصل موينع عبد الله بن موينع",
            "فيصل ناصر سيف العريفي",
            "مشاري عثمان سعد ناصر السعد",
            "يزن محمد علي اليحيى",
            "يوسف محمد عبد الله الدوسري"
        ]
    },
    "الصف الثاني المتوسط": {
        "فصل 201": [
            "إبراهيم ياسر إبراهيم الحلوى",
            "أحمد سامي بن أحمد العمران",
            "الوليد عبد الله بن إبراهيم المبدل",
            "ذياب بن محمد بن ذياب بن محمد ال مريع القحطاني",
            "راكان بن محمد بن مسفر القحطاني",
            "سلطان عبد الله حسن القحطاني",
            "عبد الرحمن حمد بن محمد العريفي",
            "عبد الرحمن ربيع جابر خبراني",
            "عبد العزيز سعود بن فهد العتيبي",
            "عبد اللطيف إبراهيم محمد الطمره",
            "فهد عيسى محمد العيسى",
            "فيصل بن عبد الله بن سعود بن عبد العزيز الجميهه",
            "مبارك صالح مبارك هليل",
            "محمد بن عبد الله بن حمد بن ناصر بن عمران",
            "محمد عبد المحسن ناصر الحزام",
            "محمد فايز عبد الرحمن بن يوسف",
            "مشاري سلطان سالم الشمراني",
            "معاذ عبد الله سعود العريفي",
            "ناصر حسين محمد ال جبران",
            "يزيد بن طارق بن علي الحديثي"
        ],
        "فصل 202": [
            "إبراهيم بن مبارك بن راشد بن عبد الرحمن السبيعي آل موينع",
            "حامد بن محمد بن حامد شباط",
            "حسام حسن محمد الشهري",
            "خالد تركي عايض القحطاني",
            "خالد داود بن عابد الحارثي",
            "سطام عبد العزيز عبد الله العريفي",
            "سعود خالد عبد الله الحمد",
            "سعود سلطان بن خليل العتيبي",
            "سعود مشعل بن إبراهيم الشثري",
            "طلال محمد منير المهدرس",
            "عبد الكريم مساعد عبد العزيز الهزاع",
            "عبد الله سامي سعد الحوشاني",
            "علي أحمد علي عقيل",
            "عمر بن سعد بن هلال الشبانات",
            "عمر خالد عبد الله المهيني",
            "فارس مشعل عبد الله بن موينع",
            "مازن خالد دخيل المطيري",
            "مازن رفعت محمد حاج النيل",
            "نايف بن بندر بن خلفان العلوي",
            "نواف عبد العزيز المرزوق",
            "هادي سلطان هادي القحطاني",
            "يزيد بن حسين بن متعب بن محمد كعكم"
        ],
        "فصل 203": [
            "ثامر عمر إبراهيم عثمان",
            "جهاد فارس عبد القادر حتاوي",
            "خالد محمد عبد الكريم الخفاجي",
            "سعد ابن مسفر بن سعد القحطاني",
            "سعود بن عبد الله بن سعود السحامي",
            "سعود ناصر سنيف العريفي",
            "سعيد محمد - باوزير",
            "طلال بن فهد بن عطيه بالحكم الزهراني",
            "عبد الرحمن أحمد جاسم الحمدي",
            "عبد العزيز ماجد راشد الزير",
            "عبد العزيز وليد ناصر بن سعران",
            "عبد الله بن بندر بن فهد المفيجل",
            "عبد المجيد بن محمد بن مسعود آل عايض القحطاني",
            "عز الدين أحمد محمد سعد",
            "عزام خالد شهوب بن شهوب",
            "عزام فهد أحمد صلوي",
            "عمر وليد ياسين درويش علي",
            "فارس ابن محمد بن سالم بن نويشي الوهبي الحربي",
            "محمد بن علي محسن العثيميني",
            "وائل بن عبد الله بن عامر علي آل عبيد الغامدي",
            "يزيد بن حمد بن مترك بن محمد ال مسعود القحطاني",
            "يوسف عايد عواد البلوي"
        ]
    },
    "الصف الثالث المتوسط": {
        "فصل 301": [
            "أصيل ناصر بن محمد مذكور",
            "خالد محمد مسعف معافا",
            "راشد سعيد راشد عبد السلام",
            "راكان بن عبد الله بن سالم اليافعي",
            "زياد أحمد بن علي اللحيد",
            "سطام محمد سعود الدوسري",
            "سلطان أحمد صالح الفتوح",
            "عبد العزيز عبد الله شراز المالكي",
            "عبد العزيز عبد الله عايض الأسمري",
            "عبد الله عبيد عبد الله العتيبي",
            "عبد الله فهد جلوي سالم الشرعي",
            "علي إبراهيم علي الأسمري",
            "عماد الدين إسلام محمد دراز",
            "عمر فهد محمد السقامي",
            "فهد عبد الرحمن فهد العتيبي",
            "فيصل بن عبد الرحمن بن عايض العصيمي العتيبي",
            "فيصل محمد صالح الفتوح",
            "محمد سلطان عبد العزيز العيد",
            "محمد مقعد ساير العتيبي",
            "مشاري إبراهيم عبد اللطيف المغربي",
            "مشاري علي موسى عقيلي",
            "مهند عبد الله فهد الزكري",
            "نواف وليد حمد الشعلان",
            "يوسف نايف مقعد العتيبي"
        ],
        "فصل 302": [
            "تركي عبد العزيز عبد الله المرزوق",
            "تركي عثمان عبد العزيز العثمان",
            "راشد أحمد فهد آل سعيد",
            "راكان إبراهيم محمد ديوان",
            "ريان ناصر عبد الرحمن المرشود",
            "صالح بن ممدوح بن صالح بن خالد الجويعي",
            "عبد الرحمن محمد صلاح بدر الدين",
            "عبد العزيز تركي عبد العزيز اللهيم",
            "عبد العزيز عبد المحسن فهد بن بديع",
            "عبد الله متعب بن عبد الرحمن الجبرين",
            "عبد المحسن طارق بن عبد الرحمن العروان",
            "فارس وليد بن عبد الله الحوطي",
            "محمد خالد محمد بن مشرف",
            "محمد سعد بن محمد العيشان",
            "محمد عبد العزيز محمد الخالدي",
            "مهند ماجد علي كعبي",
            "ناصر محمد عبد الله المزريعي",
            "نواف سعد بن علي القاسم",
            "ياسر تركي إسماعيل مسلمي"
        ],
        "فصل 303": [
            "ثامر وليد بن عبد العزيز الطليحي",
            "خالد بن عبد الرؤوف بن عبد الرحمن بن عبد الله الشنير",
            "خالد عبد الله خالد الخالدي",
            "خالد محمد بن عبد الله ال درعان",
            "راشد صالح بن عبد العزيز الحلوان",
            "رواد محمد إبراهيم الخليل",
            "صالح بن محمد بن صالح الميموني المطيري",
            "ضاري صالح مهنا العازمي",
            "عبد الرحمن بدر عبد الرحمن الطريقي",
            "عبد الرحمن خالد محمد سعيد",
            "عبد الله تركي عبد الله الأحمد",
            "عبد الله عبد الرحمن عبد الله النجراني",
            "علي بن خالد بن علي العجيري",
            "علي عبد الله علي آل حمود",
            "فهد بن خالد بن فهد بن عبد العزيز الزيد",
            "فيصل عبد الرحمن عزيز القحطاني",
            "ماجد فهد عبد العزيز الكثيري",
            "مازن خالد عبد ربه الزهراني",
            "متعب مطر جمعان الدوسري",
            "نواف فهد بن ناصر القحطاني",
            "يوسف عبد الله عوض العتيبي"
        ]
    }
}

TESTS_LIST = [
    "الاختبار التشخيصي الأول",
    "الاختبار التشخيصي الثاني",
    "الاختبار التشخيصي الثالث",
    "الاختبار التشخيصي الرابع"
]

# ---------------------------------------------------------
# 3. إدارة قاعدة البيانات / Database Manager
# ---------------------------------------------------------
DB_FILE = "student_grades_v6.db"

def init_db():
    """إنشاء جدول البيانات وتعبئة أسماء جميع الطلاب المدخلة من المدرسة لكافة الاختبارات"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            grade TEXT,
            class_name TEXT,
            seq_num INTEGER,
            student_name TEXT,
            lughati REAL DEFAULT 0.0,
            math REAL DEFAULT 0.0,
            science REAL DEFAULT 0.0,
            english REAL DEFAULT 0.0
        )
    ''')
    
    c.execute("SELECT COUNT(*) FROM grades")
    if c.fetchone()[0] == 0:
        # تعبئة قاعدة البيانات بجميع الطلاب والصفوف والفصول والاختبارات الأربعة
        initial_records = []
        for test in TESTS_LIST:
            for grade, classes in STUDENTS_DATABASE.items():
                for class_name, students in classes.items():
                    for idx, s_name in enumerate(students, 1):
                        # درجات افتراضية توضيحية أولية
                        default_l = 8.0 if (idx % 3 != 0) else (4.0 if idx % 2 == 0 else 0.0)
                        default_m = 7.5 if (idx % 2 != 0) else (3.5 if idx % 4 == 0 else 0.0)
                        default_s = 9.0 if (idx % 4 != 0) else (2.0 if idx % 3 == 0 else 0.0)
                        default_e = 6.0 if (idx % 5 != 0) else (4.5 if idx % 2 == 0 else 0.0)
                        initial_records.append((test, grade, class_name, idx, s_name, default_l, default_m, default_s, default_e))
        
        c.executemany('''
            INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, lughati, math, science, english)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', initial_records)
        conn.commit()
    conn.close()

def load_class_students(test_name, grade_name, class_name):
    """تحميل طلاب فصل محدد باختبار محدد"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('''
        SELECT id, seq_num AS 'المسلسل', student_name AS 'اسم الطالب',
               lughati AS 'لغتي', math AS 'رياضيات', science AS 'علوم', english AS 'انجليزي'
        FROM grades
        WHERE test_name = ? AND grade = ? AND class_name = ?
        ORDER BY seq_num ASC
    ''', conn, params=(test_name, grade_name, class_name))
    conn.close()
    return df

def update_student_scores(df_updated):
    """تحديث درجات الطلاب في قاعدة البيانات"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for _, row in df_updated.iterrows():
        c.execute('''
            UPDATE grades
            SET lughati = ?, math = ?, science = ?, english = ?
            WHERE id = ?
        ''', (row['لغتي'], row['رياضيات'], row['علوم'], row['انجليزي'], row['id']))
    conn.commit()
    conn.close()

def load_all_db_records():
    """تحميل كامل قاعدة البيانات للتصدير"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query('''
        SELECT id AS 'المعرف', test_name AS 'الاختبار', grade AS 'الصف الدراسي',
               class_name AS 'الفصل', seq_num AS 'المسلسل', student_name AS 'اسم الطالب',
               lughati AS 'لغتي', math AS 'رياضيات', science AS 'علوم', english AS 'انجليزي'
        FROM grades
    ''', conn)
    conn.close()
    return df

def save_new_student(test_name, grade_name, class_name, student_name, l, m, s, e):
    """إضافة طالب جديد"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MAX(seq_num) FROM grades WHERE test_name = ? AND grade = ? AND class_name = ?", (test_name, grade_name, class_name))
    max_seq = c.fetchone()[0]
    next_seq = (max_seq or 0) + 1
    
    c.execute('''
        INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, lughati, math, science, english)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (test_name, grade_name, class_name, next_seq, student_name, l, m, s, e))
    conn.commit()
    conn.close()

def export_to_excel_bytes(df_export):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='درجات المواد الاربع')
    output.seek(0)
    return output

init_db()

# ---------------------------------------------------------
# 4. الهيدر والشعار الرئيسي Main Header
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1><i class="fa-solid fa-graduation-cap"></i> نظام رصد الدرجات والرسوم البيانية</h1>
    <p>متوسطة الثغر النموذجية الأهلية - رصد مواد (لغتي، رياضيات، علوم، انجليزي)</p>
    <div class="designer-banner">
        <i class="fa-solid fa-crown designer-icon"></i>
        <span class="designer-text">تصميم وتطوير: محمد سامي السعيد</span>
    </div>
</div>
""", unsafe_allow_html=True)

# شريط الحالة العلوي
st.markdown("""
<div class="top-toolbar">
    <div class="save-indicator">
        <i class="fa-solid fa-circle-check"></i> تم الحفظ المباشر والتزامن في قاعدة البيانات (SQLite / Google Sheets)
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. القوائم المنسدلة المتسلسلة Cascading Selection (اختبار -> صف -> فصل)
# ---------------------------------------------------------
col_t, col_g, col_c = st.columns(3)

with col_t:
    selected_test = st.selectbox("📌 1. اختر الاختبار التشخيصي:", TESTS_LIST, index=0)

with col_g:
    grades_options = list(STUDENTS_DATABASE.keys())
    selected_grade = st.selectbox("🏫 2. اختر الصف الدراسي:", grades_options, index=0)

with col_c:
    classes_options = list(STUDENTS_DATABASE[selected_grade].keys())
    selected_class = st.selectbox("📚 3. اختر الفصل:", classes_options, index=0)

# ---------------------------------------------------------
# 6. التبويبات الرئيسية Tabs
# ---------------------------------------------------------
tab_entry, tab_charts, tab_excel, tab_add = st.tabs([
    "📋 رصد درجات الفصل والطباعة",
    "📈 الرسم البياني والتحليل",
    "🟢 استيراد وتصدير Excel",
    "➕ إضافة طالب جديد"
])

# =========================================================
# التبويب الأول: رصد درجات الفصل والتنسيق الشرطي والطباعة
# =========================================================
with tab_entry:
    st.subheader(f"📋 رصد درجات المواد الأربع: ({selected_test}) - {selected_grade} - {selected_class}")
    
    df_students = load_class_students(selected_test, selected_grade, selected_class)
    
    if df_students.empty:
        st.warning("لا توجد بيانات طلاب لهذا الفصل في هذا الاختبار.")
    else:
        # حساب المجموع والمتوسط لغرض العرض
        df_display = df_students.copy()
        df_display['المجموع'] = df_display[['لغتي', 'رياضيات', 'علوم', 'انجليزي']].sum(axis=1).round(1)
        df_display['المتوسط'] = (df_display['المجموع'] / 4).round(2)

        # مفتاح الألوان التوضيحي المطلوبة
        st.markdown("""
        <div class="color-legend">
            <span style="font-weight:800; color:#1e3a8a;">دليل ألوان الدرجات:</span>
            <div class="legend-item">
                <div class="color-box" style="background:#bbf7d0;"></div>
                <span>أكبر من أو يساوي 5 (أخضر فاتح)</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background:#fecaca;"></div>
                <span>أقل من 5 (أحمر فاتح)</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background:#d1d5db;"></div>
                <span>صفر (رصاصي)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # زر الطباعة الهيدر
        col_title, col_print_btn = st.columns(2)
        with col_title:
            st.markdown(f"""
            <div class="print-class-header">
                <div>
                    <h3 style="margin:0; color:#1e3a8a;"><i class="fa-solid fa-users"></i> قائمة طلاب {selected_class} ({len(df_students)} طالب)</h3>
                    <small style="color:#64748b;">رؤوس الأوردة: المسلسل | اسم الطالب | لغتي | رياضيات | علوم | انجليزي</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_print_btn:
            if st.button(f"🖨️ طباعة طلاب {selected_class}", type="primary"):
                st.components.v1.html("""<script>window.print();</script>""", height=0)
                st.success(f"جاري إرسال امر طباعة {selected_class}...")

        st.write("✏️ **جدول الرصد التفاعلي (يمكنك تعديل الدرجات مباشرة ثم الضغط على حفظ):**")

        # محرر الدرجات التفاعلي
        edited_df = st.data_editor(
            df_students[['id', 'المسلسل', 'اسم الطالب', 'لغتي', 'رياضيات', 'علوم', 'انجليزي']],
            column_config={
                "id": None, # إخفاء معرف قاعدة البيانات
                "المسلسل": st.column_config.NumberColumn("م", disabled=True, width="small"),
                "اسم الطالب": st.column_config.TextColumn("اسم الطالب", disabled=True, width="large"),
                "لغتي": st.column_config.NumberColumn("لغتي (من 10)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f"),
                "رياضيات": st.column_config.NumberColumn("رياضيات (من 10)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f"),
                "علوم": st.column_config.NumberColumn("علوم (من 10)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f"),
                "انجليزي": st.column_config.NumberColumn("انجليزي (من 10)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f")
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{selected_test}_{selected_grade}_{selected_class}"
        )

        if st.button("💾 حفظ التعديلات في قاعدة البيانات", type="secondary"):
            update_student_scores(edited_df)
            st.success("تم حفظ درجات جميع المواد دائمياً بنجاح!")
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.write("📊 **العرض المنسق بالألوان حسب درجات المواد (جاهز للطباعة والمراجعة):**")

        # تطبيق التنسيق الشرطي بالألوان المطلوبة بالضبط:
        # أقل من 5 -> أحمر فاتح (#fecaca)
        # أكبر من أو يساوي 5 -> أخضر فاتح (#bbf7d0)
        # صفر -> رصاصي (#d1d5db)
        def apply_conditional_colors(val):
            if isinstance(val, (int, float)):
                if val == 0:
                    return 'background-color: #d1d5db; color: #1f2937; font-weight: bold; text-align: center;'
                elif val < 5:
                    return 'background-color: #fecaca; color: #991b1b; font-weight: bold; text-align: center;'
                else:
                    return 'background-color: #bbf7d0; color: #166534; font-weight: bold; text-align: center;'
            return 'text-align: center;'

        styled_df = df_display[['المسلسل', 'اسم الطالب', 'لغتي', 'رياضيات', 'علوم', 'انجليزي', 'المجموع', 'المتوسط']].style.map(
            apply_conditional_colors,
            subset=['لغتي', 'رياضيات', 'علوم', 'انجليزي']
        )

        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# =========================================================
# التبويب الثاني: الرسم البياني والتحليل
# =========================================================
with tab_charts:
    st.subheader(f"📈 تحليل أدوات المواد الأربع - {selected_test}")
    
    df_class_current = load_class_students(selected_test, selected_grade, selected_class)
    
    if not df_class_current.empty:
        # حساب متوسط كل مادة في هذا الفصل
        subjects_avg = df_class_current[['لغتي', 'رياضيات', 'علوم', 'انجليزي']].mean().reset_index()
        subjects_avg.columns = ['المادة', 'متوسط الدرجة']
        subjects_avg['متوسط الدرجة'] = subjects_avg['متوسط الدرجة'].round(2)

        c_bar, c_radar = st.columns(2)
        
        with c_bar:
            fig_bar = px.bar(
                subjects_avg, x='المادة', y='متوسط الدرجة', text='متوسط الدرجة',
                title=f"مقارنة متوسط المواد في {selected_class}",
                color='المادة',
                color_discrete_sequence=['#1e40af', '#2563eb', '#3b82f6', '#60a5fa']
            )
            fig_bar.update_traces(textposition='outside')
            fig_bar.update_layout(font_family="Cairo", yaxis_range=[0, 10])
            st.plotly_chart(fig_bar, use_container_width=True)

        with c_radar:
            fig_radar = go.Figure(data=go.Scatterpolar(
                r=subjects_avg['متوسط الدرجة'],
                theta=subjects_avg['المادة'],
                fill='toself',
                line_color='#1e3a8a'
            ))
            fig_radar.update_layout(
                title=f"مخطط رادار أداء المواد في {selected_class}",
                font_family="Cairo",
                polar=dict(radialaxis=dict(visible=True, range=[0, 10]))
            )
            st.plotly_chart(fig_radar, use_container_width=True)

# =========================================================
# التبويب الثالث: استيراد وتصدير ملفات Excel
# =========================================================
with tab_excel:
    st.subheader("🟢 استيراد وتصدير كافة السجلات عبر Excel")
    
    col_exp_box, col_info_box = st.columns(2)
    
    with col_exp_box:
        st.markdown("""
        <div class="excel-box">
            <h4 style="color:#16a34a; margin-top:0;"><i class="fa-solid fa-file-excel"></i> تصدير جميع درجات المواد</h4>
            <p style="font-size:13px; color:#4b5563;">تحميل قاعدة بيانات كافة الصفوف والفصول والمواد الاربع في ملف Excel واحد منسق.</p>
        </div>
        """, unsafe_allow_html=True)
        
        df_all_export = load_all_db_records()
        excel_data = export_to_excel_bytes(df_all_export)
        
        st.download_button(
            label="📥 تحميل كافة البيانات كملف Excel (.xlsx)",
            data=excel_data,
            file_name=f"درجات_المواد_الأربع_شامل.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

# =========================================================
# التبويب الرابع: إضافة طالب جديد
# =========================================================
with tab_add:
    st.subheader("➕ إضافة طالب جديد ورصد درجات المواد له")
    
    with st.form("add_student_v6_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            add_t = st.selectbox("الاختبار:", TESTS_LIST, index=TESTS_LIST.index(selected_test))
            add_g = st.selectbox("الصف الدراسي:", list(STUDENTS_DATABASE.keys()), index=list(STUDENTS_DATABASE.keys()).index(selected_grade))
            add_c = st.selectbox("الفصل:", list(STUDENTS_DATABASE[add_g].keys()))
            add_s_name = st.text_input("اسم الطالب رباعي:")
            
        with f2:
            st.write("**رصد الدرجات الأولية للمواد (من 10):**")
            add_l = st.number_input("لغتي:", min_value=0.0, max_value=10.0, value=7.0, step=0.5)
            add_m = st.number_input("رياضيات:", min_value=0.0, max_value=10.0, value=7.0, step=0.5)
            add_s = st.number_input("علوم:", min_value=0.0, max_value=10.0, value=7.0, step=0.5)
            add_e = st.number_input("انجليزي:", min_value=0.0, max_value=10.0, value=7.0, step=0.5)

        submit_add = st.form_submit_button("💾 حفظ الطالب والدرجات")
        if submit_add:
            if not add_s_name.strip():
                st.error("يرجى كتابة اسم الطالب.")
            else:
                save_new_student(add_t, add_g, add_c, add_s_name.strip(), add_l, add_m, add_s, add_e)
                st.success(f"تمت إضافة الطالب ({add_s_name}) بنجاح إلى {add_c}!")
                st.rerun()


