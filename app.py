import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import io
import os
import gspread
from google.oauth2.service_account import Credentials

# =========================================================
# 0. إعدادات حساب الخدمة والربط بـ Google Sheets عبر st.secrets
# =========================================================
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1XuneQDIfvpqKiuPQ-BcNBfOOm2G4vFBvwIa5F5gV15g/edit?usp=sharing"

def get_gsheet_worksheet():
    """الاتصال بـ Google Sheets عبر st.secrets أو service_account.json المحشي"""
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
    """مزامنة كافة بيانات SQLite المحلية وتصديرها إلى Google Sheets (مزامنة للأمام)"""
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
    """سحب وتحديث التعديلات من Google Sheets إلى قاعدة بيانات SQLite المحلية (مزامنة عكسية)"""
    try:
        ws = get_gsheet_worksheet()
        if ws is None:
            return False, "⚠️ تعذر الاتصال بـ Google Sheets. يُرجى التثبت من إعدادات Streamlit Secrets."
        
        all_values = ws.get_all_values()
        if not all_values or len(all_values) < 2:
            return False, "⚠️ جدول Google Sheets فارغ أو لا يحتوي على بيانات."
            
        headers = [str(h).strip() for h in all_values[0]]
        rows = all_values[1:]
        
        df_gsheet = pd.DataFrame(rows, columns=headers)
        # إزالة الأعمدة المكررة أو الفارغة في الترويسة للتغلب على أخطاء الأعمدة الخالية في Google Sheets
        df_gsheet = df_gsheet.loc[:, ~df_gsheet.columns.duplicated()]
        if '' in df_gsheet.columns:
            df_gsheet = df_gsheet.drop(columns=[''])
        required_cols = ['المعرف', 'الاختبار', 'الصف الدراسي', 'الفصل', 'المسلسل', 'اسم الطالب', 'علوم', 'رياضيات', 'لغتي', 'انجليزي']
        missing_cols = [c for c in required_cols if c not in df_gsheet.columns]
        if missing_cols:
            return False, f"⚠️ الأعمدة التالية مفقودة في Google Sheets: {missing_cols}"
            
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
        return True, f"🟢 تمت المزامنة العكسية بنجاح! تم سحب وتحديث {updated_count} سجل من Google Sheets."
    except Exception as e:
        return False, f"❌ حدث خطأ أثناء المزامنة العكسية: {e}"

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
    return "\n".join([line for line in lines if line])

css_code = """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
    
    /* الترويسة الرئيسية - التوسط والترتيب */
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 24px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        text-align: center !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .main-header h1 { font-size: 26px; font-weight: 800; margin: 0 0 8px 0; color: #ffffff; text-align: center !important; }
    .main-header p { font-size: 15px; margin: 0; opacity: 0.9; text-align: center !important; }
    .designer-banner {
        margin-top: 12px;
        background: rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 8px;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 8px;
        text-align: center !important;
    }
    .designer-icon { color: #f59e0b; font-size: 14px; }
    .designer-text { color: #ffffff; font-weight: 700; font-size: 13px; }
    
    .top-toolbar { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 20px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
    .save-indicator { color: #16a34a; font-weight: 700; font-size: 14px; display: flex; align-items: center; gap: 8px; }
    .color-legend { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; }
    .color-box { width: 16px; height: 16px; border-radius: 4px; border: 1px solid rgba(0,0,0,0.1); }
    
    /* الجداول */
    .custom-grade-table { width: 100%; border-collapse: collapse; margin-top: 15px; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
    .custom-grade-table th { background: #1e3a8a; color: white; padding: 12px 10px; text-align: center; font-weight: 700; font-size: 14px; border: 1px solid #1e40af; }
    .custom-grade-table td { padding: 10px; text-align: center; border: 1px solid #e2e8f0; font-size: 14px; font-weight: 600; }
    .score-green { background-color: #bbf7d0 !important; color: #14532d !important; font-weight: 800; }
    .score-red { background-color: #fecaca !important; color: #7f1d1d !important; font-weight: 800; }
    .score-zero { background-color: #e5e7eb !important; color: #9ca3af !important; }
    .score-blank { background-color: #ffffff !important; color: transparent !important; }
    .td-name { text-align: right !important; padding-right: 15px !important; font-weight: 700; color: #1e293b; }
    .td-seq { font-weight: 700; color: #64748b; background: #f8fafc; }

    /* إخفاء عناصر التحكم عند الطباعة */
    .no-print { display: block; }

    /* إعدادات الطباعة المتقدمة الاحترافية */
    @media print {
        @page {
            size: A4 portrait;
            margin: 6mm;
        }

        /* إخفاء كافة عناصر التحكم والتنقل وجدول الرصد المباشر */
        header, [data-testid="stHeader"], [data-testid="stSidebar"], 
        .main-header, .top-toolbar, .stButton, .stSelectbox, .stMultiSelect, 
        .stCheckbox, [data-testid="stForm"], .no-print, .color-legend,
        div[data-testid="stToolbar"], button, iframe[title="st.iframe"],
        div[data-testid="stDataEditor"], div[data-testid="stDataFrame"],
        .stDataEditor, hr {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        body, html, [data-testid="stAppViewContainer"], .main, .block-container, [data-testid="stVerticalBlock"] {
            background: #ffffff !important;
            color: #000000 !important;
            padding: 0 !important;
            margin: 0 !important;
            width: 100% !important;
            max-width: 100% !important;
            overflow: visible !important;
        }

        /* طباعة الجدول المنسق فقط في صفحة واحدة احترافية */
        .custom-grade-table {
            width: 100% !important;
            font-size: 9pt !important;
            border-collapse: collapse !important;
            border: 1.5px solid #1e3a8a !important;
            box-shadow: none !important;
            margin-top: 5px !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }
        .custom-grade-table th {
            background-color: #1e3a8a !important;
            color: #ffffff !important;
            padding: 5px 4px !important;
            font-size: 9.5pt !important;
            border: 1px solid #1e40af !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        .custom-grade-table td {
            padding: 3.5px 4px !important;
            font-size: 9pt !important;
            border: 1px solid #cbd5e1 !important;
        }
        .score-green {
            background-color: #bbf7d0 !important;
            color: #14532d !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        .score-red {
            background-color: #fecaca !important;
            color: #7f1d1d !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
        .score-zero {
            background-color: #f1f5f9 !important;
            color: #94a3b8 !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }

        /* طباعة الرسوم البيانية في صفحة واحدة واضحة وبكامل أبعادها */
        div[data-testid="stPlotlyChart"], 
        .js-plotly-plot, 
        .plot-container, 
        .svg-container {
            width: 100% !important;
            max-width: 100% !important;
            height: 75vh !important;
            max-height: 220mm !important;
            page-break-inside: avoid !important;
            break-inside: avoid !important;
            overflow: hidden !important;
            margin: 0 auto !important;
        }

        .js-plotly-plot .plotly .main-svg {
            width: 100% !important;
            max-width: 100% !important;
            height: 100% !important;
        }
    }
</style>"""
st.markdown(clean_html(css_code), unsafe_allow_html=True)

# =========================================================
# 2. البيانات وقواعد البيانات
# =========================================================
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
    {   'class': 'فصل 201',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 6.0,
        'math': 3.0,
        'name': 'إبراهيم ياسر إبراهيم الحلوى',
        'science': 4.0,
        'seq': 1},
    {   'class': 'فصل 201',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 2.0,
        'math': 2.0,
        'name': 'أحمد سامي بن أحمد العمران',
        'science': 3.0,
        'seq': 2},
    {   'class': 'فصل 201',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'الوليد عبد الله بن إبراهيم المبدل',
        'science': 0.0,
        'seq': 3},
    {   'class': 'فصل 201',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 0.0,
        'name': 'ذياب بن محمد بن ذياب بن محمد ال مريع القحطاني',
        'science': 0.0,
        'seq': 4},
    {   'class': 'فصل 201',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 2.0,
        'math': 3.0,
        'name': 'راكان بن محمد بن مسفر القحطاني',
        'science': 5.0,
        'seq': 5},
    {   'class': 'فصل 201',
        'english': 2.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 2.0,
        'name': 'سلطان عبد الله حسن القحطاني',
        'science': 3.0,
        'seq': 6},
    {   'class': 'فصل 201',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 3.0,
        'math': 0.0,
        'name': 'عبد الرحمن حمد بن محمد العريفي',
        'science': 0.0,
        'seq': 7},
    {   'class': 'فصل 201',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 6.0,
        'math': 3.0,
        'name': 'عبد الرحمن ربيع جابر خبراني',
        'science': 7.0,
        'seq': 8},
    {   'class': 'فصل 201',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 3.0,
        'math': 3.0,
        'name': 'عبد العزيز سعود بن فهد العتيبي',
        'science': 4.0,
        'seq': 9},
    {   'class': 'فصل 201',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 2.0,
        'name': 'عبد اللطيف إبراهيم محمد الطمره',
        'science': 2.0,
        'seq': 10},
    {   'class': 'فصل 201',
        'english': 1.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 2.0,
        'math': 2.0,
        'name': 'فهد عيسى محمد العيسى',
        'science': 3.0,
        'seq': 11},
    {   'class': 'فصل 201',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'فيصل بن عبد الله بن سعود بن عبد العزيز الجميهه',
        'science': 0.0,
        'seq': 12},
    {   'class': 'فصل 201',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'مبارك صالح مبارك هليل',
        'science': 0.0,
        'seq': 13},
    {   'class': 'فصل 201',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 2.0,
        'math': 0.0,
        'name': 'محمد بن عبد الله بن حمد بن ناصر بن عمران',
        'science': 2.0,
        'seq': 14},
    {   'class': 'فصل 201',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 3.0,
        'math': 7.0,
        'name': 'محمد عبد المحسن ناصر الحزام',
        'science': 7.0,
        'seq': 15},
    {   'class': 'فصل 201',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 2.0,
        'name': 'محمد فايز عبد الرحمن بن يوسف',
        'science': 6.0,
        'seq': 16},
    {   'class': 'فصل 201',
        'english': 6.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 2.0,
        'math': 4.0,
        'name': 'مشاري سلطان سالم الشمراني',
        'science': 3.0,
        'seq': 17},
    {   'class': 'فصل 201',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'معاذ عبد الله سعود العريفي',
        'science': 0.0,
        'seq': 18},
    {   'class': 'فصل 201',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 2.0,
        'name': 'ناصر حسين محمد ال جبران',
        'science': 4.0,
        'seq': 19},
    {   'class': 'فصل 202',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 3.0,
        'name': 'أنس خالد المرزوق',
        'science': 5.0,
        'seq': 1},
    {   'class': 'فصل 202',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 2.0,
        'name': 'بندر علي فهد القحطاني',
        'science': 4.0,
        'seq': 2},
    {   'class': 'فصل 202',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 6.0,
        'math': 4.0,
        'name': 'حسن محمد حسن العمري',
        'science': 3.0,
        'seq': 3},
    {   'class': 'فصل 202',
        'english': 6.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 5.0,
        'name': 'خالد سعد الدوسري',
        'science': 6.0,
        'seq': 4},
    {   'class': 'فصل 202',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 3.0,
        'name': 'راشد فهد ناصر العريفي',
        'science': 4.0,
        'seq': 5},
    {   'class': 'فصل 202',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 6.0,
        'math': 4.0,
        'name': 'سعد عبد الله العتيبي',
        'science': 5.0,
        'seq': 6},
    {   'class': 'فصل 202',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 3.0,
        'name': 'سعود عبدالعزيز الشمري',
        'science': 4.0,
        'seq': 7},
    {   'class': 'فصل 202',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 2.0,
        'name': 'سلطان ناصر السبيعي',
        'science': 3.0,
        'seq': 8},
    {   'class': 'فصل 202',
        'english': 6.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 7.0,
        'math': 5.0,
        'name': 'صالح فهد الميموني',
        'science': 6.0,
        'seq': 9},
    {   'class': 'فصل 202',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 4.0,
        'name': 'عبد الرحمن علي الشهري',
        'science': 5.0,
        'seq': 10},
    {   'class': 'فصل 202',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 3.0,
        'name': 'عبد العزيز محمد الحارثي',
        'science': 4.0,
        'seq': 11},
    {   'class': 'فصل 202',
        'english': 7.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 6.0,
        'math': 5.0,
        'name': 'عبد الله خالد المطيري',
        'science': 6.0,
        'seq': 12},
    {   'class': 'فصل 202',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 4.0,
        'name': 'علي حسين الزهراني',
        'science': 5.0,
        'seq': 13},
    {   'class': 'فصل 202',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 3.0,
        'name': 'عمر سعد القحطاني',
        'science': 3.0,
        'seq': 14},
    {   'class': 'فصل 202',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 3.0,
        'math': 2.0,
        'name': 'فهد ناصر الدوسري',
        'science': 4.0,
        'seq': 15},
    {   'class': 'فصل 202',
        'english': 6.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 4.0,
        'name': 'فيصل عبد الله العريفي',
        'science': 5.0,
        'seq': 16},
    {   'class': 'فصل 202',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 3.0,
        'name': 'محمد بن سعيد القحطاني',
        'science': 4.0,
        'seq': 17},
    {   'class': 'فصل 202',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 4.0,
        'name': 'مشاري فهد الحربي',
        'science': 5.0,
        'seq': 18},
    {   'class': 'فصل 202',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 3.0,
        'math': 2.0,
        'name': 'نايف بن بندر بن خلفان العلوي',
        'science': 0.0,
        'seq': 19},
    {   'class': 'فصل 202',
        'english': 5.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 3.0,
        'name': 'نواف عبد العزيز المرزوق',
        'science': 6.0,
        'seq': 20},
    {   'class': 'فصل 202',
        'english': 1.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 2.0,
        'math': 2.0,
        'name': 'هادي سلطان هادي القحطاني',
        'science': 1.0,
        'seq': 21},
    {   'class': 'فصل 202',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 0.0,
        'name': 'يزيد بن حسين بن متعب بن محمد كعكم',
        'science': 0.0,
        'seq': 22},
    {   'class': 'فصل 203',
        'english': 6.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 7.0,
        'math': 4.0,
        'name': 'ثامر عمر إبراهيم عثمان',
        'science': 3.0,
        'seq': 1},
    {   'class': 'فصل 203',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 2.0,
        'name': 'جهاد فارس عبد القادر حتاوي',
        'science': 2.0,
        'seq': 2},
    {   'class': 'فصل 203',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'خالد محمد عبد الكريم الخفاجي',
        'science': 4.0,
        'seq': 3},
    {   'class': 'فصل 203',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 2.0,
        'name': 'سعد ابن مسفر بن سعد القحطاني',
        'science': 5.0,
        'seq': 4},
    {   'class': 'فصل 203',
        'english': 2.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'سعود بن عبد الله بن سعود السحامي',
        'science': 4.0,
        'seq': 5},
    {   'class': 'فصل 203',
        'english': 8.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 6.0,
        'math': 6.0,
        'name': 'سعود ناصر سنيف العريفي',
        'science': 4.0,
        'seq': 6},
    {   'class': 'فصل 203',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 2.0,
        'name': 'سعيد محمد باوزير',
        'science': 0.0,
        'seq': 7},
    {   'class': 'فصل 203',
        'english': 6.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 7.0,
        'math': 3.0,
        'name': 'طلال بن فهد بن عطيه بالحكم الزهراني',
        'science': 7.0,
        'seq': 8},
    {   'class': 'فصل 203',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 5.0,
        'name': 'عبد الرحمن أحمد جاسم الحمدي',
        'science': 4.0,
        'seq': 9},
    {   'class': 'فصل 203',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 2.0,
        'name': 'عبد العزيز ماجد راشد الزير',
        'science': 5.0,
        'seq': 10},
    {   'class': 'فصل 203',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 1.0,
        'name': 'عبد العزيز وليد ناصر بن سعران',
        'science': 4.0,
        'seq': 11},
    {   'class': 'فصل 203',
        'english': 2.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 2.0,
        'name': 'عبد الله بن بندر بن فهد المفيجل',
        'science': 5.0,
        'seq': 12},
    {   'class': 'فصل 203',
        'english': 9.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 7.0,
        'math': 8.0,
        'name': 'عبد المجيد بن محمد بن مسعود آل عايض القحطاني',
        'science': 4.0,
        'seq': 13},
    {   'class': 'فصل 203',
        'english': 6.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 5.0,
        'name': 'عز الدين أحمد محمد سعد',
        'science': 3.0,
        'seq': 14},
    {   'class': 'فصل 203',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 5.0,
        'math': 2.0,
        'name': 'عزام خالد شهوب بن شهوب',
        'science': 4.0,
        'seq': 15},
    {   'class': 'فصل 203',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'عزام فهد أحمد صلوي',
        'science': 2.0,
        'seq': 16},
    {   'class': 'فصل 203',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 5.0,
        'name': 'عمر وليد ياسين درويش علي',
        'science': 4.0,
        'seq': 17},
    {   'class': 'فصل 203',
        'english': 3.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 3.0,
        'name': 'فارس ابن محمد بن سالم الحربي',
        'science': 3.0,
        'seq': 18},
    {   'class': 'فصل 203',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 4.0,
        'math': 3.0,
        'name': 'محمد بن علي محسن العثيميني',
        'science': 1.0,
        'seq': 19},
    {   'class': 'فصل 203',
        'english': 4.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 6.0,
        'math': 0.0,
        'name': 'وائل بن عبد الله بن عامر الغامدي',
        'science': 1.0,
        'seq': 20},
    {   'class': 'فصل 203',
        'english': 0.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'يزيد بن حمد القحطاني',
        'science': 2.0,
        'seq': 21},
    {   'class': 'فصل 203',
        'english': 7.0,
        'grade': 'الصف الثاني المتوسط',
        'lughati': 6.0,
        'math': 6.0,
        'name': 'يوسف عايد عواد البلوي',
        'science': 8.0,
        'seq': 22},
    {   'class': 'فصل 301',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 3.0,
        'name': 'أصيل ناصر بن محمد مذكور',
        'science': 3.0,
        'seq': 1},
    {   'class': 'فصل 301',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'خالد محمد مسعف معافا',
        'science': 0.0,
        'seq': 2},
    {   'class': 'فصل 301',
        'english': 8.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'راشد سعيد راشد عبد السلام',
        'science': 4.0,
        'seq': 3},
    {   'class': 'فصل 301',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 7.0,
        'name': 'راكان بن عبد الله بن سالم اليافعي',
        'science': 4.0,
        'seq': 4},
    {   'class': 'فصل 301',
        'english': 1.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'زياد أحمد بن علي اللحيد',
        'science': 3.0,
        'seq': 5},
    {   'class': 'فصل 301',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 5.0,
        'name': 'سطام محمد سعود الدوسري',
        'science': 5.0,
        'seq': 6},
    {   'class': 'فصل 301',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 4.0,
        'name': 'سلطان أحمد صالح الفتوح',
        'science': 6.0,
        'seq': 7},
    {   'class': 'فصل 301',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'عبد العزيز عبد الله شراز المالكي',
        'science': 5.0,
        'seq': 8},
    {   'class': 'فصل 301',
        'english': 5.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 7.0,
        'math': 6.0,
        'name': 'عبد العزيز عبد الله عايض الأسمري',
        'science': 5.0,
        'seq': 9},
    {   'class': 'فصل 301',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 4.0,
        'math': 4.0,
        'name': 'عبد الله عبيد عبد الله العتيبي',
        'science': 2.0,
        'seq': 10},
    {   'class': 'فصل 301',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'عبد الله فهد جلوي سالم الشرعي',
        'science': 0.0,
        'seq': 11},
       {   'class': 'فصل 301',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 7.0,
        'name': 'عماد الدين إسلام محمد دراز',
        'science': 0.0,
        'seq': 13},
    {   'class': 'فصل 301',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 2.0,
        'name': 'عمر فهد محمد السقامي',
        'science': 4.0,
        'seq': 14},
    {   'class': 'فصل 301',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 5.0,
        'math': 0.0,
        'name': 'فهد عبد الرحمن فهد العتيبي',
        'science': 3.0,
        'seq': 15},
    {   'class': 'فصل 301',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 9.0,
        'name': 'فيصل بن عبد الرحمن بن عايض العصيمي العتيبي',
        'science': 5.0,
        'seq': 16},
    {   'class': 'فصل 301',
        'english': 4.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 7.0,
        'math': 7.0,
        'name': 'فيصل محمد صالح الفتوح',
        'science': 5.0,
        'seq': 17},
    {   'class': 'فصل 301',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 5.0,
        'name': 'محمد سلطان عبد العزيز العيد',
        'science': 4.0,
        'seq': 18},
    {   'class': 'فصل 301',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 6.0,
        'name': 'محمد مقعد ساير العتيبي',
        'science': 5.0,
        'seq': 19},
    {   'class': 'فصل 301',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 4.0,
        'name': 'مشاري إبراهيم عبد اللطيف المغربي',
        'science': 0.0,
        'seq': 20},
    {   'class': 'فصل 301',
        'english': 4.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 6.0,
        'name': 'مشاري علي موسى عقيلي',
        'science': 4.0,
        'seq': 21},
    {   'class': 'فصل 301',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 7.0,
        'math': 4.0,
        'name': 'مهند عبد الله فهد الزكري',
        'science': 6.0,
        'seq': 22},
    {   'class': 'فصل 301',
        'english': 5.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 5.0,
        'math': 6.0,
        'name': 'نواف وليد حمد الشعلان',
        'science': 5.0,
        'seq': 23},
    {   'class': 'فصل 301',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'يوسف نايف مقعد العتيبي',
        'science': 5.0,
        'seq': 24},
    {   'class': 'فصل 302',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'تركي عبد العزيز عبد الله المرزوق',
        'science': 4.0,
        'seq': 1},
    {   'class': 'فصل 302',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'تركي عثمان عبد العزيز العثمان',
        'science': 4.0,
        'seq': 2},
    {   'class': 'فصل 302',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'راشد أحمد فهد آل سعيد',
        'science': 0.0,
        'seq': 3},
    {   'class': 'فصل 302',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 4.0,
        'math': 3.0,
        'name': 'راكان إبراهيم محمد ديوان',
        'science': 4.0,
        'seq': 4},
    {   'class': 'فصل 302',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'ريان ناصر عبد الرحمن المرشود',
        'science': 4.0,
        'seq': 5},
    {   'class': 'فصل 302',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'صالح بن ممدوح الجويعي',
        'science': 3.0,
        'seq': 6},
    {   'class': 'فصل 302',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 4.0,
        'name': 'عبد الرحمن محمد صلاح بدر الدين',
        'science': 6.0,
        'seq': 7},
    {   'class': 'فصل 302',
        'english': 5.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 4.0,
        'name': 'عبد العزيز تركي عبد العزيز اللهيم',
        'science': 2.0,
        'seq': 8},
    {   'class': 'فصل 302',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 6.0,
        'name': 'عبد العزيز عبد المحسن بن بديع',
        'science': 0.0,
        'seq': 9},
    {   'class': 'فصل 302',
        'english': 4.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 7.0,
        'math': 7.0,
        'name': 'عبد الله متعب الجبرين',
        'science': 4.0,
        'seq': 10},
    {   'class': 'فصل 302',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 3.0,
        'name': 'عبد المحسن طارق العروان',
        'science': 4.0,
        'seq': 11},
    {   'class': 'فصل 302',
        'english': 5.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 5.0,
        'name': 'فارس وليد بن عبد الله الحوطي',
        'science': 4.0,
        'seq': 12},
    {   'class': 'فصل 302',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 5.0,
        'math': 5.0,
        'name': 'محمد خالد محمد بن مشرف',
        'science': 4.0,
        'seq': 13},
    {   'class': 'فصل 302',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'محمد سعد بن محمد العيشان',
        'science': 4.0,
        'seq': 14},
    {   'class': 'فصل 302',
        'english': 1.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 4.0,
        'math': 0.0,
        'name': 'محمد عبد العزيز محمد الخالدي',
        'science': 0.0,
        'seq': 15},
    {   'class': 'فصل 302',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 4.0,
        'math': 5.0,
        'name': 'مهند ماجد علي كعبي',
        'science': 5.0,
        'seq': 16},
    {   'class': 'فصل 302',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 4.0,
        'math': 3.0,
        'name': 'ناصر محمد عبد الله المزريعي',
        'science': 5.0,
        'seq': 17},
    {   'class': 'فصل 302',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 5.0,
        'math': 8.0,
        'name': 'نواف سعد بن علي القاسم',
        'science': 4.0,
        'seq': 18},
    {   'class': 'فصل 302',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 9.0,
        'name': 'ياسر تركي إسماعيل مسلمي',
        'science': 8.0,
        'seq': 19},
    {   'class': 'فصل 303',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 3.0,
        'name': 'ثامر وليد بن عبد العزيز الطليحي',
        'science': 2.0,
        'seq': 1},
    {   'class': 'فصل 303',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 5.0,
        'name': 'خالد بن عبد الرؤوف الشنير',
        'science': 4.0,
        'seq': 2},
    {   'class': 'فصل 303',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 5.0,
        'math': 7.0,
        'name': 'خالد عبد الله خالد الخالدي',
        'science': 4.0,
        'seq': 3},
    {   'class': 'فصل 303',
        'english': 4.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 5.0,
        'math': 3.0,
        'name': 'خالد محمد بن عبد الله ال درعان',
        'science': 5.0,
        'seq': 4},
    {   'class': 'فصل 303',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 4.0,
        'math': 4.0,
        'name': 'راشد صالح بن عبد العزيز الحلوان',
        'science': 4.0,
        'seq': 5},
    {   'class': 'فصل 303',
        'english': 5.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 5.0,
        'name': 'رواد محمد إبراهيم الخليل',
        'science': 3.0,
        'seq': 6},
    {   'class': 'فصل 303',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 0.0,
        'name': 'صالح بن محمد الميموني المطيري',
        'science': 4.0,
        'seq': 7},
    {   'class': 'فصل 303',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 3.0,
        'name': 'ضاري صالح مهنا العازمي',
        'science': 2.0,
        'seq': 8},
    {   'class': 'فصل 303',
        'english': 3.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 3.0,
        'name': 'عبد الرحمن بدر عبد الرحمن الطريقي',
        'science': 4.0,
        'seq': 9},
    {   'class': 'فصل 303',
        'english': 5.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 7.0,
        'math': 7.0,
        'name': 'عبد الرحمن خالد محمد سعيد',
        'science': 4.0,
        'seq': 10},
    {   'class': 'فصل 303',
        'english': 7.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 6.0,
        'name': 'عبد الله تركي عبد الله الأحمد',
        'science': 4.0,
        'seq': 11},
    {   'class': 'فصل 303',
        'english': 6.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 7.0,
        'math': 7.0,
        'name': 'عبد الله عبد الرحمن النجراني',
        'science': 3.0,
        'seq': 12},
    {   'class': 'فصل 303',
        'english': 7.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 3.0,
        'math': 4.0,
        'name': 'علي بن خالد بن علي العجيري',
        'science': 2.0,
        'seq': 13},
    {   'class': 'فصل 303',
        'english': 10.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 7.0,
        'math': 7.0,
        'name': 'علي عبد الله علي آل حمود',
        'science': 6.0,
        'seq': 14},
    {   'class': 'فصل 303',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 2.0,
        'name': 'فهد بن خالد بن فهد الزيد',
        'science': 3.0,
        'seq': 15},
    {   'class': 'فصل 303',
        'english': 2.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 4.0,
        'name': 'فيصل عبد الرحمن عزيز القحطاني',
        'science': 3.0,
        'seq': 16},
    {   'class': 'فصل 303',
        'english': 7.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'ماجد فهد عبد العزيز الكثيري',
        'science': 1.0,
        'seq': 17},
    {   'class': 'فصل 303',
        'english': 5.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 8.0,
        'math': 4.0,
        'name': 'مازن خالد عبد ربه الزهراني',
        'science': 4.0,
        'seq': 18},
    {   'class': 'فصل 303',
        'english': 0.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 0.0,
        'name': 'متعب مطر جمعان الدوسري',
        'science': 0.0,
        'seq': 19},
    {   'class': 'فصل 303',
        'english': 9.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 6.0,
        'math': 0.0,
        'name': 'نواف فهد بن ناصر القحطاني',
        'science': 8.0,
        'seq': 20},
    {   'class': 'فصل 303',
        'english': 4.0,
        'grade': 'الصف الثالث المتوسط',
        'lughati': 0.0,
        'math': 6.0,
        'name': 'يوسف عبد الله عوض العتيبي',
        'science': 3.0,
        'seq': 21}]
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
        SELECT id AS 'المعرف', test_name AS 'الاختبار', grade AS 'الصف الدراسي', class_name AS 'الفصل', seq_num AS 'المسلسل', student_name AS 'اسم الطالب', science AS 'علوم', math AS 'رياضيات', lughati AS 'لغتي', english AS 'انجليزي'
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
        SELECT id, seq_num AS 'المسلسل', student_name AS 'اسم الطالب', science AS 'علوم', math AS 'رياضيات', lughati AS 'لغتي', english AS 'انجليزي'
        FROM grades
        WHERE TRIM(test_name) = ? AND TRIM(grade) = ? AND TRIM(class_name) = ?
        ORDER BY seq_num ASC
    """, conn, params=[clean_t, clean_g, clean_c])
    
    if df.empty:
        g_short = clean_g.replace("الصف ", "").strip()
        c_short = clean_c.replace("فصل ", "").strip()
        df = pd.read_sql_query("""
            SELECT id, seq_num AS 'المسلسل', student_name AS 'اسم الطالب', science AS 'علوم', math AS 'رياضيات', lughati AS 'لغتي', english AS 'انجليزي'
            FROM grades
            WHERE (TRIM(test_name) = ? OR TRIM(test_name) LIKE ?)
              AND (TRIM(grade) = ? OR TRIM(grade) LIKE ?)
              AND (TRIM(class_name) = ? OR TRIM(class_name) LIKE ?)
            ORDER BY seq_num ASC
        """, conn, params=[clean_t, f"%{clean_t}%", clean_g, f"%{g_short}%", clean_c, f"%{c_short}%"])
        
    conn.close()
    return df

def update_student_scores(edited_df):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for _, row in edited_df.iterrows():
        c.execute('''
            UPDATE grades
            SET science = ?, math = ?, lughati = ?, english = ?
            WHERE id = ?
        ''', (row['علوم'], row['رياضيات'], row['لغتي'], row['انجليزي'], row['id']))
    conn.commit()
    conn.close()
    return sync_db_to_gsheets()
def save_new_student(test_name, grade_name, class_name, student_name, s, m, l, e):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT MAX(seq_num) FROM grades WHERE test_name = ? AND grade = ? AND class_name = ?', (test_name, grade_name, class_name))
    max_seq_res = c.fetchone()
    next_seq = ((max_seq_res[0] or 0) if max_seq_res and max_seq_res[0] else 0) + 1
    c.execute('''
        INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (test_name, grade_name, class_name, next_seq, student_name, s, m, l, e))
    conn.commit()
    conn.close()
    return sync_db_to_gsheets()
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
        st.warning(f"⚠️ لا توجد بيانات طلاب حالياً لـ ({selected_test}) - {selected_grade} - {selected_class}.")
        st.info("💡 قد تكون البيانات في قاعدة البيانات تضررت نتيجة سحب فارغ من Google Sheets.")
        if st.button("🔄 استعادة قاعدة بيانات جميع الفصول والطلاب (166 طالب)", type="primary"):
            init_db(force=True)
            st.success("تمت استعادة كافة بيانات الفصول والطلاب بنجاح!")
            st.rerun()
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

        c_btn1, c_btn2, c_btn3 = st.columns([4, 4, 3])
        with c_btn1:
            show_blank = st.checkbox("📝 عرض وطباعة كشف رصد فارغ (بدون درجات)", value=False)
        with c_btn2:
            table_print_orient = st.radio("📐 اتجاه طباعة التقرير:", ["عمودي (Portrait)", "أفقي (Landscape)"], index=0, horizontal=True)
        with c_btn3:
            if st.button("🖨️ طباعة تقرير الفصل (PDF / Print)", type="primary"):
                st.components.v1.html("""<script>setTimeout(function() { window.parent.print(); }, 200);</script>""", height=0)

        # تطبيق اتجاه الصفحة المختار لجدول التقارير عند الطباعة
        if "أفقي" in table_print_orient:
            st.markdown("""<style>
                @media print {
                    @page { size: A4 landscape !important; margin: 6mm !important; }
                    .custom-grade-table { font-size: 10pt !important; }
                }
            </style>""", unsafe_allow_html=True)
        else:
            st.markdown("""<style>
                @media print {
                    @page { size: A4 portrait !important; margin: 6mm !important; }
                    .custom-grade-table { font-size: 9pt !important; }
                }
            </style>""", unsafe_allow_html=True)

        st.markdown('<div class="no-print">✏️ <b>جدول الرصد المنظم والتعديل التفاعلي:</b></div>', unsafe_allow_html=True)

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
            st.success("تم الحفظ والمزامنة المزدوجة بنجاح!")
            st.rerun()

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown('<div class="no-print">📊 <b>عرض جدول الرصد المنسق بالكامل:</b></div>', unsafe_allow_html=True)

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
    # تضمين تنسيق إخفاء الترويسة والأدوات عند الطباعة وتحديد الاتجاه الأفقي
    st.markdown(""" 
    <style> 
    @media print { 
        @page {
            size: landscape; /* جعل اتجاه الطباعة أفقياً تلقائياً */
        }
        .main-header, .top-toolbar, header, [data-testid="stHeader"], [data-testid="stSidebar"], .stButton, .stSelectbox, .stMultiSelect { 
            display: none !important; 
        } 
    } 
    </style> 
    """, unsafe_allow_html=True)

    st.subheader(f"📈 التحليل البياني والمقارنة بين الفصول - {selected_test}")
    
    col_ch_print, col_ch_multi = st.columns([3, 4])
    
    with col_ch_multi:
        avail_classes = grades_map[selected_grade]
        selected_classes_compare = st.multiselect(
            "📚 اختر الفصول المراد المقارنة بينها:",
            avail_classes,
            default=avail_classes
        )
        
    with col_ch_print:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🖨️ طباعة الرسم البياني (PDF)", type="primary"):
            st.components.v1.html("""<script>
                setTimeout(function() { window.parent.print(); }, 300);
            </script>""", height=0)

    chart_shape = st.selectbox(
        "شكل الرسم البياني للمقارنة:",
        ["أعمدة بيانية متجاورة (Grouped Bar Chart)", "منحنى بياني متعدد (Multi-Line Chart)", "رادار الفصول (Radar Chart)"]
    )

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

        if df_comp.empty:
            st.info("لا توجد بيانات للفصول المختارة.")
        else:
            df_comp[['علوم', 'رياضيات', 'لغتي', 'انجليزي']] = df_comp[['علوم', 'رياضيات', 'لغتي', 'انجليزي']].round(2)
            df_melted = df_comp.melt(id_vars=['class_name'], var_name='المادة', value_name='متوسط الدرجة')

            if "أعمدة" in chart_shape:
                fig_comp = px.bar(
                    df_melted, x='class_name', y='متوسط الدرجة', color='المادة', barmode='group',
                    text='متوسط الدرجة',
                    title=f"مقارنة متوسط درجات المواد بين فصول {selected_grade}",
                    labels={'class_name': 'الفصل', 'متوسط الدرجة': 'متوسط الدرجة (من 10)'},
                    color_discrete_sequence=['#2563eb', '#ef4444', '#16a34a', '#6b7280']
                )
                fig_comp.update_traces(textposition='outside')
            elif "منحنى" in chart_shape:
                fig_comp = px.line(
                    df_melted, x='class_name', y='متوسط الدرجة', color='المادة', markers=True,
                    title=f"منحنى مقارنة أداء المواد بين فصول {selected_grade}",
                    labels={'class_name': 'الفصل', 'متوسط الدرجة': 'متوسط الدرجة (من 10)'},
                    color_discrete_sequence=['#2563eb', '#ef4444', '#16a34a', '#6b7280']
                )
            else:
                fig_comp = go.Figure()
                for c_name in selected_classes_compare:
                    c_data = df_melted[df_melted['class_name'] == c_name]
                    fig_comp.add_trace(go.Scatterpolar(
                        r=c_data['متوسط الدرجة'],
                        theta=c_data['المادة'],
                        fill='toself',
                        name=c_name
                    ))
                fig_comp.update_layout(title=f"مخطط رادار مقارنة الفصول - {selected_grade}", polar=dict(radialaxis=dict(visible=True, range=[5])))

            fig_comp.update_layout(font_family="Cairo", plot_bgcolor="white", margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_comp, use_container_width=True)
# ---------------------------------------------------------
# التبويب الثالث: التصدير والمزامنة المزدوجة
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# التبويب الرابع: إضافة طالب جديد
# ---------------------------------------------------------
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
                st.success(f"تمت إضافة الطالب ({add_s_name}) بنجاح ومزامنة بياناته!")
                st.rerun()
