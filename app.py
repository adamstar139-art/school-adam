import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import io
import gspread
from google.oauth2.service_account import Credentials

# =========================================================
# 0. إعدادات حساب الخدمة والربط بـ Google Sheets
# =========================================================
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1XuneQDIfvpqKiuPQ-BcNBfOOm2G4vFBvwIa5F5gV15g/edit?usp=sharing"

SERVICE_ACCOUNT_INFO = {
  "type": "service_account",
  "project_id": "level-hope-509007-d2",
  "private_key_id": "c42734f035259f1f2255f53212a9d30ba68cd1a9",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCbobkzWaaWX2Qu\nXHWl+wf9PMlAkvP+XWgiB0NN/QED3s3qepXV1STYFJMD6/8SjXg/IcSxVguPHFJs\n5vKphFiKNsxQvgAMjgRAhB55FQ3LYWulaQ9Zgs6xpiSnZwZSN4X3ksceV7xozn13\nGKiZIP7YmuNlGg6piI3/+NGdiysvmg7F0sZedmmqE5Yasn1d450WbK1UDA12nBnB\nDfOPjKtQe28yqbj2Hm9veBfHuuIGZlnFJEbitOEoUjluZFb+3shHCsMo/FgpA9MI\nq2GG+yAK9jd0NVIEzPEhI/F77Rg4Q5EADTEs8b1kr/7eXDK/NKDCgRgqzCR/x0Db\n5v1UYHN/AgMBAAECggEARAGDuX4TzsKpNp79Y8WRZKWStY5hYwWy8qekz+fd8TCD\nX1IotjM4sdkvsreFkrhR0phxaCJW07bHB8JVSCDGRcMTPbcAs3u9POnenP9Hs1cD\nIFkLtYv0wOj+PE5HE1ciyZ+QNeCVumB8r7WNOriR09m+wteDj65VioRSKFr/SIGF\nLUzb8k55DrGn9626xxM2ugtvBir99yGCIzOjscoipkF+CiY5a9uWluZl7dgZKqYu\nj3CEuRe1NUatB4jU6Fnf8xW/QnYYVG2HB+zCNkesLw6DP1azfN+7G9R5gn6E7mnW\n3aUt8wKIZN2Wgd2NpoGJ03o/Wfc0h99gCuAGCo1PKQKBgQDNjXxRl8+ETPvZIrb2\nj4Z0VsebmugCdPP3T9wO+yZXtNmW0nf+8t4oZVn5paQdiS8z0rZd58VUFJRSHRpH\ndUZ11iOv7889oaLsy/2YQicY8GS+1+AWLbS4l5CIgBFxuuqjFRxO9e09Ac1+LbnP\neUjxqTGOC/iv9CYRkHaRJGV1KQKBgQDB08rUoYOj9SKn9nYJNvsebilRKQVThpJH\nqwnvXZlDcArzgV7FcN6X7Vi2SYwAk7sAXpOdXaz7UAVO5m4Idv+plh/OMktQ4lr2\nyeLoLR4hcQOmg/SzEoIFvTey0GLDtVvZm5PDB0OMBrPc5kmiLuC50kqjSYUMZszp\nh6muBBXQZwKBgCXunCh6eWMSyc8SJu1tIwTJFuDSP0pkxri21gc1taetyhGZGWfE\n7dZKjcYSGS0SKdHIarr9kF6pxY05raXOMIiCUeefu4DGGUjVhCDa5Fgn1I+bStEM\n8jK2VYe7Cn0QX0hlFupDW9pMQN2uFoIBAcMG1AxAjU37IiNPo3G5Y7exAoGAX7JW\nsVaxLPEp1C2+J1yK7YJMSfLr20pUzKeotxLKSd52ubUE+ox4iiA4LX/wbJSDvnHz\nhb2rW0Ut6b+hUfKW1b72IxL31o57hN82dZVZC//FYqBB32vi4DyE1HdIXAIdwDms\n4Zyjf+4LPaRBdJ6ae4RVL3tsAix7PU2qu+zubD8CgYAX8UhV3i6e1gIIO4kuJZV2\nhZoV3SZJ9JzNm5UHLeti7PMvcUKvUzG0b4OtsD/PFRgSh5uV1wG8yjviIb9yQRJa\n3vssSl148U5gB/sZwru8rte/rWNuxd/hif0gXMul6i0QuXRDhZqomqxZ4EzwYY7O\nGM8q3+/zsMUq5r4AQjzahg==\n-----END PRIVATE KEY-----\n",
  "client_email": "mohamed-samy@level-hope-509007-d2.iam.gserviceaccount.com",
  "client_id": "101141263500943756197",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mohamed-samy%40level-hope-509007-d2.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

def get_gsheet_worksheet():
    """الاتصال بـ Google Sheets مع المحاولة بالترتيب وتشخيص أسباب الخطأ"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 1. المحاولة الأولى: قراءة ملف service_account.json الخارجي
    if os.path.exists("service_account.json"):
        try:
            creds = Credentials.from_service_account_file("service_account.json", scopes=scopes)
            client = gspread.authorize(creds)
            return client.open_by_url(SPREADSHEET_URL).sheet1
        except Exception as e:
            st.error(f"❌ فشل الاتصال عبر ملف service_account.json: {e}")

    # 2. المحاولة الثانية: استخدام st.secrets من منصة Streamlit Cloud
    if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        try:
            info = dict(st.secrets["gcp_service_account"])
            if "private_key" in info and isinstance(info["private_key"], str):
                info["private_key"] = info["private_key"].replace("\n", "
")
            creds = Credentials.from_service_account_info(info, scopes=scopes)
            client = gspread.authorize(creds)
            return client.open_by_url(SPREADSHEET_URL).sheet1
        except Exception as e:
            st.error(f"❌ فشل الاتصال عبر st.secrets: {e}")

    # 3. المحاولة الثالثة: استخدام المفتاح المدمج مع تصحيح تنسيق Private Key
    try:
        info = dict(SERVICE_ACCOUNT_INFO)
        if "private_key" in info and isinstance(info["private_key"], str):
            info["private_key"] = info["private_key"].replace("\n", "
")
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(creds)
        return client.open_by_url(SPREADSHEET_URL).sheet1
    except Exception as e:
        st.error(f"❌ خطأ في الاتصال بـ Google Sheets: {e}")
        return None

def sync_db_to_gsheets():
    """مزامنة كافة بيانات SQLite المحلية وتصديرها إلى Google Sheets (مزامنة للأمام)"""
    ws = get_gsheet_worksheet()
    if ws is not None:
        try:
            df = load_all_db_records()
            ws.clear()
            ws.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
            return True, "تم رفع وتصدير البيانات إلى Google Sheets بنجاح!"
        except Exception as e:
            return False, f"تعذرت المزامنة مع Google Sheets: {e}"
    return False, "تعذر الاتصال بـ Google Sheets"

def sync_gsheets_to_db_reverse():
    """سحب وتحديث التعديلات من Google Sheets إلى قاعدة بيانات SQLite المحلية (مزامنة عكسية)"""
    ws = get_gsheet_worksheet()
    if ws is None:
        return False, "تعذر الاتصال بـ Google Sheets"
    try:
        records = ws.get_all_records()
        if not records:
            return False, "جدول Google Sheets فارغ أو لا يحتوي على بيانات."
        
        df_gsheet = pd.DataFrame(records)
        required_cols = ['المعرف', 'الاختبار', 'الصف الدراسي', 'الفصل', 'المسلسل', 'اسم الطالب', 'علوم', 'رياضيات', 'لغتي', 'انجليزي']
        missing_cols = [c for c in required_cols if c not in df_gsheet.columns]
        if missing_cols:
            return False, f"الأعمدة التالية مفقودة في Google Sheets: {missing_cols}"
            
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        updated_count = 0
        for _, row in df_gsheet.iterrows():
            rec_id = int(row['المعرف']) if str(row['المعرف']).isdigit() else None
            test_n = str(row['الاختبار'])
            grade_n = str(row['الصف الدراسي'])
            class_n = str(row['الفصل'])
            seq_n = int(row['المسلسل']) if str(row['المسلسل']).isdigit() else 1
            std_name = str(row['اسم الطالب'])
            
            def parse_num(v):
                try: return float(v)
                except: return 0.0

            sc = parse_num(row['علوم'])
            ma = parse_num(row['رياضيات'])
            lu = parse_num(row['لغتي'])
            en = parse_num(row['انجليزي'])
            
            if rec_id is not None:
                c.execute("SELECT id FROM grades WHERE id = ?", (rec_id,))
                exists = c.fetchone()
                if exists:
                    c.execute("""
                        UPDATE grades
                        SET test_name=?, grade=?, class_name=?, seq_num=?, student_name=?, science=?, math=?, lughati=?, english=?
                        WHERE id=?
                    """, (test_n, grade_n, class_n, seq_n, std_name, sc, ma, lu, en, rec_id))
                else:
                    c.execute("""
                        INSERT INTO grades (id, test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (rec_id, test_n, grade_n, class_n, seq_n, std_name, sc, ma, lu, en))
                updated_count += 1
            
        conn.commit()
        conn.close()
        return True, f"تمت المزامنة العكسية بنجاح! تم سحب وتحديث {updated_count} سجل من Google Sheets."
    except Exception as e:
        return False, f"حدث خطأ أثناء المزامنة العكسية: {e}"

# =========================================================
# 1. تهيئة الصفحة والنمط Visual Theme & Page Config
# =========================================================
st.set_page_config(
    page_title="نظام رصد الدرجات والرسوم البيانية - متوسطة الثغر النموذجية الأهلية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def clean_html(html_str):
    if not html_str: return ""
    lines = [line.strip() for line in html_str.strip().splitlines()]
    return "
".join([line for line in lines if line])

css_code = """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    .main-header { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 24px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .main-header h1 { font-size: 26px; font-weight: 800; margin: 0 0 8px 0; color: #ffffff; }
    .main-header p { font-size: 15px; margin: 0; opacity: 0.9; }
    .designer-banner { margin-top: 12px; background: rgba(255, 255, 255, 0.15); padding: 6px 14px; border-radius: 8px; display: inline-flex; align-items: center; gap: 8px; }
    .designer-icon { color: #f59e0b; font-size: 14px; }
    .designer-text { color: #ffffff; font-weight: 700; font-size: 13px; }
    .top-toolbar { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
    .save-indicator { color: #16a34a; font-weight: 700; font-size: 14px; display: flex; align-items: center; gap: 8px; }
    .color-legend { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; }
    .color-box { width: 16px; height: 16px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.1); }
    .custom-grade-table { width: 100%; border-collapse: collapse; margin-top: 15px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .custom-grade-table th { background: #1e3a8a; color: white; padding: 12px 10px; text-align: center; font-weight: 700; font-size: 14px; border: 1px solid #1e40af; }
    .custom-grade-table td { padding: 10px; text-align: center; border: 1px solid #e2e8f0; font-size: 14px; font-weight: 600; }
    .score-green { background-color: #bbf7d0 !important; color: #14532d !important; font-weight: 800; }
    .score-red { background-color: #fecaca !important; color: #7f1d1d !important; font-weight: 800; }
    .score-zero { background-color: #e5e7eb !important; color: #9ca3af !important; }
    .score-blank { background-color: #ffffff !important; color: transparent !important; }
    .td-name { text-align: right !important; padding-right: 15px !important; font-weight: 700; color: #1e293b; }
    .td-seq { font-weight: 700; color: #64748b; background: #f8fafc; }
</style>
"""
st.markdown(clean_html(css_code), unsafe_allow_html=True)

# =========================================================
# 2. البيانات وقواعد البيانات
# =========================================================
RAW_EXCEL_STUDENTS = [
    { "seq": 1, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "بلال عبد الرزاق عيسى العيسى", "science": 5.0, "math": 9.0, "lughati": 5.0, "english": 4.0 },
    { "seq": 2, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "جاسر بن عبد الله بن منصور الحارثي", "science": 4.0, "math": 0.0, "lughati": 3.0, "english": 1.0 },
    { "seq": 3, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "حسام بن محمد بن علي ال رايان البارقي", "science": 3.0, "math": 4.0, "lughati": 6.0, "english": 6.0 },
    { "seq": 4, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "ريان عبد الله جابر الأسمري", "science": 4.0, "math": 7.0, "lughati": 6.0, "english": 3.0 },
    { "seq": 5, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "زيد زياد عبد اللطيف أبو قبع", "science": 6.0, "math": 0.0, "lughati": 5.0, "english": 6.0 },
    { "seq": 6, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "سامي سعد عباس حمد", "science": 3.0, "math": 0.0, "lughati": 6.0, "english": 5.0 },
    { "seq": 7, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "سعد ناصر سعد السيف", "science": 3.0, "math": 0.0, "lughati": 2.0, "english": 4.0 },
    { "seq": 8, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "عبد الله بن سليمان بن عبد الله الراجحي", "science": 0.0, "math": 0.0, "lughati": 7.0, "english": 0.0 },
    { "seq": 9, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "عبد الله سعد بن محمد العيشان", "science": 0.0, "math": 0.0, "lughati": 7.0, "english": 0.0 },
    { "seq": 10, "grade": "الصف الأول المتوسط", "class": "فصل 101", "name": "علي أحمد علي كريري", "science": 4.0, "math": 0.0, "lughati": 5.0, "english": 2.0 }
]

TESTS_LIST = ["الاختبار التشخيصي الأول", "الاختبار التشخيصي الثاني", "الاختبار التشخيصي الثالث", "الاختبار التشخيصي الرابع"]
DB_FILE = "student_grades_v12.db"

def init_db():
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
    if c.fetchone()[0] == 0:
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
        SELECT id AS 'المعرف', test_name AS 'الاختبار', grade AS 'الصف الدراسي', class_name AS 'الفصل', seq_num AS 'المسلسل', student_name AS 'اسم الطالب', science AS 'علوم', math AS 'رياضيات', lughati AS 'لغتي', english AS 'انجليزي'
        FROM grades
    """, conn)
    conn.close()
    return df

def load_class_students(test_name, grade_name, class_name):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT id, seq_num AS 'المسلسل', student_name AS 'اسم الطالب', science AS 'علوم', math AS 'رياضيات', lughati AS 'لغتي', english AS 'انجليزي'
        FROM grades
        WHERE test_name = ? AND grade = ? AND class_name = ?
        ORDER BY seq_num ASC
    """, conn, params=[test_name, grade_name, class_name])
    conn.close()
    return df

def update_student_scores(edited_df):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for _, row in edited_df.iterrows():
        c.execute("""
            UPDATE grades
            SET science = ?, math = ?, lughati = ?, english = ?
            WHERE id = ?
        """, (row['علوم'], row['رياضيات'], row['لغتي'], row['انجليزي'], row['id']))
    conn.commit()
    conn.close()
    success, msg = sync_db_to_gsheets()
    if success:
        st.success(msg)
    else:
        st.warning(msg)

def save_new_student(test_name, grade_name, class_name, student_name, s, m, l, e):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MAX(seq_num) FROM grades WHERE test_name = ? AND grade = ? AND class_name = ?", (test_name, grade_name, class_name))
    max_seq_res = c.fetchone()
    next_seq = ((max_seq_res[0] or 0) if max_seq_res and max_seq_res[0] else 0) + 1
    
    c.execute("""
        INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (test_name, grade_name, class_name, next_seq, student_name, s, m, l, e))
    conn.commit()
    conn.close()
    success, msg = sync_db_to_gsheets()
    if success:
        st.success(msg)
    else:
        st.warning(msg)

def export_to_excel_bytes(df_export):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='درجات المواد الأربع')
    output.seek(0)
    return output

init_db()

# =========================================================
# 3. الهيدر وشريط الأدوات العلوي Main Header
# =========================================================
header_html = """<div class="main-header">
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

# =========================================================
# 4. القوائم المنسدلة المتسلسلة
# =========================================================
col_t, col_g, col_c = st.columns(3)
with col_t: selected_test = st.selectbox("📌 1. اختر الاختبار التشخيصي:", TESTS_LIST, index=0)
grades_map = {
    "الصف الأول المتوسط": ["فصل 101", "فصل 102"],
    "الصف الثاني المتوسط": ["فصل 201", "فصل 202", "فصل 203"],
    "الصف الثالث المتوسط": ["فصل 301", "فصل 302", "فصل 303"]
}
with col_g: selected_grade = st.selectbox("🏫 2. اختر الصف الدراسي:", list(grades_map.keys()), index=0)
with col_c: selected_class = st.selectbox("📚 3. اختر الفصل:", grades_map[selected_grade], index=0)

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
        st.warning("لا توجد بيانات طلاب لهذا الفصل في هذا الاختبار.")
    else:
        legend_html = """<div class="color-legend">
            <span style="font-weight:800; color:#1e3a8a;">🎨 دليل التنسيق الشرطي للدرجات:</span>
            <div class="legend-item">
                <div class="color-box" style="background:#bbf7d0;"></div>
                <span>درجة ≥ 5.0 (أخضر فاتح - إتقان)</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background:#fecaca;"></div>
                <span>درجة < 5.0 (أحمر فاتح - دون الإتقان)</span>
            </div>
            <div class="legend-item">
                <div class="color-box" style="background:#e5e7eb;"></div>
                <span>بدون درجة / 0 (رصاصي فاتح - خالية)</span>
            </div>
        </div>"""
        st.markdown(clean_html(legend_html), unsafe_allow_html=True)

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            show_blank = st.checkbox("📝 عرض وطباعة كشف رصد فارغ (بدون درجات للتصحيح الورقي)", value=False)
        with c_btn2:
            if st.button("🖨️ طباعة تقرير الفصل (PDF / Print)", type="primary"):
                st.components.v1.html("""<script>setTimeout(function() { window.parent.print(); }, 200);</script>""", height=0)

        st.write("✏️ **جدول الرصد المنظم والتعديل التفاعلي:**")

        edited_df = st.data_editor(
            df_students[['id', 'المسلسل', 'اسم الطالب', 'علوم', 'رياضيات', 'لغتي', 'انجليزي']],
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
        
        if st.button("💾 حفظ التعديلات في SQLite + Google Sheets", type="secondary"):
            update_student_scores(edited_df)
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.write("📊 **عرض جدول الرصد المنسق بالكامل:**")

        def build_html_grade_table(df_data, is_blank=False):
            rows_html = ""
            for _, row in df_data.iterrows():
                seq = row['المسلسل']
                name = row['اسم الطالب']
                
                if is_blank:
                    rows_html += f"""<tr>
                        <td class="td-seq">{seq}</td>
                        <td class="td-name">{name}</td>
                        <td class="score-blank"></td>
                        <td class="score-blank"></td>
                        <td class="score-blank"></td>
                        <td class="score-blank"></td>
                        <td class="score-blank"></td>
                        <td class="score-blank"></td>
                    </tr>"""
                else:
                    s_val = row['علوم']
                    m_val = row['رياضيات']
                    l_val = row['لغتي']
                    e_val = row['انجليزي']
                    tot_val = s_val + m_val + l_val + e_val
                    avg_val = tot_val / 4.0 if tot_val > 0 else 0.0
                    
                    def fmt_score_cell(v):
                        if pd.isna(v) or v == 0 or v == 0.0:
                            return 'score-zero', ''
                        elif v < 5.0:
                            txt = f'{int(v)}' if v == int(v) else f'{v:g}'
                            return 'score-red', txt
                        else:
                            txt = f'{int(v)}' if v == int(v) else f'{v:g}'
                            return 'score-green', txt

                    cs, ts = fmt_score_cell(s_val)
                    cm, tm = fmt_score_cell(m_val)
                    cl, tl = fmt_score_cell(l_val)
                    ce, te = fmt_score_cell(e_val)
                    
                    ttot = f'{int(tot_val)}' if tot_val == int(tot_val) else f'{tot_val:g}' if tot_val > 0 else ''
                    tavg = f'{int(avg_val)}' if avg_val == int(avg_val) else f'{avg_val:.2f}' if avg_val > 0 else ''
                    
                    rows_html += f"""<tr>
                        <td class="td-seq">{seq}</td>
                        <td class="td-name">{name}</td>
                        <td class="{cs}">{ts}</td>
                        <td class="{cm}">{tm}</td>
                        <td class="{cl}">{tl}</td>
                        <td class="{ce}">{te}</td>
                        <td style="background:#f1f5f9; color:#0f172a; font-weight:800;">{ttot}</td>
                        <td style="background:#f1f5f9; color:#0f172a; font-weight:800;">{tavg}</td>
                    </tr>"""
        
            table_html = f"""<table class="custom-grade-table">
                <thead>
                    <tr>
                        <th class="th-seq">م</th>
                        <th class="th-name">اسم الطالب</th>
                        <th class="th-sci">علوم (10)</th>
                        <th class="th-math">رياضيات (10)</th>
                        <th class="th-lug">لغتي (10)</th>
                        <th class="th-eng">انجليزي (10)</th>
                        <th class="th-tot">المجموع (40)</th>
                        <th class="th-avg">المتوسط (10)</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>"""
            return table_html

        table_html = build_html_grade_table(df_students, is_blank=show_blank)
        st.markdown(clean_html(table_html), unsafe_allow_html=True)

# ---------------------------------------------------------
# التبويب الثاني: الرسم البياني والمقارنة
# ---------------------------------------------------------
with tab_charts:
    st.subheader(f"📈 التحليل البياني والمقارنة بين الفصول - {selected_test}")
    col_ch_print, col_ch_multi = st.columns([3, 4])
    with col_ch_multi:
        avail_classes = grades_map[selected_grade]
        selected_classes_compare = st.multiselect("📚 اختر الفصول للمقارنة:", avail_classes, default=avail_classes)
    with col_ch_print:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🖨️ طباعة الرسم البياني (PDF)", type="primary"):
            st.components.v1.html("""<script>setTimeout(function() { window.parent.print(); }, 300);</script>""", height=0)

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

# ---------------------------------------------------------
# التبويب الثالث: التصدير والمزامنة
# ---------------------------------------------------------
with tab_excel:
    st.subheader("🟢 استيراد وتصدير والمزامنة المزدوجة مع Google Sheets")
    col_exp_box, col_sync_box, col_rev_box = st.columns(3)
    with col_exp_box:
        df_all_export = load_all_db_records()
        excel_data = export_to_excel_bytes(df_all_export)
        st.download_button(
            label="📥 تحميل كافة البيانات (.xlsx)",
            data=excel_data,
            file_name="درجات_المواد_الأربع_شامل.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    with col_sync_box:
        if st.button("⬆️ تصدير إلى Google Sheets", type="secondary"):
            success, msg = sync_db_to_gsheets()
            if success:
                st.success(msg)
            else:
                st.error(msg)
    with col_rev_box:
        if st.button("⬇️ سحب التعديلات من Google Sheets", type="secondary"):
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
    st.subheader("➕ إضافة طالب جديد ورصد درجات المواد له")
    with st.form("add_student_v5_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            add_t = st.selectbox("الاختبار:", TESTS_LIST, index=TESTS_LIST.index(selected_test))
            add_g = st.selectbox("الصف الدراسي:", list(grades_map.keys()), index=list(grades_map.keys()).index(selected_grade))
            add_c = st.selectbox("الفصل:", grades_map[add_g])
            add_s_name = st.text_input("اسم الطالب رباعي:")
        with f2:
            st.write("**رصد الدرجات الأولية للمواد (من 10):**")
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
                st.rerun()
