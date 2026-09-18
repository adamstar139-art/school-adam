import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import gspread
from google.oauth2.service_account import Credentials

# =========================================================
# 1. تهيئة الصفحة والإعدادات العامة
# =========================================================
st.set_page_config(
    page_title="نظام رصد الدرجات والرسوم البيانية",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DB_FILE = "student_grades.db"
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1XuneQDIfvpqKiuPQ-BcNBfOOm2G4vFBvwIa5F5gV15g/edit?usp=sharing"

TESTS_LIST = [
    "الاختبار التشخيصي الأول",
    "الاختبار التشخيصي الثاني",
    "الاختبار التشخيصي الثالث",
    "الاختبار التشخيصي الرابع"
]

# قاموس تحويل أسماء الأعمدة من الإنجليزية (SQLite) إلى العربية (Google Sheets)
COLUMN_MAPPING_TO_ARABIC = {
    "test_name": "الاختبار",
    "grade": "الصف الدراسي",
    "class_name": "الفصل",
    "seq_num": "المسلسل",
    "student_name": "اسم الطالب",
    "science": "علوم",
    "math": "رياضيات",
    "lughati": "لغتي",
    "english": "انجليزي"
}

# قاموس العكس: من العربية (Google Sheets) إلى الإنجليزية (SQLite)
COLUMN_MAPPING_TO_ENGLISH = {v: k for k, v in COLUMN_MAPPING_TO_ARABIC.items()}

# الترتيب القياسي للأعمدة بالعربية
ARABIC_COLUMNS_ORDER = [
    "الاختبار", "الصف الدراسي", "الفصل", "المسلسل", "اسم الطالب",
    "علوم", "رياضيات", "لغتي", "انجليزي"
]

# ---------------------------------------------------------
# الاتصال بـ Google Sheets
# ---------------------------------------------------------
def get_gsheet_worksheet():
    """الاتصال بـ Google Sheets عبر st.secrets أو service_account.json المحلي"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        try:
            info = dict(st.secrets["gcp_service_account"])
            if "private_key" in info and isinstance(info["private_key"], str):
                info["private_key"] = info["private_key"].replace(chr(92) + "n", chr(10))
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            client = gspread.authorize(creds)
            return client.open_by_url(SPREADSHEET_URL).sheet1
        except Exception as e:
            st.error(f"❌ فشل الاتصال عبر st.secrets: {e}")

    if os.path.exists("service_account.json"):
        try:
            creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
            client = gspread.authorize(creds)
            return client.open_by_url(SPREADSHEET_URL).sheet1
        except Exception as e:
            st.error(f"❌ فشل الاتصال عبر ملف service_account.json: {e}")

    st.error("⚠️ لم يتم العثور على اعتمادات Google Sheets! يرجى إضافة [gcp_service_account] داخل Streamlit Cloud Secrets.")
    return None

# =========================================================
# 2. قواعد البيانات والبيانات الأولية (شاملة درجات الرياضيات)
# =========================================================
RAW_EXCEL_STUDENTS = [
    # الصف الأول المتوسط - فصل 101 (مع إضافة وتدقيق درجات الرياضيات)
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 1, 'name': 'بلال عبد الرزاق عيسى العيسى', 'science': 5.0, 'math': 9.0, 'lughati': 5.0, 'english': 4.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 2, 'name': 'جاسر بن عبد الله بن منصور الحارثي', 'science': 4.0, 'math': 0.0, 'lughati': 3.0, 'english': 1.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 3, 'name': 'حسام بن محمد بن علي ال رايان البارقي', 'science': 3.0, 'math': 4.0, 'lughati': 6.0, 'english': 6.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 4, 'name': 'ريان عبد الله جابر الأسمري', 'science': 4.0, 'math': 0.0, 'lughati': 6.0, 'english': 3.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 5, 'name': 'زيد زياد عبد اللطيف أبو قبع', 'science': 6.0, 'math': 7.0, 'lughati': 5.0, 'english': 6.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 6, 'name': 'سامي سعد عباس حمد', 'science': 3.0, 'math': 4.0, 'lughati': 6.0, 'english': 5.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 7, 'name': 'سعد ناصر سعد السيف', 'science': 3.0, 'math': 5.0, 'lughati': 2.0, 'english': 4.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 8, 'name': 'عبد الله بن سليمان بن عبد الله الراجحي', 'science': 0.0, 'math': 5.0, 'lughati': 7.0, 'english': 0.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 9, 'name': 'عبد الله سعد بن محمد العيشان', 'science': 0.0, 'math': 0.0, 'lughati': 7.0, 'english': 0.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 10, 'name': 'علي أحمد علي كريري', 'science': 4.0, 'math': 6.0, 'lughati': 5.0, 'english': 2.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 11, 'name': 'علي سعد علي القحطاني', 'science': 3.0, 'math': 0.0, 'lughati': 3.0, 'english': 4.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 12, 'name': 'عمر عبد الله سعد الجبرين', 'science': 2.0, 'math': 3.0, 'lughati': 1.0, 'english': 4.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 13, 'name': 'مازن إسلام أحمد إبراهيم موسى', 'science': 4.0, 'math': 8.0, 'lughati': 5.0, 'english': 5.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 14, 'name': 'محمد أحمد علي عقيل', 'science': 0.0, 'math': 0.0, 'lughati': 0.0, 'english': 0.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 15, 'name': 'محمد إسلام محمد دراز', 'science': 4.0, 'math': 5.0, 'lughati': 5.0, 'english': 6.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 16, 'name': 'محمد أشرف مسعود أبو خاطر', 'science': 4.0, 'math': 6.0, 'lughati': 5.0, 'english': 6.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 17, 'name': 'محمد نايف فراج الدعجاني', 'science': 0.0, 'math': 0.0, 'lughati': 3.0, 'english': 0.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 101', 'seq': 18, 'name': 'وائل بولعيش', 'science': 0.0, 'math': 4.0, 'lughati': 0.0, 'english': 5.0},

    # الصف الأول المتوسط - فصل 102 (محدث بدرجات الرياضيات)
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 1, 'name': 'إبراهيم بن محمد بن علي الوهيبي', 'science': 3.0, 'math': 0.0, 'lughati': 1.0, 'english': 2.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 2, 'name': 'الوليد ابن خالد بن فهد العتيبي', 'science': 5.0, 'math': 6.0, 'lughati': 6.0, 'english': 9.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 3, 'name': 'باسل محمد فرج الدوسري', 'science': 6.0, 'math': 3.0, 'lughati': 7.0, 'english': 4.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 4, 'name': 'بسام بن عبد الكريم بن عبد الله الحرقان الدوسري', 'science': 4.0, 'math': 4.0, 'lughati': 3.0, 'english': 0.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 5, 'name': 'تركي عبد الله مسفر الدوسري', 'science': 5.0, 'math': 4.0, 'lughati': 5.0, 'english': 4.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 6, 'name': 'تميم فهد عبد العزيز العزاز', 'science': 3.0, 'math': 5.0, 'lughati': 5.0, 'english': 3.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 7, 'name': 'راكان عبد الله يحيى كريري', 'science': 5.0, 'math': 8.0, 'lughati': 6.0, 'english': 6.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 8, 'name': 'ريان عبد الله منصور السبر', 'science': 7.0, 'math': 4.0, 'lughati': 9.0, 'english': 6.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 9, 'name': 'ريان وليد حالق', 'science': 4.0, 'math': 5.0, 'lughati': 3.0, 'english': 0.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 10, 'name': 'سيف عبد الكريم بريك العصيمي', 'science': 3.0, 'math': 6.0, 'lughati': 0.0, 'english': 3.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 11, 'name': 'صالح حسن فتحي سندي', 'science': 0.0, 'math': 6.0, 'lughati': 5.0, 'english': 0.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 12, 'name': 'عبد الرحمن إبراهيم عبد الله الحضيف', 'science': 4.0, 'math': 5.0, 'lughati': 5.0, 'english': 5.0},
    {'grade': 'الصف الأول المتوسط', 'class': 'فصل 102', 'seq': 13, 'name': 'عبد الله صالح حمد الصفيان', 'science': 3.0, 'math': 5.0, 'lughati': 4.0, 'english': 5.0},

    # الصف الثاني المتوسط - فصل 201
    {'grade': 'الصف الثاني المتوسط', 'class': 'فصل 201', 'seq': 1, 'name': 'إبراهيم ياسر إبراهيم الحلوى', 'science': 4.0, 'math': 3.0, 'lughati': 6.0, 'english': 5.0},
    {'grade': 'الصف الثاني المتوسط', 'class': 'فصل 201', 'seq': 2, 'name': 'أحمد سامي بن أحمد العمران', 'science': 3.0, 'math': 2.0, 'lughati': 2.0, 'english': 3.0},

    # الصف الثاني المتوسط - فصل 202
    {'grade': 'الصف الثاني المتوسط', 'class': 'فصل 202', 'seq': 1, 'name': 'أنس خالد المرزوق', 'science': 5.0, 'math': 3.0, 'lughati': 4.0, 'english': 4.0},
    {'grade': 'الصف الثاني المتوسط', 'class': 'فصل 202', 'seq': 2, 'name': 'بندر علي فهد القحطاني', 'science': 4.0, 'math': 2.0, 'lughati': 5.0, 'english': 3.0},

    # الصف الثاني المتوسط - فصل 203
    {'grade': 'الصف الثاني المتوسط', 'class': 'فصل 203', 'seq': 1, 'name': 'ثامر عمر إبراهيم عثمان', 'science': 3.0, 'math': 4.0, 'lughati': 7.0, 'english': 6.0},

    # الصف الثالث المتوسط - فصل 301
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 301', 'seq': 15, 'name': 'فهد عبد الرحمن فهد العتيبي', 'science': 3.0, 'math': 0.0, 'lughati': 5.0, 'english': 0.0},
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 301', 'seq': 16, 'name': 'فيصل بن عبد الرحمن بن عايض العصيمي العتيبي', 'science': 5.0, 'math': 9.0, 'lughati': 0.0, 'english': 6.0},
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 301', 'seq': 17, 'name': 'فيصل محمد صالح الفتوح', 'science': 5.0, 'math': 7.0, 'lughati': 7.0, 'english': 4.0},
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 301', 'seq': 18, 'name': 'محمد سلطان عبد العزيز العيد', 'science': 4.0, 'math': 5.0, 'lughati': 0.0, 'english': 3.0},
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 301', 'seq': 19, 'name': 'محمد مقعد ساير العتيبي', 'science': 5.0, 'math': 6.0, 'lughati': 6.0, 'english': 6.0},

    # الصف الثالث المتوسط - فصل 302
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 302', 'seq': 1, 'name': 'تركي عبد العزيز عبد الله المرزوق', 'science': 4.0, 'math': 0.0, 'lughati': 0.0, 'english': 3.0},
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 302', 'seq': 7, 'name': 'عبد الرحمن محمد صلاح بدر الدين', 'science': 6.0, 'math': 4.0, 'lughati': 6.0, 'english': 6.0},

    # الصف الثالث المتوسط - فصل 303
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 303', 'seq': 1, 'name': 'ثامر وليد بن عبد العزيز الطليحي', 'science': 2.0, 'math': 3.0, 'lughati': 0.0, 'english': 2.0},
    {'grade': 'الصف الثالث المتوسط', 'class': 'فصل 303', 'seq': 2, 'name': 'خالد بن عبد الرؤوف الشنير', 'science': 4.0, 'math': 5.0, 'lughati': 0.0, 'english': 0.0}
]

def init_db(force=False):
    """إنشاء وتعبئة قاعدة البيانات المحلية SQLite لضمان حفظ البيانات بشكل دائم"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            grade TEXT,
            class_name TEXT,
            seq_num INTEGER,
            student_name TEXT,
            science REAL DEFAULT 0.0,
            math REAL DEFAULT 0.0,
            lughati REAL DEFAULT 0.0,
            english REAL DEFAULT 0.0
        )
    """)
    
    c.execute("SELECT COUNT(*) FROM grades")
    row_count = c.fetchone()[0]
    
    if force or row_count < 10:
        c.execute("DELETE FROM grades")
        initial_rows = []
        for rec in RAW_EXCEL_STUDENTS:
            initial_rows.append(("الاختبار التشخيصي الأول", rec["grade"], rec["class"], rec["seq"], rec["name"], rec["science"], rec["math"], rec["lughati"], rec["english"]))
            for t in ["الاختبار التشخيصي الثاني", "الاختبار التشخيصي الثالث", "الاختبار التشخيصي الرابع"]:
                initial_rows.append((t, rec["grade"], rec["class"], rec["seq"], rec["name"], 0.0, 0.0, 0.0, 0.0))
                
        c.executemany("""
            INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_rows)
        conn.commit()
    conn.close()

# تشغيل التهيئة
init_db()

# ---------------------------------------------------------
# دوال التفاعل مع قاعدة البيانات والتخزين الدائم
# ---------------------------------------------------------
def load_class_students(test_name, grade, class_name):
    """جلب طلاب فصل محدد واختبار محدد"""
    conn = sqlite3.connect(DB_FILE)
    clean_t, clean_g, clean_c = test_name.strip(), grade.strip(), class_name.strip()
    
    df = pd.read_sql_query("""
        SELECT id, seq_num AS 'المسلسل', student_name AS 'اسم الطالب', science AS 'علوم', math AS 'رياضيات', lughati AS 'لغتي', english AS 'انجليزي'
        FROM grades
        WHERE TRIM(test_name) = ? AND TRIM(grade) = ? AND TRIM(class_name) = ?
        ORDER BY seq_num ASC
    """, conn, params=[clean_t, clean_g, clean_c])
    
    conn.close()
    return df

def load_all_db_records():
    """جلب كل سجلات قاعدة البيانات"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT test_name, grade, class_name, seq_num, student_name, science, math, lughati, english
        FROM grades
        ORDER BY test_name, grade, class_name, seq_num ASC
    """, conn)
    conn.close()
    return df

def update_student_scores(edited_df):
    """تحديث الحفظ الدائم في SQLite والمزامنة التلقائية مع Google Sheets"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for _, row in edited_df.iterrows():
        c.execute("""
            UPDATE grades
            SET science = ?, math = ?, lughati = ?, english = ?
            WHERE id = ?
        """, (float(row['علوم']), float(row['رياضيات']), float(row['لغتي']), float(row['انجليزي']), int(row['id'])))
    conn.commit()
    conn.close()
    sync_db_to_gsheets()

def save_new_student(test_name, grade, class_name, student_name, science, math, lughati, english):
    """إضافة طالب جديد وحفظه بصفة دائمة"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT MAX(seq_num) FROM grades WHERE TRIM(test_name)=? AND TRIM(grade)=? AND TRIM(class_name)=?
    """, (test_name.strip(), grade.strip(), class_name.strip()))
    max_seq_res = c.fetchone()
    max_seq = max_seq_res[0] if max_seq_res else 0
    next_seq = (max_seq or 0) + 1
    
    c.execute("""
        INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (test_name.strip(), grade.strip(), class_name.strip(), next_seq, student_name, science, math, lughati, english))
    conn.commit()
    conn.close()
    sync_db_to_gsheets()

def export_to_excel_bytes(df):
    """تصدير ملف Excel كـ Bytes"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="النتائج")
    return output.getvalue()

# ---------------------------------------------------------
# دوال المزامنة المزدوجة والمستمرة (Google Sheets ↔ SQLite)
# ---------------------------------------------------------
def sync_db_to_gsheets():
    """رفع ومزامنة البيانات مع Google Sheets بأعمدة اللغة العربية"""
    try:
        ws = get_gsheet_worksheet()
        if ws is None:
            return False, "❌ لم يتم الاتصال بـ Google Sheets."
        
        df_db = load_all_db_records()
        if df_db.empty:
            return False, "⚠️ قاعدة البيانات المحلية خالية من البيانات."

        df_ar = df_db.rename(columns=COLUMN_MAPPING_TO_ARABIC)
        df_ar = df_ar[ARABIC_COLUMNS_ORDER].fillna(0)

        header = ARABIC_COLUMNS_ORDER
        data_rows = df_ar.values.tolist()
        all_values = [header] + data_rows

        ws.clear()
        ws.update("A1", all_values)

        return True, f"✅ تمت المزامنة والرفع بنجاح! تم حفظ ورصد {len(data_rows)} سجلاً بنجاح."
    except Exception as e:
        return False, f"❌ حدث خطأ أثناء المزامنة مع Google Sheets: {str(e)}"

def sync_gsheets_to_db_reverse():
    """سحب البيانات المحدثة من Google Sheets وحفظها في SQLite"""
    try:
        ws = get_gsheet_worksheet()
        if ws is None:
            return False, "❌ لم يتم الاتصال بـ Google Sheets."

        records = ws.get_all_records()
        if not records:
            return False, "⚠️ ورقة Google Sheets فارغة أو لا تحتوي على بيانات."

        df_gsheet = pd.DataFrame(records)

        missing_cols = [col for col in ARABIC_COLUMNS_ORDER if col not in df_gsheet.columns]
        if missing_cols:
            return False, f"❌ الأعمدة التالية مفقودة في Google Sheets: {missing_cols}."

        df_eng = df_gsheet.rename(columns=COLUMN_MAPPING_TO_ENGLISH)

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()

        updated_count = 0
        for _, row in df_eng.iterrows():
            c.execute("""
                UPDATE grades
                SET science = ?, math = ?, lughati = ?, english = ?
                WHERE TRIM(test_name) = ? AND TRIM(grade) = ? AND TRIM(class_name) = ? AND seq_num = ?
            """, (
                float(row.get('science', 0.0)),
                float(row.get('math', 0.0)),
                float(row.get('lughati', 0.0)),
                float(row.get('english', 0.0)),
                str(row.get('test_name', '')).strip(),
                str(row.get('grade', '')).strip(),
                str(row.get('class_name', '')).strip(),
                int(row.get('seq_num', 0))
            ))
            if c.rowcount > 0:
                updated_count += 1

        conn.commit()
        conn.close()

        return True, f"✅ تمت المزامنة العكسية بنجاح! تم تحديث وحفظ {updated_count} سجلاً في قاعدة البيانات المحلية."
    except Exception as e:
        return False, f"❌ حدث خطأ أثناء السحب من Google Sheets: {str(e)}"

# =========================================================
# 3. الهيدر وشريط الأدوات العلوي
# =========================================================
st.markdown("""
<div style="text-align: center; padding: 12px; background: linear-gradient(135deg, #1e3a8a, #3b82f6); color: white; border-radius: 10px;">
    <h1>🎓 نظام رصد الدرجات والرسوم البيانية</h1>
    <p>متوسطة الثغر النموذجية الأهلية - إدارة التحصيل الدراسي والاختبارات التشخيصية</p>
    <div style="font-weight: bold; background: rgba(255,255,255,0.2); display: inline-block; padding: 5px 15px; border-radius: 15px;">
        👑 تصميم وتطوير: محمد سامي السعيد
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-top: 10px; padding: 8px; background-color: #d1fae5; border-right: 5px solid #10b981; border-radius: 5px;">
    ✅ الحفظ دائم وتلقائي (SQLite المحلي ↔ Google Sheets)
</div>
""", unsafe_allow_html=True)

# =========================================================
# 4. القوائم المنسدلة المتسلسلة
# =========================================================
col_t, col_g, col_c = st.columns(3)
with col_t:
    selected_test = st.selectbox("📌 1. اختر الاختبار التشخيصي:", TESTS_LIST, index=0)

grades_map = {
    "الصف الأول المتوسط": ["فصل 101", "فصل 102"],
    "الصف الثاني المتوسط": ["فصل 201", "فصل 202", "فصل 203"],
    "الصف الثالث المتوسط": ["فصل 301", "فصل 302", "فصل 303"]
}

with col_g:
    selected_grade = st.selectbox("🏫 2. اختر الصف الدراسي:", list(grades_map.keys()), index=0)

with col_c:
    selected_class = st.selectbox("📚 3. اختر الفصل:", grades_map[selected_grade], index=0)

# =========================================================
# 5. التبويبات الرئيسية Tabs
# =========================================================
tab_entry, tab_charts, tab_excel, tab_add = st.tabs([
    "📋 رصد درجات الفصل والطباعة",
    "📈 الرسم البياني والمقارنة بين الفصول",
    "🟢 استيراد وتصدير والمزامنة المزدوجة",
    "➕ إضافة طالب جديد"
])

# ---------------------------------------------------------
# التبويب الأول: رصد درجات الفصل والطباعة
# ---------------------------------------------------------
with tab_entry:
    st.subheader(f"📋 سجل درجات الطلاب: ({selected_test}) - {selected_grade} - {selected_class}")
    df_students = load_class_students(selected_test, selected_grade, selected_class)

    if df_students.empty:
        st.warning(f"⚠️ لا توجد بيانات طلاب حالياً لـ ({selected_test}) - {selected_grade} - {selected_class}.")
        if st.button("🔄 استعادة قاعدة بيانات جميع الفصول والطلاب", type="primary"):
            init_db(force=True)
            st.success("تمت استعادة كافة البيانات بنجاح!")
            st.rerun()
    else:
        c_btn1, c_btn2, c_btn3 = st.columns([4, 4, 3])
        with c_btn1:
            show_blank = st.checkbox("📝 عرض وطباعة كشف رصد فارغ (بدون درجات)", value=False)
        with c_btn2:
            table_print_orient = st.radio("📐 اتجاه طباعة التقرير:", ["عمودي (Portrait)", "أفقي (Landscape)"], index=0, horizontal=True)
        with c_btn3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🖨️ طباعة تقرير الفصل (PDF / Print)", type="primary"):
                page_size = "landscape" if "أفقي" in table_print_orient else "portrait"
                st.components.v1.html(f"""
                <style>
                    @media print {{
                        @page {{ size: {page_size}; margin: 10mm; }}
                    }}
                </style>
                <script>setTimeout(function() {{ window.parent.print(); }}, 300);</script>
                """, height=0)

        st.markdown('✏️ **جدول الرصد المنظم والتعديل التفاعلي:**')

        df_display = df_students.copy()
        if show_blank:
            for col in ['علوم', 'رياضيات', 'لغتي', 'انجليزي']:
                df_display[col] = None

        edited_df = st.data_editor(
            df_display[['id', 'المسلسل', 'اسم الطالب', 'علوم', 'رياضيات', 'لغتي', 'انجليزي']],
            column_config={
                "id": None,
                "المسلسل": st.column_config.NumberColumn("م", disabled=True, width="small"),
                "اسم الطالب": st.column_config.TextColumn("اسم الطالب", disabled=True, width="large"),
                "علوم": st.column_config.NumberColumn("علوم (10)", min_value=0.0, max_value=10.0, step=0.5, format="%g"),
                "رياضيات": st.column_config.NumberColumn("رياضيات (10)", min_value=0.0, max_value=10.0, step=0.5, format="%g"),
                "لغتي": st.column_config.NumberColumn("لغتي (10)", min_value=0.0, max_value=10.0, step=0.5, format="%g"),
                "انجليزي": st.column_config.NumberColumn("انجليزي (10)", min_value=0.0, max_value=10.0, step=0.5, format="%g")
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{selected_test}_{selected_grade}_{selected_class}"
        )
        
        if st.button("💾 حفظ التعديلات بصفة دائمة في SQLite + Google Sheets", type="secondary"):
            update_student_scores(edited_df)
            st.success("تم الحفظ الدائم والمزامنة المزدوجة بنجاح!")
            st.rerun()

# ---------------------------------------------------------
# التبويب الثاني: الرسم البياني والمقارنة بين الفصول مع خيار الطباعة
# ---------------------------------------------------------
with tab_charts:
    st.subheader(f"📈 التحليل البياني والمقارنة بين الفصول - {selected_test}")
    
    col_ch_multi, col_ch_orient, col_ch_print = st.columns([4, 4, 3])
    avail_classes = grades_map[selected_grade]
    
    with col_ch_multi:
        selected_classes_compare = st.multiselect("📚 اختر الفصول للمقارنة:", avail_classes, default=avail_classes)
    
    with col_ch_orient:
        chart_print_orient = st.radio("📐 اتجاه طباعة الرسم البياني:", ["أفقي (Landscape)", "عمودي (Portrait)"], index=0, horizontal=True)
    
    with col_ch_print:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🖨️ طباعة الرسم البياني (PDF)", type="primary"):
            chart_page_size = "landscape" if "أفقي" in chart_print_orient else "portrait"
            st.components.v1.html(f"""
            <style>
                @media print {{
                    @page {{ size: {chart_page_size}; margin: 10mm; }}
                }}
            </style>
            <script>setTimeout(function() {{ window.parent.print(); }}, 300);</script>
            """, height=0)

    # جلب بيانات المقارنة ورسم المخطط البياني
    df_all = load_all_db_records()
    df_filtered = df_all[
        (df_all["test_name"] == selected_test) &
        (df_all["grade"] == selected_grade) &
        (df_all["class_name"].isin(selected_classes_compare))
    ]

    if not df_filtered.empty:
        # حساب متوسط الدرجات لكل فصل في المواد الأربع (شاملة الرياضيات)
        df_avg = df_filtered.groupby("class_name")[["science", "math", "lughati", "english"]].mean().reset_index()
        df_avg_melted = df_avg.melt(id_vars=["class_name"], var_name="المادة", value_name="متوسط الدرجة")
        
        # تحويل أسماء المواد إلى العربية للعرض
        subj_map = {"science": "علوم", "math": "رياضيات", "lughati": "لغتي", "english": "انجليزي"}
        df_avg_melted["المادة"] = df_avg_melted["المادة"].map(subj_map)

        fig = px.bar(
            df_avg_melted,
            x="class_name",
            y="متوسط الدرجة",
            color="المادة",
            barmode="group",
            title=f"مقارنة متوسط درجات المواد (شاملة الرياضيات) بين الفصول - {selected_grade}",
            labels={"class_name": "الفصل", "متوسط الدرجة": "متوسط الدرجة (من 10)"},
            text_auto=".1f"
        )
        fig.update_layout(template="plotly_white", font=dict(family="Cairo, Arial", size=14))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ لا توجد بيانات متاحة لعرض الرسم البياني للمقارنة.")

# ---------------------------------------------------------
# التبويب الثالث: التصدير والمزامنة المزدوجة
# ---------------------------------------------------------
with tab_excel:
    st.subheader("🟢 التصدير والمزامنة المزدوجة (SQLite ↔ Google Sheets)")

    st.markdown("### 📊 تحميل نتائج اختبار تشخيصي محدد")
    selected_export_test = st.selectbox(
        "📌 اختر الاختبار التشخيصي المراد تصديره:",
        TESTS_LIST,
        key="export_test_selector"
    )

    df_all_data = load_all_db_records()
    df_selected_test = df_all_data[df_all_data["test_name"] == selected_export_test].copy()

    if not df_selected_test.empty:
        df_selected_test_ar = df_selected_test.rename(columns=COLUMN_MAPPING_TO_ARABIC)
        excel_test_bytes = export_to_excel_bytes(df_selected_test_ar)

        st.download_button(
            label=f"📥 تحميل نتائج ({selected_export_test}) كملف Excel (.xlsx)",
            data=excel_test_bytes,
            file_name=f"نتائج_{selected_export_test}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.warning(f"⚠️ لا توجد نتائج مسجلة لـ ({selected_export_test}) حالياً.")

    st.markdown("<hr>", unsafe_allow_html=True)

    col_exp_box, col_sync_box, col_rev_box = st.columns(3)

    with col_exp_box:
        excel_data = export_to_excel_bytes(df_all_data.rename(columns=COLUMN_MAPPING_TO_ARABIC))
        st.download_button(
            label="📥 تحميل كافة البيانات كملف Excel (.xlsx)",
            data=excel_data,
            file_name="درجات_المواد_الأربع_شامل.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="secondary"
        )

    with col_sync_box:
        if st.button("📤 رفع المزامنة من SQLite إلى Google Sheets", type="secondary"):
            success, msg = sync_db_to_gsheets()
            if success:
                st.success(msg)
            else:
                st.error(msg)

    with col_rev_box:
        if st.button("📥 سحب التعديلات من Google Sheets إلى SQLite", type="secondary"):
            success, msg = sync_gsheets_to_db_reverse()
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

# ---------------------------------------------------------
# التبويب الرابع: إضافة طالب جديد
# ---------------------------------------------------------
with tab_add:
    st.subheader("➕ إضافة طالب جديد وإسناد الدرجات له (حفظ دائم)")
    with st.form("add_student_form"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            add_t = st.selectbox("📌 الاختبار:", TESTS_LIST, key="add_t")
        with col_f2:
            add_g = st.selectbox("🏫 الصف:", list(grades_map.keys()), key="add_g")
        with col_f3:
            add_c = st.selectbox("📚 الفصل:", grades_map[add_g], key="add_c")

        add_s_name = st.text_input("👤 اسم الطالب الرباعي:")

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            add_s = st.number_input("علوم (10)", min_value=0.0, max_value=10.0, step=0.5, value=0.0)
        with col_s2:
            add_m = st.number_input("رياضيات (10)", min_value=0.0, max_value=10.0, step=0.5, value=0.0)
        with col_s3:
            add_l = st.number_input("لغتي (10)", min_value=0.0, max_value=10.0, step=0.5, value=0.0)
        with col_s4:
            add_e = st.number_input("انجليزي (10)", min_value=0.0, max_value=10.0, step=0.5, value=0.0)

        submit_add = st.form_submit_button("💾 حفظ الطالب والدرجات بصفة دائمة")
        if submit_add:
            if not add_s_name.strip():
                st.error("يرجى كتابة اسم الطالب.")
            else:
                save_new_student(add_t, add_g, add_c, add_s_name.strip(), add_s, add_m, add_l, add_e)
                st.success(f"تمت إضافة الطالب ({add_s_name}) وحفظه بنجاح ومزامنة بياناته!")
                st.rerun()
