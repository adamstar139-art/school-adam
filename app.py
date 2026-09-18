import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import io
import os
import gspread
from google.oauth2.service_account import Credentials

### =========================================================
### 0. إعدادات حساب الخدمة والربط بـ Google Sheets عبر st.secrets
### =========================================================
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1XuneQDIfvpqKiuPQ-BcNBfOOm2G4vFBvwIa5F5gV15g/edit?usp=sharing"

def get_gsheet_worksheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 1. المحاولة الأولى: الاستدعاء المباشر من Streamlit Cloud Secrets (الأكثر أماناً وموصى به)
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

    # 2. المحاولة الثانية: ملف service_account.json محلي إذا كان موجوداً
    if os.path.exists("service_account.json"):
        try:
            creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
            client = gspread.authorize(creds)
            return client.open_by_url(SPREADSHEET_URL).sheet1
        except Exception as e:
            st.error(f"❌ فشل الاتصال عبر ملف service_account.json: {e}")

    st.error("⚠️ لم يتم العثور على اعتمادات Google Sheets! يرجى إضافة [gcp_service_account] داخل Streamlit Cloud Secrets.")
    return None

def sync_db_to_gsheets():
    try:
        ws = get_gsheet_worksheet()
        if ws is None:
            return False, "⚠️ تعذر الاتصال بـ Google Sheets. يُرجى التثبت من إعدادات Streamlit Secrets."
        df = load_all_db_records()
        ws.clear()
        ws.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
        return True, "🟢 تم رفع وتصدير البيانات إلى Google Sheets بنجاح!"
    except Exception as e:
        return False, f"❌ تعذرت المزامنة مع Google Sheets: {e}"

def sync_gsheets_to_db_reverse():
    try:
        ws = get_gsheet_worksheet()
        if ws is None:
            return False, "⚠️ تعذر الاتصال بـ Google Sheets. يُرجى التثبت من إعدادات Streamlit Secrets."
        records = ws.get_all_records()
        if not records:
            return False, "⚠️ الجدول في Google Sheets فارغ!"
        df_gs = pd.DataFrame(records)
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM grades")
        
        for _, row in df_gs.iterrows():
            c.execute("""
                INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row.get('الاختبار', '')),
                str(row.get('الصف الدراسي', '')),
                str(row.get('الفصل', '')),
                int(row.get('المسلسل', 0)),
                str(row.get('اسم الطالب', '')),
                float(row.get('علوم', 0.0) or 0.0),
                float(row.get('رياضيات', 0.0) or 0.0),
                float(row.get('لغتي', 0.0) or 0.0),
                float(row.get('انجليزي', 0.0) or 0.0)
            ))
        conn.commit()
        conn.close()
        return True, "🟢 تم سحب التعديلات من Google Sheets بنجاح وتحديث قاعدة البيانات!"
    except Exception as e:
        return False, f"❌ تعذر سحب البيانات من Google Sheets: {e}"

def export_to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='الدرجات')
    return output.getvalue()

def save_new_student(test_name, grade_name, class_name, student_name, science, math, lughati, english):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT COALESCE(MAX(seq_num), 0) + 1 FROM grades
        WHERE grade = ? AND class_name = ?
    """, (grade_name, class_name))
    next_seq = c.fetchone()[0]
    
    c.execute("""
        INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (test_name, grade_name, class_name, next_seq, student_name, science, math, lughati, english))
    conn.commit()
    conn.close()

### =========================================================
### 1. تهيئة الصفحة والنمط Visual Theme & Page Config
### =========================================================
st.set_page_config(
    page_title="نظام رصد الدرجات والرسوم البيانية - متوسطة الثغر النموذجية الأهلية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def clean_html(html_str):
    if not html_str:
        return ""
    lines = [line.strip() for line in html_str.strip().splitlines()]
    return "\n".join([line for line in lines if line])

css_code = """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Cairo', sans-serif;
        direction: rtl;
    }
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 26px;
        font-weight: 800;
    }
    .main-header p {
        margin: 5px 0 0 0;
        opacity: 0.9;
        font-size: 14px;
    }
    .designer-banner {
        background: rgba(255, 255, 255, 0.15);
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        margin-top: 10px;
        font-size: 13px;
        font-weight: 600;
    }
    .top-toolbar {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .save-indicator {
        color: #16a34a;
        font-size: 13px;
        font-weight: 600;
    }
</style>
"""
st.markdown(clean_html(css_code), unsafe_allow_html=True)

### =========================================================
### 2. البيانات وقواعد البيانات
### =========================================================
RAW_EXCEL_STUDENTS = [
    # الصف الأول المتوسط - فصل 101
    {'class': 'فصل 101', 'english': 4.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 9.0, 'name': 'بلال عبد الرزاق عيسى العيسى', 'science': 5.0, 'seq': 1},
    {'class': 'فصل 101', 'english': 1.0, 'grade': 'الصف الأول المتوسط', 'lughati': 3.0, 'math': 0.0, 'name': 'جاسر بن عبد الله بن منصور الحارثي', 'science': 4.0, 'seq': 2},
    {'class': 'فصل 101', 'english': 6.0, 'grade': 'الصف الأول المتوسط', 'lughati': 6.0, 'math': 4.0, 'name': 'حسام بن محمد بن علي ال رايان البارقي', 'science': 3.0, 'seq': 3},
    {'class': 'فصل 101', 'english': 3.0, 'grade': 'الصف الأول المتوسط', 'lughati': 6.0, 'math': 0.0, 'name': 'ريان عبد الله جابر الأسمري', 'science': 4.0, 'seq': 4},
    {'class': 'فصل 101', 'english': 6.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 7.0, 'name': 'زيد زياد عبد اللطيف أبو قبع', 'science': 6.0, 'seq': 5},
    {'class': 'فصل 101', 'english': 5.0, 'grade': 'الصف الأول المتوسط', 'lughati': 6.0, 'math': 4.0, 'name': 'سامي سعد عباس حمد', 'science': 3.0, 'seq': 6},
    {'class': 'فصل 101', 'english': 4.0, 'grade': 'الصف الأول المتوسط', 'lughati': 2.0, 'math': 5.0, 'name': 'سعد ناصر سعد السيف', 'science': 3.0, 'seq': 7},
    {'class': 'فصل 101', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 7.0, 'math': 5.0, 'name': 'عبد الله بن سليمان بن عبد الله الراجحي', 'science': 0.0, 'seq': 8},
    {'class': 'فصل 101', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 7.0, 'math': 0.0, 'name': 'عبد الله سعد بن محمد العيشان', 'science': 0.0, 'seq': 9},
    {'class': 'فصل 101', 'english': 2.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 6.0, 'name': 'علي أحمد علي كريري', 'science': 4.0, 'seq': 10},
    {'class': 'فصل 101', 'english': 4.0, 'grade': 'الصف الأول المتوسط', 'lughati': 3.0, 'math': 0.0, 'name': 'علي سعد علي القحطاني', 'science': 3.0, 'seq': 11},
    {'class': 'فصل 101', 'english': 4.0, 'grade': 'الصف الأول المتوسط', 'lughati': 1.0, 'math': 3.0, 'name': 'عمر عبد الله سعد الجبرين', 'science': 2.0, 'seq': 12},
    {'class': 'فصل 101', 'english': 5.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 8.0, 'name': 'مازن إسلام أحمد إبراهيم موسى', 'science': 4.0, 'seq': 13},
    {'class': 'فصل 101', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'محمد أحمد علي عقيل', 'science': 0.0, 'seq': 14},
    {'class': 'فصل 101', 'english': 6.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 8.0, 'name': 'محمد إسلام محمد دراز', 'science': 4.0, 'seq': 15},
    {'class': 'فصل 101', 'english': 6.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 6.0, 'name': 'محمد أشرف مسعود أبو خاطر', 'science': 4.0, 'seq': 16},
    {'class': 'فصل 101', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 3.0, 'math': 3.0, 'name': 'محمد نايف فراج الدعجاني', 'science': 0.0, 'seq': 17},
    {'class': 'فصل 101', 'english': 5.0, 'grade': 'الصف الأول المتوسط', 'lughati': 0.0, 'math': 9.0, 'name': 'وائل بولعيش', 'science': 0.0, 'seq': 18},

    # الصف الأول المتوسط - فصل 102
    {'class': 'فصل 102', 'english': 2.0, 'grade': 'الصف الأول المتوسط', 'lughati': 1.0, 'math': 0.0, 'name': 'إبراهيم بن محمد بن علي الوهيبي', 'science': 3.0, 'seq': 1},
    {'class': 'فصل 102', 'english': 9.0, 'grade': 'الصف الأول المتوسط', 'lughati': 6.0, 'math': 6.0, 'name': 'الوليد ابن خالد بن فهد العتيبي', 'science': 5.0, 'seq': 2},
    {'class': 'فصل 102', 'english': 4.0, 'grade': 'الصف الأول المتوسط', 'lughati': 7.0, 'math': 3.0, 'name': 'باسل محمد فرج الدوسري', 'science': 6.0, 'seq': 3},
    {'class': 'فصل 102', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 3.0, 'math': 4.0, 'name': 'بسام بن عبد الكريم بن عبد الله الحرقان الدوسري', 'science': 4.0, 'seq': 4},
    {'class': 'فصل 102', 'english': 4.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 4.0, 'name': 'تركي عبد الله مسفر الدوسري', 'science': 5.0, 'seq': 5},
    {'class': 'فصل 102', 'english': 3.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 5.0, 'name': 'تميم فهد عبد العزيز العزاز', 'science': 3.0, 'seq': 6},
    {'class': 'فصل 102', 'english': 6.0, 'grade': 'الصف الأول المتوسط', 'lughati': 6.0, 'math': 8.0, 'name': 'راكان عبد الله يحيى كريري', 'science': 5.0, 'seq': 7},
    {'class': 'فصل 102', 'english': 6.0, 'grade': 'الصف الأول المتوسط', 'lughati': 9.0, 'math': 4.0, 'name': 'ريان عبد الله منصور السبر', 'science': 7.0, 'seq': 8},
    {'class': 'فصل 102', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 3.0, 'math': 5.0, 'name': 'ريان وليد حلاق', 'science': 4.0, 'seq': 9},
    {'class': 'فصل 102', 'english': 3.0, 'grade': 'الصف الأول المتوسط', 'lughati': 0.0, 'math': 6.0, 'name': 'سيف عبد الكريم بريك العصيمي', 'science': 3.0, 'seq': 10},
    {'class': 'فصل 102', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 6.0, 'name': 'صالح حسن فتحي سندي', 'science': 0.0, 'seq': 11},
    {'class': 'فصل 102', 'english': 5.0, 'grade': 'الصف الأول المتوسط', 'lughati': 5.0, 'math': 5.0, 'name': 'عبد الرحمن إبراهيم عبد الله الحضيف', 'science': 4.0, 'seq': 12},
    {'class': 'فصل 102', 'english': 5.0, 'grade': 'الصف الأول المتوسط', 'lughati': 4.0, 'math': 5.0, 'name': 'عبد الله صالح حمد الصفيان', 'science': 3.0, 'seq': 13},
    {'class': 'فصل 102', 'english': 7.0, 'grade': 'الصف الأول المتوسط', 'lughati': 4.0, 'math': 4.0, 'name': 'فهد ابن أحمد بن فهد العثمان', 'science': 4.0, 'seq': 14},
    {'class': 'فصل 102', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 0.0, 'math': 4.0, 'name': 'فهد عويض ثعيل المطيري', 'science': 0.0, 'seq': 15},
    {'class': 'فصل 102', 'english': 3.0, 'grade': 'الصف الأول المتوسط', 'lughati': 4.0, 'math': 2.0, 'name': 'فهد نايف فهد الحسينان', 'science': 2.0, 'seq': 16},
    {'class': 'فصل 102', 'english': 0.0, 'grade': 'الصف الأول المتوسط', 'lughati': 0.0, 'math': 3.0, 'name': 'فيصل موينع عبد الله بن موينع', 'science': 0.0, 'seq': 17},
    {'class': 'فصل 102', 'english': 6.0, 'grade': 'الصف الأول المتوسط', 'lughati': 6.0, 'math': 3.0, 'name': 'فيصل ناصر سيف العريفي', 'science': 6.0, 'seq': 18},
    {'class': 'فصل 102', 'english': 7.0, 'grade': 'الصف الأول المتوسط', 'lughati': 3.0, 'math': 5.0, 'name': 'مشاري عثمان سعد ناصر السعد', 'science': 3.0, 'seq': 19},
    {'class': 'فصل 102', 'english': 5.0, 'grade': 'الصف الأول المتوسط', 'lughati': 6.0, 'math': 3.0, 'name': 'يزن محمد علي اليحيى', 'science': 3.0, 'seq': 20},
    {'class': 'فصل 102', 'english': 4.0, 'grade': 'الصف الأول المتوسط', 'lughati': 2.0, 'math': 3.0, 'name': 'يوسف محمد عبد الله الدوسري', 'science': 4.0, 'seq': 21},

    # الصف الثاني المتوسط - فصل 202
    {'class': 'فصل 202', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 4.0, 'math': 3.0, 'name': 'أنس خالد المرزوق', 'science': 5.0, 'seq': 1},
    {'class': 'فصل 202', 'english': 3.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 2.0, 'name': 'بندر علي فهد القحطاني', 'science': 4.0, 'seq': 2},
    {'class': 'فصل 202', 'english': 5.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 6.0, 'math': 4.0, 'name': 'حسن محمد حسن العمري', 'science': 3.0, 'seq': 3},
    {'class': 'فصل 202', 'english': 6.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 5.0, 'name': 'خالد سعد الدوسري', 'science': 6.0, 'seq': 4},
    {'class': 'فصل 202', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 4.0, 'math': 3.0, 'name': 'راشد فهد ناصر العريفي', 'science': 4.0, 'seq': 5},
    {'class': 'فصل 202', 'english': 5.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 6.0, 'math': 4.0, 'name': 'سعد عبد الله العتيبي', 'science': 5.0, 'seq': 6},
    {'class': 'فصل 202', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 3.0, 'name': 'سعود عبدالعزيز الشمري', 'science': 4.0, 'seq': 7},
    {'class': 'فصل 202', 'english': 3.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 4.0, 'math': 2.0, 'name': 'سلطان ناصر السبيعي', 'science': 3.0, 'seq': 8},
    {'class': 'فصل 202', 'english': 6.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 7.0, 'math': 5.0, 'name': 'صالح فهد الميموني', 'science': 6.0, 'seq': 9},
    {'class': 'فصل 202', 'english': 5.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 4.0, 'name': 'عبد الرحمن علي الشهري', 'science': 5.0, 'seq': 10},
    {'class': 'فصل 202', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 4.0, 'math': 3.0, 'name': 'عبد العزيز محمد الحارثي', 'science': 4.0, 'seq': 11},
    {'class': 'فصل 202', 'english': 7.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 6.0, 'math': 5.0, 'name': 'عبد الله خالد المطيري', 'science': 6.0, 'seq': 12},
    {'class': 'فصل 202', 'english': 5.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 4.0, 'name': 'علي حسين الزهراني', 'science': 5.0, 'seq': 13},
    {'class': 'فصل 202', 'english': 3.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 4.0, 'math': 3.0, 'name': 'عمر سعد القحطاني', 'science': 3.0, 'seq': 14},
    {'class': 'فصل 202', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 3.0, 'math': 2.0, 'name': 'فهد ناصر الدوسري', 'science': 4.0, 'seq': 15},
    {'class': 'فصل 202', 'english': 6.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 4.0, 'name': 'فيصل عبد الله العريفي', 'science': 5.0, 'seq': 16},
    {'class': 'فصل 202', 'english': 5.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 4.0, 'math': 3.0, 'name': 'محمد بن سعيد القحطاني', 'science': 4.0, 'seq': 17},
    {'class': 'فصل 202', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 4.0, 'name': 'مشاري فهد الحربي', 'science': 5.0, 'seq': 18},
    {'class': 'فصل 202', 'english': 0.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 3.0, 'math': 2.0, 'name': 'نايف بن بندر بن خلفان العلوي', 'science': 0.0, 'seq': 19},
    {'class': 'فصل 202', 'english': 5.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 3.0, 'name': 'نواف عبد العزيز المرزوق', 'science': 6.0, 'seq': 20},
    {'class': 'فصل 202', 'english': 1.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 2.0, 'math': 2.0, 'name': 'هادي سلطان هادي القحطاني', 'science': 1.0, 'seq': 21},
    {'class': 'فصل 202', 'english': 0.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 4.0, 'math': 0.0, 'name': 'يزيد بن حسين بن متعب بن محمد كعكم', 'science': 0.0, 'seq': 22},

    # الصف الثاني المتوسط - فصل 203
    {'class': 'فصل 203', 'english': 6.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 7.0, 'math': 4.0, 'name': 'ثامر عمر إبراهيم عثمان', 'science': 3.0, 'seq': 1},
    {'class': 'فصل 203', 'english': 3.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 2.0, 'name': 'جهاد فارس عبد القادر حتاوي', 'science': 2.0, 'seq': 2},
    {'class': 'فصل 203', 'english': 0.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'خالد محمد عبد الكريم الخفاجي', 'science': 4.0, 'seq': 3},
    {'class': 'فصل 203', 'english': 3.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 2.0, 'name': 'سعد ابن مسفر بن سعد القحطاني', 'science': 5.0, 'seq': 4},
    {'class': 'فصل 203', 'english': 2.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'سعود بن عبد الله بن سعود السحامي', 'science': 4.0, 'seq': 5},
    {'class': 'فصل 203', 'english': 8.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 6.0, 'math': 6.0, 'name': 'سعود ناصر سنيف العريفي', 'science': 4.0, 'seq': 6},
    {'class': 'فصل 203', 'english': 0.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 2.0, 'name': 'سعيد محمد باوزير', 'science': 0.0, 'seq': 7},
    {'class': 'فصل 203', 'english': 6.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 7.0, 'math': 3.0, 'name': 'طلال بن فهد بن عطيه بالحكم الزهراني', 'science': 7.0, 'seq': 8},
    {'class': 'فصل 203', 'english': 0.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 5.0, 'name': 'عبد الرحمن أحمد جاسم الحمدي', 'science': 4.0, 'seq': 9},
    {'class': 'فصل 203', 'english': 3.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 2.0, 'name': 'عبد العزيز ماجد راشد الزير', 'science': 5.0, 'seq': 10},
    {'class': 'فصل 203', 'english': 3.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 1.0, 'name': 'عبد العزيز وليد ناصر بن سعران', 'science': 4.0, 'seq': 11},
    {'class': 'فصل 203', 'english': 2.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 2.0, 'name': 'عبد الله بن بندر بن فهد المفيجل', 'science': 5.0, 'seq': 12},
    {'class': 'فصل 203', 'english': 9.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 7.0, 'math': 8.0, 'name': 'عبد المجيد بن محمد بن مسعود آل عايض القحطاني', 'science': 4.0, 'seq': 13},
    {'class': 'فصل 203', 'english': 6.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 5.0, 'name': 'عز الدين أحمد محمد سعد', 'science': 3.0, 'seq': 14},
    {'class': 'فصل 203', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 5.0, 'math': 2.0, 'name': 'عزام خالد شهوب بن شهوب', 'science': 4.0, 'seq': 15},
    {'class': 'فصل 203', 'english': 0.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'عزام فهد أحمد صلوي', 'science': 2.0, 'seq': 16},
    {'class': 'فصل 203', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 5.0, 'name': 'عمر وليد ياسين درويش علي', 'science': 4.0, 'seq': 17},
    {'class': 'فصل 203', 'english': 3.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 3.0, 'name': 'فارس ابن محمد بن سالم الحربي', 'science': 3.0, 'seq': 18},
    {'class': 'فصل 203', 'english': 0.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 4.0, 'math': 3.0, 'name': 'محمد بن علي محسن العثيميني', 'science': 1.0, 'seq': 19},
    {'class': 'فصل 203', 'english': 4.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 6.0, 'math': 0.0, 'name': 'وائل بن عبد الله بن عامر الغامدي', 'science': 1.0, 'seq': 20},
    {'class': 'فصل 203', 'english': 0.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'يزيد بن حمد القحطاني', 'science': 2.0, 'seq': 21},
    {'class': 'فصل 203', 'english': 7.0, 'grade': 'الصف الثاني المتوسط', 'lughati': 6.0, 'math': 6.0, 'name': 'يوسف عايد عواد البلوي', 'science': 8.0, 'seq': 22},

    # الصف الثالث المتوسط - فصل 301
    {'class': 'فصل 301', 'english': 2.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 3.0, 'name': 'أصيل ناصر بن محمد مذكور', 'science': 3.0, 'seq': 1},
    {'class': 'فصل 301', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'خالد محمد مسعف معافا', 'science': 0.0, 'seq': 2},
    {'class': 'فصل 301', 'english': 8.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'راشد سعيد راشد عبد السلام', 'science': 4.0, 'seq': 3},
    {'class': 'فصل 301', 'english': 3.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 6.0, 'math': 7.0, 'name': 'راكان بن عبد الله بن سالم اليافعي', 'science': 4.0, 'seq': 4},
    {'class': 'فصل 301', 'english': 1.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'زياد أحمد بن علي اللحيد', 'science': 3.0, 'seq': 5},
    {'class': 'فصل 301', 'english': 3.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 5.0, 'name': 'سطام محمد سعود الدوسري', 'science': 5.0, 'seq': 6},
    {'class': 'فصل 301', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 6.0, 'math': 4.0, 'name': 'سلطان أحمد صالح الفتوح', 'science': 6.0, 'seq': 7},
    {'class': 'فصل 301', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'عبد العزيز عبد الله شراز المالكي', 'science': 5.0, 'seq': 8},
    {'class': 'فصل 301', 'english': 5.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 7.0, 'math': 6.0, 'name': 'عبد العزيز عبد الله عايض الأسمري', 'science': 5.0, 'seq': 9},
    {'class': 'فصل 301', 'english': 2.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 4.0, 'math': 4.0, 'name': 'عبد الله عبيد عبد الله العتيبي', 'science': 2.0, 'seq': 10},
    {'class': 'فصل 301', 'english': 0.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'عبد الله فهد جلوي سالم الشرعي', 'science': 0.0, 'seq': 11},
    {'class': 'فصل 301', 'english': 0.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'علي إبراهيم علي الأسمري', 'science': 0.0, 'seq': 12},
    {'class': 'فصل 301', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 7.0, 'name': 'عماد الدين إسلام محمد دراز', 'science': 0.0, 'seq': 13},
    {'class': 'فصل 301', 'english': 0.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 2.0, 'name': 'عمر فهد محمد السقامي', 'science': 4.0, 'seq': 14},
    {'class': 'فصل 301', 'english': 0.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 5.0, 'math': 0.0, 'name': 'فهد عبد الرحمن فهد العتيبي', 'science': 3.0, 'seq': 15},
    {'class': 'فصل 301', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 9.0, 'name': 'فيصل بن عبد الرحمن بن عايض العصيمي العتيبي', 'science': 5.0, 'seq': 16},
    {'class': 'فصل 301', 'english': 4.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 7.0, 'math': 7.0, 'name': 'فيصل محمد صالح الفتوح', 'science': 5.0, 'seq': 17},
    {'class': 'فصل 301', 'english': 3.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 5.0, 'name': 'محمد سلطان عبد العزيز العيد', 'science': 4.0, 'seq': 18},
    {'class': 'فصل 301', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 6.0, 'math': 6.0, 'name': 'محمد مقعد ساير العتيبي', 'science': 5.0, 'seq': 19},
    {'class': 'فصل 301', 'english': 3.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 4.0, 'name': 'مشاري إبراهيم عبد اللطيف المغربي', 'science': 0.0, 'seq': 20},
    {'class': 'فصل 301', 'english': 4.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 6.0, 'name': 'مشاري علي موسى عقيلي', 'science': 4.0, 'seq': 21},
    {'class': 'فصل 301', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 7.0, 'math': 4.0, 'name': 'مهند عبد الله فهد الزكري', 'science': 6.0, 'seq': 22},
    {'class': 'فصل 301', 'english': 5.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 5.0, 'math': 6.0, 'name': 'نواف وليد حمد الشعلان', 'science': 5.0, 'seq': 23},
    {'class': 'فصل 301', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'يوسف نايف مقعد العتيبي', 'science': 5.0, 'seq': 24},

    # الصف الثالث المتوسط - فصل 302 / 303
    {'class': 'فصل 302', 'english': 3.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'تركي عبد العزيز عبد الله المرزوق', 'science': 4.0, 'seq': 1},
    {'class': 'فصل 302', 'english': 3.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'تركي عثمان عبد العزيز العثمان', 'science': 4.0, 'seq': 2},
    {'class': 'فصل 302', 'english': 2.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'راشد أحمد فهد آل سعيد', 'science': 0.0, 'seq': 3},
    {'class': 'فصل 302', 'english': 2.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 4.0, 'math': 3.0, 'name': 'راكان إبراهيم محمد ديوان', 'science': 4.0, 'seq': 4},
    {'class': 'فصل 302', 'english': 0.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'ريان ناصر عبد الرحمن المرشود', 'science': 4.0, 'seq': 5},
    {'class': 'فصل 302', 'english': 0.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'صالح بن ممدوح الجويعي', 'science': 3.0, 'seq': 6},
    {'class': 'فصل 302', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 6.0, 'math': 4.0, 'name': 'عبد الرحمن محمد صلاح بدر الدين', 'science': 6.0, 'seq': 7},
    {'class': 'فصل 302', 'english': 5.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 6.0, 'math': 4.0, 'name': 'عبد العزيز تركي عبد العزيز اللهيم', 'science': 2.0, 'seq': 8},
    {'class': 'فصل 302', 'english': 0.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 6.0, 'name': 'عبد العزيز عبد المحسن بن بديع', 'science': 0.0, 'seq': 9},
    {'class': 'فصل 302', 'english': 4.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 7.0, 'math': 7.0, 'name': 'عبد الرحمن خالد محمد سعيد', 'science': 4.0, 'seq': 10},
    {'class': 'فصل 303', 'english': 7.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 6.0, 'name': 'عبد الله تركي عبد الله الأحمد', 'science': 4.0, 'seq': 11},
    {'class': 'فصل 303', 'english': 6.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 7.0, 'math': 7.0, 'name': 'عبد الله عبد الرحمن النجراني', 'science': 3.0, 'seq': 12},
    {'class': 'فصل 303', 'english': 7.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 3.0, 'math': 4.0, 'name': 'علي بن خالد بن علي العجيري', 'science': 2.0, 'seq': 13},
    {'class': 'فصل 303', 'english': 10.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 7.0, 'math': 7.0, 'name': 'علي عبد الله علي آل حمود', 'science': 6.0, 'seq': 14},
    {'class': 'فصل 303', 'english': 2.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 6.0, 'math': 2.0, 'name': 'فهد بن خالد بن فهد الزيد', 'science': 3.0, 'seq': 15},
    {'class': 'فصل 303', 'english': 2.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 4.0, 'name': 'فيصل عبد الرحمن عزيز القحطاني', 'science': 3.0, 'seq': 16},
    {'class': 'فصل 303', 'english': 7.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'ماجد فهد عبد العزيز الكثيري', 'science': 1.0, 'seq': 17},
    {'class': 'فصل 303', 'english': 5.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 8.0, 'math': 4.0, 'name': 'مازن خالد عبد ربه الزهراني', 'science': 4.0, 'seq': 18},
    {'class': 'فصل 303', 'english': 0.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 0.0, 'name': 'متعب مطر جمعان الدوسري', 'science': 0.0, 'seq': 19},
    {'class': 'فصل 303', 'english': 9.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 6.0, 'math': 0.0, 'name': 'نواف فهد بن ناصر القحطاني', 'science': 8.0, 'seq': 20},
    {'class': 'فصل 303', 'english': 4.0, 'grade': 'الصف الثالث المتوسط', 'lughati': 0.0, 'math': 6.0, 'name': 'يوسف عبد الله عوض العتيبي', 'science': 3.0, 'seq': 21}
]

TESTS_LIST = ["الاختبار التشخيصي الأول", "الاختبار التشخيصي الثاني", "الاختبار التشخيصي الثالث", "الاختبار التشخيصي الرابع"]
DB_FILE = "student_grades_v12.db"

def init_db(force=False):
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

def load_all_db_records():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT 
            id AS 'المعرف',
            test_name AS 'الاختبار',
            grade AS 'الصف الدراسي',
            class_name AS 'الفصل',
            seq_num AS 'المسلسل',
            student_name AS 'اسم الطالب',
            science AS 'علوم',
            math AS 'رياضيات',
            lughati AS 'لغتي',
            english AS 'انجليزي'
        FROM grades
    """, conn)
    conn.close()
    return df

def load_class_students(test_name, grade_name, class_name):
    conn = sqlite3.connect(DB_FILE)
    clean_t = str(test_name).strip()
    clean_g = str(grade_name).strip()
    clean_c = str(class_name).strip()
    df = pd.read_sql_query("""
        SELECT 
            id AS 'المعرف',
            seq_num AS 'المسلسل',
            student_name AS 'اسم الطالب',
            science AS 'علوم',
            math AS 'رياضيات',
            lughati AS 'لغتي',
            english AS 'انجليزي'
        FROM grades
        WHERE test_name = ? AND grade = ? AND class_name = ?
        ORDER BY seq_num ASC
    """, conn, params=[clean_t, clean_g, clean_c])
    conn.close()
    return df

init_db()

### =========================================================
### 3. الهيدر وشريط الأدوات العلوي Main Header
### =========================================================
header_html = """<div class="main-header" style="text-align: center;">
    <h1><i class="fa-solid fa-graduation-cap"></i> نظام رصد الدرجات والرسوم البيانية</h1>
    <p>متوسطة الثغر النموذجية الأهلية - إدارة التحصيل الدراسي والاختبارات التشخيصية</p>
    <div class="designer-banner">
        <i class="fa-solid fa-crown designer-icon"></i>
        <span class="designer-text">تصميم وتطوير: محمد سامي السعيد</span>
    </div>
</div>"""
st.markdown(clean_html(header_html), unsafe_allow_html=True)

toolbar_html = """<div class="top-toolbar">
    <div class="save-indicator">
        <i class="fa-solid fa-circle-check"></i> تم التزامن والحفظ الفوري دائمياً (SQLite المحلي ↔ Google Sheets)
    </div>
</div>"""
st.markdown(clean_html(toolbar_html), unsafe_allow_html=True)

### =========================================================
### 4. القوائم المنسدلة المتسلسلة
### =========================================================
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

### =========================================================
### 5. التبويبات الرئيسية Tabs
### =========================================================
tab_entry, tab_charts, tab_excel, tab_add = st.tabs([
    "📋 رصد درجات الفصل والطباعة",
    "📈 الرسم البياني والمقارنة بين الفصول",
    "🟢 استيراد وتصدير والمزامنة المزدوجة",
    "➕ إضافة طالب جديد"
])

### ---------------------------------------------------------
### التبويب الأول: رصد درجات الفصل والطباعة
### ---------------------------------------------------------
with tab_entry:
    st.subheader(f"📋 سجل درجات الطلاب: ({selected_test}) - {selected_grade} - {selected_class}")
    df_students = load_class_students(selected_test, selected_grade, selected_class)
    
    if not df_students.empty:
        edited_df = st.data_editor(
            df_students,
            column_config={
                "المعرف": None,
                "المسلسل": st.column_config.NumberColumn("المسلسل", disabled=True, width="small"),
                "اسم الطالب": st.column_config.TextColumn("اسم الطالب", disabled=True, width="large"),
                "علوم": st.column_config.NumberColumn("علوم (من 10)", min_value=0.0, max_value=10.0, step=0.5),
                "رياضيات": st.column_config.NumberColumn("رياضيات (من 10)", min_value=0.0, max_value=10.0, step=0.5),
                "لغتي": st.column_config.NumberColumn("لغتي (من 10)", min_value=0.0, max_value=10.0, step=0.5),
                "انجليزي": st.column_config.NumberColumn("انجليزي (من 10)", min_value=0.0, max_value=10.0, step=0.5),
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{selected_test}_{selected_grade}_{selected_class}"
        )
        
        if st.button("💾 حفظ التعديلات المباشرة", type="primary"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            for _, row in edited_df.iterrows():
                c.execute("""
                    UPDATE grades
                    SET science = ?, math = ?, lughati = ?, english = ?
                    WHERE id = ?
                """, (row['علوم'], row['رياضيات'], row['لغتي'], row['انجليزي'], row['المعرف']))
            conn.commit()
            conn.close()
            st.success("🟢 تم حفظ التعديلات في قاعدة البيانات المحلية المباشرة!")

### ---------------------------------------------------------
### التبويب الثاني: الرسم البياني والمقارنة
### ---------------------------------------------------------
with tab_charts:
    st.subheader(f"📈 التحليل البياني والمقارنة بين الفصول - {selected_test}")
    col_ch_multi, col_ch_orient, col_ch_print = st.columns([4, 4, 3])
    
    with col_ch_multi:
        avail_classes = grades_map[selected_grade]
        selected_classes_compare = st.multiselect("📚 اختر الفصول للمقارنة:", avail_classes, default=avail_classes)
        
    with col_ch_orient:
        chart_print_orient = st.radio("📐 اتجاه طباعة الرسم البياني:", ["أفقي (Landscape)", "عمودي / عرضي (Portrait)"], index=0, horizontal=True)
        
    with col_ch_print:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🖨️ طباعة الرسم البياني (PDF)", type="primary"):
            st.components.v1.html("""<script>setTimeout(function() { window.parent.print(); }, 300);</script>""", height=0)

    # تطبيق الاتجاه المختار للرسم البياني عند الطباعة وتفعيله في إعدادات الطابعة
    if "أفقي" in chart_print_orient:
        st.markdown("""<style>
            @media print {
                @page {
                    size: A4 landscape !important;
                    margin: 8mm !important;
                }
                header, footer, [data-testid="stHeader"], [data-testid="stSidebar"], .top-toolbar, .main-header, button, .stButton, [data-testid="stTabs"] > div:first-child {
                    display: none !important;
                }
                body, .stApp, .main, .block-container {
                    background: white !important;
                    color: black !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    overflow: visible !important;
                }
                div[data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container, .svg-container {
                    width: 100% !important;
                    height: 85vh !important;
                    max-height: 180mm !important;
                    page-break-inside: avoid !important;
                    visibility: visible !important;
                }
            }
        </style>""", unsafe_allow_html=True)
    else:
        st.markdown("""<style>
            @media print {
                @page {
                    size: A4 portrait !important;
                    margin: 8mm !important;
                }
                header, footer, [data-testid="stHeader"], [data-testid="stSidebar"], .top-toolbar, .main-header, button, .stButton, [data-testid="stTabs"] > div:first-child {
                    display: none !important;
                }
                body, .stApp, .main, .block-container {
                    background: white !important;
                    color: black !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    overflow: visible !important;
                }
                div[data-testid="stPlotlyChart"], .js-plotly-plot, .plot-container, .svg-container {
                    width: 100% !important;
                    height: 65vh !important;
                    max-height: 250mm !important;
                    page-break-inside: avoid !important;
                    visibility: visible !important;
                }
            }
        </style>""", unsafe_allow_html=True)

    chart_shape = st.selectbox("شكل الرسم البياني للمقارنة:", ["أعمدة بيانية متجاورة (Grouped Bar Chart)", "منحنى بياني متعدد (Multi-Line Chart)", "رادار الفصول (Radar Chart)"])

    if not selected_classes_compare:
        st.warning("يرجى اختيار فصل واحد على الأقل للمقارنة.")
    else:
        conn = sqlite3.connect(DB_FILE)
        placeholders = ', '.join(['?'] * len(selected_classes_compare))
        query = f"""
            SELECT class_name, AVG(science) AS 'علوم', AVG(math) AS 'رياضيات', AVG(lughati) AS 'لغتي', AVG(english) AS 'انجليزي'
            FROM grades
            WHERE test_name = ? AND grade = ? AND class_name IN ({placeholders})
            GROUP BY class_name
        """
        params = [selected_test, selected_grade] + selected_classes_compare
        df_comp = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df_comp.empty:
            df_comp[['علوم', 'رياضيات', 'لغتي', 'انجليزي']] = df_comp[['علوم', 'رياضيات', 'لغتي', 'انجليزي']].round(2)
            df_melted = df_comp.melt(id_vars=['class_name'], var_name='المادة', value_name='متوسط الدرجة')

            if "أعمدة" in chart_shape:
                fig_comp = px.bar(
                    df_melted, x='class_name', y='متوسط الدرجة', color='المادة', barmode='group',
                    text='متوسط الدرجة',
                    title=f"مقارنة متوسط درجات المواد بين فصول {selected_grade}",
                    color_discrete_sequence=['#2563eb', '#ef4444', '#16a34a', '#6b7280']
                )
                fig_comp.update_traces(textposition='outside')
            elif "منحنى" in chart_shape:
                fig_comp = px.line(
                    df_melted, x='class_name', y='متوسط الدرجة', color='المادة', markers=True,
                    title=f"منحنى مقارنة أداء المواد بين فصول {selected_grade}",
                    color_discrete_sequence=['#2563eb', '#ef4444', '#16a34a', '#6b7280']
                )
            else:
                fig_comp = go.Figure()
                for c_name in selected_classes_compare:
                    c_data = df_melted[df_melted['class_name'] == c_name]
                    fig_comp.add_trace(go.Scatterpolar(r=c_data['متوسط الدرجة'], theta=c_data['المادة'], fill='toself', name=c_name))
                fig_comp.update_layout(title=f"مخطط رادار مقارنة الفصول - {selected_grade}")

            fig_comp.update_layout(font_family="Cairo", plot_bgcolor="white", margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_comp, use_container_width=True)

### ---------------------------------------------------------
### التبويب الثالث: التصدير والمزامنة المزدوجة
### ---------------------------------------------------------
with tab_excel:
    st.subheader("🟢 التصدير والمزامنة المزدوجة (SQLite ↔ Google Sheets)")
    col_exp_box, col_sync_box, col_rev_box = st.columns(3)
    
    with col_exp_box:
        df_all_export = load_all_db_records()
        excel_data = export_to_excel_bytes(df_all_export)
        st.download_button(
            label="📥 تحميل كافة البيانات كملف Excel (.xlsx)",
            data=excel_data,
            file_name="درجات_المواد_الأربع_شامل.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
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

### ---------------------------------------------------------
### التبويب الرابع: إضافة طالب جديد
### ---------------------------------------------------------
with tab_add:
    st.subheader("➕ إضافة طالب جديد ورصد درجات المواد له")
    with st.form("add_student_v7_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            add_t = st.selectbox("الاختبار:", TESTS_LIST, index=TESTS_LIST.index(selected_test))
            add_g = st.selectbox("الصف الدراسي:", list(grades_map.keys()), index=list(grades_map.keys()).index(selected_grade))
            add_c = st.selectbox("الفصل:", grades_map[add_g])
            add_s_name = st.text_input("اسم الطالب رباعي:")
        with f2:
            st.write(" **رصد الدرجات الأولية للمواد (من 10):** ")
            add_s = st.number_input("علوم:", min_value=0.0, max_value=10.0, value=7.0, step=0.5)
            add_m = st.number_input("رياضيات:", min_value=0.0, max_value=10.0, value=7.0, step=0.5)
            add_l = st.number_input("لغتي:", min_value=0.0, max_value=10.0, value=7.0, step=0.5)
            add_e = st.number_input("انجليزي:", min_value=0.0, max_value=10.0, value=7.0, step=0.5)

        submit_add = st.form_submit_button("💾 حفظ الطالب والدرجات")
        if submit_add:
            if not add_s_name.strip():
                st.error("يرجى كتابة اسم الطالب.")
            else:
                save_new_student(add_t, add_g, add_c, add_s_name.strip(), add_s, add_m, add_l, add_e)
                st.success(f"تمت إضافة الطالب ({add_s_name}) بنجاح ومزامنة بياناته!")
                st.rerun()
