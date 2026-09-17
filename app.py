import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sqlite3
import io

def clean_html(html_str):
    if not html_str:
        return ""
    lines = [line.strip() for line in html_str.strip().splitlines()]
    return "\n".join([line for line in lines if line])
def build_html_grade_table(df_data, is_blank=False):
    rows_html = ""
    for _, row in df_data.iterrows():
        seq = row['المسلسل']
        name = row['اسم الطالب']
        
        if is_blank:
            rows_html += f"""<tr>
                <td class="td-seq">{seq}</td>
                <td class="td-name">{name}</td>
                <td class="score-blank"></td><td class="score-blank"></td>
                <td class="score-blank"></td><td class="score-blank"></td>
                <td class="score-blank"></td><td class="score-blank"></td>
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
    
    return f"""<table class="custom-grade-table">
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
        <tbody>
            {rows_html}
        </tbody>
    </table>"""
# ---------------------------------------------------------
# 1. تهيئة الصفحة والنمط Visual Theme & Page Config
# ---------------------------------------------------------
st.set_page_config(
    page_title="نظام رصد الدرجات والرسوم البيانية - متوسطة الثغر النموذجية الأهلية",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تضمين التنسيقات الخواص بـ CSS والمستوحاة من التصميم الأصلي (بدون تعليقات CSS لضمان عدم ظهور أسطر نصية)
css_code = """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
    --gray-bg: #e5e7eb;
    --gray-text: #4b5563;
}
html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Cairo', sans-serif !important;
    direction: rtl !important;
    text-align: right !important;
}
.main-header {
    text-align: center;
    background: linear-gradient(135deg, #1e3a8a, #1e40af, #3b82f6);
    color: white;
    padding: 24px 20px;
    border-radius: 20px;
    margin-bottom: 20px;
    box-shadow: 0 10px 20px rgba(30, 58, 138, 0.15);
    position: relative;
    overflow: hidden;
}
.main-header h1 { margin: 0 0 8px 0; font-size: 26px; font-weight: 800; color: #ffffff; }
.main-header p { margin: 0 0 12px 0; opacity: 0.92; font-size: 15px; color: #e2e8f0; }
.designer-banner {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.4);
    padding: 6px 22px;
    border-radius: 50px;
    margin-top: 5px;
}
.designer-text { font-size: 16px; font-weight: 800; color: var(--gold); }
.designer-icon { font-size: 18px; color: var(--gold); }
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
    direction: rtl;
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
    direction: rtl;
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
.print-header-only { display: none; }
.custom-grade-table {
    width: 100%;
    border-collapse: collapse;
    direction: rtl !important;
    text-align: center;
    font-family: 'Cairo', sans-serif;
    margin-top: 15px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    border-radius: 12px;
    overflow: hidden;
}
.custom-grade-table th {
    padding: 12px 8px;
    color: white;
    font-weight: 800;
    font-size: 14px;
    border: 1px solid #cbd5e1;
    text-align: center;
}
.th-seq { background-color: #1e3a8a; width: 6%; }
.th-name { background-color: #1e3a8a; width: 30%; text-align: right !important; padding-right: 12px !important; }
.th-sci { background-color: #1e40af; width: 10%; }
.th-math { background-color: #2563eb; width: 10%; }
.th-lug { background-color: #3b82f6; width: 10%; }
.th-eng { background-color: #0284c7; width: 10%; }
.th-tot { background-color: #0f766e; width: 12%; }
.th-avg { background-color: #0369a1; width: 12%; }
.custom-grade-table td {
    padding: 9px 8px;
    border: 1px solid #cbd5e1;
    font-size: 14px;
    font-weight: 700;
    text-align: center;
}
.td-name { text-align: right !important; padding-right: 12px !important; color: #0f172a; font-weight: 800; }
.td-seq { text-align: center !important; color: #475569; background-color: #f8fafc; }
.score-green { background-color: #bbf7d0 !important; color: #166534 !important; font-weight: 800; }
.score-red { background-color: #fecaca !important; color: #991b1b !important; font-weight: 800; }
.score-zero { background-color: #e5e7eb !important; color: #64748b !important; }
.score-blank { background-color: #ffffff !important; color: #000000 !important; height: 32px; }
.excel-box {
    background-color: #f0fdf4;
    border: 2px dashed #16a34a;
    border-radius: 16px;
    padding: 20px;
    text-align: center;
    margin-bottom: 20px;
}
@media print {
    @page {
        size: A4 portrait;
        margin: 5mm 6mm;
    }
    [data-testid="stSidebar"], .stButton, button, header, footer, .no-print, div[role="tablist"], .top-toolbar, [data-testid="stHeader"], .color-legend, .stSelectbox, .stCheckbox, .stPopover, .stMultiSelect, .main-header {
        display: none !important;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stTabs"], div[role="tabpanel"], .main, .block-container {
        display: block !important;
        visibility: visible !important;
        background: white !important;
        color: black !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        zoom: 90% !important;
    }
    .print-header-only {
        display: block !important;
        text-align: center;
        margin-bottom: 6px;
        border-bottom: 2px solid #1e3a8a;
        padding-bottom: 4px;
    }
    .custom-grade-table {
        box-shadow: none !important;
        border: 1px solid #000 !important;
        width: 100% !important;
        margin-top: 4px !important;
        page-break-inside: avoid !important;
    }
    .custom-grade-table th {
        color: black !important;
        background-color: #e2e8f0 !important;
        border: 1px solid #000 !important;
        padding: 3px 2px !important;
        font-size: 9.5pt !important;
    }
    .custom-grade-table td {
        border: 1px solid #000 !important;
        color: black !important;
        padding: 2px 2px !important;
        font-size: 9.5pt !important;
        height: auto !important;
    }
}
</style>"""
st.markdown(clean_html(css_code), unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. قاعدة بيانات الطلاب الشاملة والمطابقة للمصدر والإكسل (167 طالب رسمياً)
# ---------------------------------------------------------
RAW_EXCEL_STUDENTS = [
  {
    "seq": 1,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "بلال عبد الرزاق عيسى العيسى",
    "science": 5.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 4.0
  },
  {
    "seq": 2,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "جاسر بن عبد الله بن منصور الحارثي",
    "science": 4.0,
    "math": 0.0,
    "lughati": 3.0,
    "english": 1.0
  },
  {
    "seq": 3,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "حسام بن محمد بن علي ال رايان البارقي",
    "science": 3.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 6.0
  },
  {
    "seq": 4,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "ريان عبد الله جابر الأسمري",
    "science": 4.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 3.0
  },
  {
    "seq": 5,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "زيد زياد عبد اللطيف أبو قبع",
    "science": 6.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 6.0
  },
  {
    "seq": 6,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "سامي سعد عباس حمد",
    "science": 3.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 5.0
  },
  {
    "seq": 7,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "سعد ناصر سعد السيف",
    "science": 3.0,
    "math": 0.0,
    "lughati": 2.0,
    "english": 4.0
  },
  {
    "seq": 8,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "عبد الله بن سليمان بن عبد الله الراجحي",
    "science": 0.0,
    "math": 0.0,
    "lughati": 7.0,
    "english": 0.0
  },
  {
    "seq": 9,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "عبد الله سعد بن محمد العيشان",
    "science": 0.0,
    "math": 0.0,
    "lughati": 7.0,
    "english": 0.0
  },
  {
    "seq": 10,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "علي أحمد علي كريري",
    "science": 4.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 2.0
  },
  {
    "seq": 11,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "علي سعد علي القحطاني",
    "science": 3.0,
    "math": 0.0,
    "lughati": 3.0,
    "english": 4.0
  },
  {
    "seq": 12,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "عمر عبد الله سعد الجبرين",
    "science": 2.0,
    "math": 0.0,
    "lughati": 1.0,
    "english": 4.0
  },
  {
    "seq": 13,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "مازن إسلام أحمد إبراهيم موسى",
    "science": 4.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 5.0
  },
  {
    "seq": 14,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "محمد أحمد علي عقيل",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 15,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "محمد إسلام محمد دراز",
    "science": 4.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 6.0
  },
  {
    "seq": 16,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "محمد أشرف مسعود أبو خاطر",
    "science": 4.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 6.0
  },
  {
    "seq": 17,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "محمد نايف فراج الدعجاني",
    "science": 0.0,
    "math": 0.0,
    "lughati": 3.0,
    "english": 0.0
  },
  {
    "seq": 18,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 101",
    "name": "وائل - - بولعيش",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 5.0
  },
  {
    "seq": 1,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "إبراهيم بن محمد بن علي الوهيبي",
    "science": 3.0,
    "math": 0.0,
    "lughati": 1.0,
    "english": 2.0
  },
  {
    "seq": 2,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "الوليد ابن خالد بن فهد العتيبي",
    "science": 5.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 9.0
  },
  {
    "seq": 3,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "باسل محمد فرج الدوسري",
    "science": 6.0,
    "math": 0.0,
    "lughati": 7.0,
    "english": 4.0
  },
  {
    "seq": 4,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "بسام بن عبد الكريم بن عبد الله الحرقان الدوسري",
    "science": 4.0,
    "math": 0.0,
    "lughati": 3.0,
    "english": 0.0
  },
  {
    "seq": 5,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "تركي عبد الله مسفر الدوسري",
    "science": 5.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 4.0
  },
  {
    "seq": 6,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "تميم فهد عبد العزيز العزاز",
    "science": 3.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 3.0
  },
  {
    "seq": 7,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "راكان عبد الله يحيى كريري",
    "science": 5.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 6.0
  },
  {
    "seq": 8,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "ريان عبد الله منصور السبر",
    "science": 7.0,
    "math": 0.0,
    "lughati": 9.0,
    "english": 6.0
  },
  {
    "seq": 9,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "ريان وليد - حلاق",
    "science": 4.0,
    "math": 0.0,
    "lughati": 3.0,
    "english": 0.0
  },
  {
    "seq": 10,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "سيف عبد الكريم بريك العصيمي",
    "science": 3.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 11,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "صالح حسن فتحي سندي",
    "science": 0.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 0.0
  },
  {
    "seq": 12,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "عبد الرحمن إبراهيم عبد الله الحضيف",
    "science": 4.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 5.0
  },
  {
    "seq": 13,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "عبد الله صالح حمد الصفيان",
    "science": 3.0,
    "math": 0.0,
    "lughati": 4.0,
    "english": 5.0
  },
  {
    "seq": 14,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "فهد ابن أحمد بن فهد العثمان",
    "science": 4.0,
    "math": 0.0,
    "lughati": 4.0,
    "english": 7.0
  },
  {
    "seq": 15,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "فهد عويض ثعيل المطيري",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 16,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "فهد نايف فهد الحسينان",
    "science": 2.0,
    "math": 0.0,
    "lughati": 4.0,
    "english": 3.0
  },
  {
    "seq": 17,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "فيصل موينع عبد الله بن موينع",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 18,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "فيصل ناصر سيف العريفي",
    "science": 6.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 6.0
  },
  {
    "seq": 19,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "مشاري عثمان سعد ناصر السعد",
    "science": 3.0,
    "math": 0.0,
    "lughati": 3.0,
    "english": 7.0
  },
  {
    "seq": 20,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "يزن محمد علي اليحيى",
    "science": 3.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 5.0
  },
  {
    "seq": 21,
    "grade": "الصف الأول المتوسط",
    "class": "فصل 102",
    "name": "يوسف محمد عبد الله الدوسري",
    "science": 4.0,
    "math": 0.0,
    "lughati": 2.0,
    "english": 4.0
  },
  {
    "seq": 1,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "إبراهيم ياسر إبراهيم الحلوى",
    "science": 4.0,
    "math": 3.0,
    "lughati": 6.0,
    "english": 5.0
  },
  {
    "seq": 2,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "أحمد سامي بن أحمد العمران",
    "science": 3.0,
    "math": 2.0,
    "lughati": 2.0,
    "english": 3.0
  },
  {
    "seq": 3,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "الوليد عبد الله بن إبراهيم المبدل",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 4,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "ذياب بن محمد بن ذياب بن محمد ال مريع القحطاني",
    "science": 0.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 0.0
  },
  {
    "seq": 5,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "راكان بن محمد بن مسفر القحطاني",
    "science": 5.0,
    "math": 3.0,
    "lughati": 2.0,
    "english": 0.0
  },
  {
    "seq": 6,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "سلطان عبد الله حسن القحطاني",
    "science": 3.0,
    "math": 2.0,
    "lughati": 0.0,
    "english": 2.0
  },
  {
    "seq": 7,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "عبد الرحمن حمد بن محمد العريفي",
    "science": 0.0,
    "math": 0.0,
    "lughati": 3.0,
    "english": 0.0
  },
  {
    "seq": 8,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "عبد الرحمن ربيع جابر خبراني",
    "science": 7.0,
    "math": 3.0,
    "lughati": 6.0,
    "english": 4.0
  },
  {
    "seq": 9,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "عبد العزيز سعود بن فهد العتيبي",
    "science": 4.0,
    "math": 3.0,
    "lughati": 3.0,
    "english": 3.0
  },
  {
    "seq": 10,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "عبد اللطيف إبراهيم محمد الطمره",
    "science": 2.0,
    "math": 2.0,
    "lughati": 5.0,
    "english": 3.0
  },
  {
    "seq": 11,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "فهد عيسى محمد العيسى",
    "science": 3.0,
    "math": 2.0,
    "lughati": 2.0,
    "english": 1.0
  },
  {
    "seq": 12,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "فيصل بن عبد الله بن سعود بن عبد العزيز الجميهه",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 13,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "مبارك صالح مبارك هليل",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 14,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "محمد بن عبد الله بن حمد بن ناصر بن عمران",
    "science": 2.0,
    "math": 0.0,
    "lughati": 2.0,
    "english": 3.0
  },
  {
    "seq": 15,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "محمد عبد المحسن ناصر الحزام",
    "science": 7.0,
    "math": 7.0,
    "lughati": 3.0,
    "english": 5.0
  },
  {
    "seq": 16,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "محمد فايز عبد الرحمن بن يوسف",
    "science": 6.0,
    "math": 2.0,
    "lughati": 5.0,
    "english": 0.0
  },
  {
    "seq": 17,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "مشاري سلطان سالم الشمراني",
    "science": 3.0,
    "math": 4.0,
    "lughati": 2.0,
    "english": 6.0
  },
  {
    "seq": 18,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "معاذ عبد الله سعود العريفي",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 19,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "ناصر حسين محمد ال جبران",
    "science": 0.0,
    "math": 3.0,
    "lughati": 4.0,
    "english": 0.0
  },
  {
    "seq": 20,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 201",
    "name": "يزيد بن طارق بن علي الحديثي",
    "science": 0.0,
    "math": 2.0,
    "lughati": 3.0,
    "english": 3.0
  },
  {
    "seq": 1,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "إبراهيم بن مبارك بن راشد بن عبد الرحمن السبيعي آل موينع",
    "science": 5.0,
    "math": 6.0,
    "lughati": 3.0,
    "english": 10.0
  },
  {
    "seq": 2,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "حامد بن محمد بن حامد شباط",
    "science": 3.0,
    "math": 3.0,
    "lughati": 2.0,
    "english": 2.0
  },
  {
    "seq": 3,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "حسام حسن محمد الشهري",
    "science": 6.0,
    "math": 4.0,
    "lughati": 4.0,
    "english": 5.0
  },
  {
    "seq": 4,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "خالد تركي عايض القحطاني",
    "science": 3.0,
    "math": 2.0,
    "lughati": 5.0,
    "english": 2.0
  },
  {
    "seq": 5,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "خالد داود بن عابد الحارثي",
    "science": 0.0,
    "math": 0.0,
    "lughati": 4.0,
    "english": 2.0
  },
  {
    "seq": 6,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "سطام عبد العزيز عبد الله العريفي",
    "science": 0.0,
    "math": 2.0,
    "lughati": 2.0,
    "english": 1.0
  },
  {
    "seq": 7,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "سعود خالد عبد الله الحمد",
    "science": 6.0,
    "math": 5.0,
    "lughati": 3.0,
    "english": 2.0
  },
  {
    "seq": 8,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "سعود سلطان بن خليل العتيبي",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 9,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "سعود مشعل بن إبراهيم الشثري",
    "science": 3.0,
    "math": 2.0,
    "lughati": 2.0,
    "english": 10.0
  },
  {
    "seq": 10,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "طلال محمد منير المهدرس",
    "science": 5.0,
    "math": 4.0,
    "lughati": 3.0,
    "english": 2.0
  },
  {
    "seq": 11,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "عبد الكريم مساعد عبد العزيز الهزاع",
    "science": 1.0,
    "math": 3.0,
    "lughati": 1.0,
    "english": 1.0
  },
  {
    "seq": 12,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "عبد الله سامي سعد الحوشاني",
    "science": 3.0,
    "math": 5.0,
    "lughati": 1.0,
    "english": 4.0
  },
  {
    "seq": 13,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "علي أحمد علي عقيل",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 14,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "عمر بن سعد بن هلال الشبانات",
    "science": 2.0,
    "math": 3.0,
    "lughati": 2.0,
    "english": 0.0
  },
  {
    "seq": 15,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "عمر خالد عبد الله المهيني",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 16,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "فارس مشعل عبد الله بن موينع",
    "science": 4.0,
    "math": 3.0,
    "lughati": 2.0,
    "english": 4.0
  },
  {
    "seq": 17,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "مازن خالد دخيل المطيري",
    "science": 0.0,
    "math": 2.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 18,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "مازن رفعت محمد حاج النيل",
    "science": 4.0,
    "math": 5.0,
    "lughati": 4.0,
    "english": 5.0
  },
  {
    "seq": 19,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "نايف بن بندر بن خلفان العلوي",
    "science": 0.0,
    "math": 2.0,
    "lughati": 3.0,
    "english": 0.0
  },
  {
    "seq": 20,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "نواف عبد العزيز المرزوق",
    "science": 6.0,
    "math": 3.0,
    "lughati": 0.0,
    "english": 5.0
  },
  {
    "seq": 21,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "هادي سلطان هادي القحطاني",
    "science": 1.0,
    "math": 2.0,
    "lughati": 2.0,
    "english": 1.0
  },
  {
    "seq": 22,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 202",
    "name": "يزيد بن حسين بن متعب بن محمد كعكم",
    "science": 0.0,
    "math": 0.0,
    "lughati": 4.0,
    "english": 0.0
  },
  {
    "seq": 1,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "ثامر عمر إبراهيم عثمان",
    "science": 3.0,
    "math": 4.0,
    "lughati": 7.0,
    "english": 6.0
  },
  {
    "seq": 2,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "جهاد فارس عبد القادر حتاوي",
    "science": 2.0,
    "math": 2.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 3,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "خالد محمد عبد الكريم الخفاجي",
    "science": 4.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 4,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "سعد ابن مسفر بن سعد القحطاني",
    "science": 5.0,
    "math": 2.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 5,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "سعود بن عبد الله بن سعود السحامي",
    "science": 4.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 2.0
  },
  {
    "seq": 6,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "سعود ناصر سنيف العريفي",
    "science": 4.0,
    "math": 6.0,
    "lughati": 6.0,
    "english": 8.0
  },
  {
    "seq": 7,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "سعيد محمد - باوزير",
    "science": 0.0,
    "math": 2.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 8,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "طلال بن فهد بن عطيه بالحكم الزهراني",
    "science": 7.0,
    "math": 3.0,
    "lughati": 7.0,
    "english": 6.0
  },
  {
    "seq": 9,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عبد الرحمن أحمد جاسم الحمدي",
    "science": 4.0,
    "math": 5.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 10,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عبد العزيز ماجد راشد الزير",
    "science": 5.0,
    "math": 2.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 11,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عبد العزيز وليد ناصر بن سعران",
    "science": 4.0,
    "math": 1.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 12,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عبد الله بن بندر بن فهد المفيجل",
    "science": 5.0,
    "math": 2.0,
    "lughati": 5.0,
    "english": 2.0
  },
  {
    "seq": 13,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عبد المجيد بن محمد بن مسعود آل عايض القحطاني",
    "science": 4.0,
    "math": 8.0,
    "lughati": 7.0,
    "english": 9.0
  },
  {
    "seq": 14,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عز الدين أحمد محمد سعد",
    "science": 3.0,
    "math": 5.0,
    "lughati": 0.0,
    "english": 6.0
  },
  {
    "seq": 15,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عزام خالد شهوب بن شهوب",
    "science": 4.0,
    "math": 2.0,
    "lughati": 5.0,
    "english": 4.0
  },
  {
    "seq": 16,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عزام فهد أحمد صلوي",
    "science": 2.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 17,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "عمر وليد ياسين درويش علي",
    "science": 4.0,
    "math": 5.0,
    "lughati": 0.0,
    "english": 4.0
  },
  {
    "seq": 18,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "فارس ابن محمد بن سالم بن نويشي الوهبي الحربي",
    "science": 3.0,
    "math": 3.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 19,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "محمد بن علي محسن العثيميني",
    "science": 1.0,
    "math": 3.0,
    "lughati": 4.0,
    "english": 0.0
  },
  {
    "seq": 20,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "وائل بن عبد الله بن عامر علي آل عبيد الغامدي",
    "science": 1.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 4.0
  },
  {
    "seq": 21,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "يزيد بن حمد بن مترك بن محمد ال مسعود القحطاني",
    "science": 2.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 22,
    "grade": "الصف الثاني المتوسط",
    "class": "فصل 203",
    "name": "يوسف عايد عواد البلوي",
    "science": 8.0,
    "math": 6.0,
    "lughati": 6.0,
    "english": 7.0
  },
  {
    "seq": 1,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "أصيل ناصر بن محمد مذكور",
    "science": 3.0,
    "math": 3.0,
    "lughati": 0.0,
    "english": 2.0
  },
  {
    "seq": 2,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "خالد محمد مسعف معافا",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 6.0
  },
  {
    "seq": 3,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "راشد سعيد راشد عبد السلام",
    "science": 4.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 8.0
  },
  {
    "seq": 4,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "راكان بن عبد الله بن سالم اليافعي",
    "science": 4.0,
    "math": 7.0,
    "lughati": 6.0,
    "english": 3.0
  },
  {
    "seq": 5,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "زياد أحمد بن علي اللحيد",
    "science": 3.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 1.0
  },
  {
    "seq": 6,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "سطام محمد سعود الدوسري",
    "science": 5.0,
    "math": 5.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 7,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "سلطان أحمد صالح الفتوح",
    "science": 6.0,
    "math": 4.0,
    "lughati": 6.0,
    "english": 6.0
  },
  {
    "seq": 8,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "عبد العزيز عبد الله شراز المالكي",
    "science": 5.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 6.0
  },
  {
    "seq": 9,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "عبد العزيز عبد الله عايض الأسمري",
    "science": 5.0,
    "math": 6.0,
    "lughati": 7.0,
    "english": 5.0
  },
  {
    "seq": 10,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "عبد الله عبيد عبد الله العتيبي",
    "science": 2.0,
    "math": 4.0,
    "lughati": 4.0,
    "english": 2.0
  },
  {
    "seq": 11,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "عبد الله فهد جلوي سالم الشرعي",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 12,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "علي إبراهيم علي الأسمري",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 13,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "عماد الدين إسلام محمد دراز",
    "science": 0.0,
    "math": 7.0,
    "lughati": 0.0,
    "english": 6.0
  },
  {
    "seq": 14,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "عمر فهد محمد السقامي",
    "science": 4.0,
    "math": 2.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 15,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "فهد عبد الرحمن فهد العتيبي",
    "science": 3.0,
    "math": 0.0,
    "lughati": 5.0,
    "english": 0.0
  },
  {
    "seq": 16,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "فيصل بن عبد الرحمن بن عايض العصيمي العتيبي",
    "science": 5.0,
    "math": 9.0,
    "lughati": 0.0,
    "english": 6.0
  },
  {
    "seq": 17,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "فيصل محمد صالح الفتوح",
    "science": 5.0,
    "math": 7.0,
    "lughati": 7.0,
    "english": 4.0
  },
  {
    "seq": 18,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "محمد سلطان عبد العزيز العيد",
    "science": 4.0,
    "math": 5.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 19,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "محمد مقعد ساير العتيبي",
    "science": 5.0,
    "math": 6.0,
    "lughati": 6.0,
    "english": 6.0
  },
  {
    "seq": 20,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "مشاري إبراهيم عبد اللطيف المغربي",
    "science": 0.0,
    "math": 4.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 21,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "مشاري علي موسى عقيلي",
    "science": 4.0,
    "math": 6.0,
    "lughati": 0.0,
    "english": 4.0
  },
  {
    "seq": 22,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "مهند عبد الله فهد الزكري",
    "science": 6.0,
    "math": 4.0,
    "lughati": 7.0,
    "english": 6.0
  },
  {
    "seq": 23,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "نواف وليد حمد الشعلان",
    "science": 5.0,
    "math": 6.0,
    "lughati": 5.0,
    "english": 5.0
  },
  {
    "seq": 24,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 301",
    "name": "يوسف نايف مقعد العتيبي",
    "science": 5.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 6.0
  },
  {
    "seq": 1,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "تركي عبد العزيز عبد الله المرزوق",
    "science": 4.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 2,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "تركي عثمان عبد العزيز العثمان",
    "science": 4.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 3,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "راشد أحمد فهد آل سعيد",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 2.0
  },
  {
    "seq": 4,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "راكان إبراهيم محمد ديوان",
    "science": 4.0,
    "math": 3.0,
    "lughati": 4.0,
    "english": 2.0
  },
  {
    "seq": 5,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "ريان ناصر عبد الرحمن المرشود",
    "science": 4.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 6,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "صالح بن ممدوح بن صالح بن خالد الجويعي",
    "science": 3.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 7,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "عبد الرحمن محمد صلاح بدر الدين",
    "science": 6.0,
    "math": 4.0,
    "lughati": 6.0,
    "english": 6.0
  },
  {
    "seq": 8,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "عبد العزيز تركي عبد العزيز اللهيم",
    "science": 2.0,
    "math": 4.0,
    "lughati": 6.0,
    "english": 5.0
  },
  {
    "seq": 9,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "عبد العزيز عبد المحسن فهد بن بديع",
    "science": 0.0,
    "math": 6.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 10,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "عبد الله متعب بن عبد الرحمن الجبرين",
    "science": 4.0,
    "math": 7.0,
    "lughati": 7.0,
    "english": 4.0
  },
  {
    "seq": 11,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "عبد المحسن طارق بن عبد الرحمن العروان",
    "science": 4.0,
    "math": 3.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 12,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "فارس وليد بن عبد الله الحوطي",
    "science": 4.0,
    "math": 5.0,
    "lughati": 6.0,
    "english": 5.0
  },
  {
    "seq": 13,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "محمد خالد محمد بن مشرف",
    "science": 4.0,
    "math": 5.0,
    "lughati": 5.0,
    "english": 3.0
  },
  {
    "seq": 14,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "محمد سعد بن محمد العيشان",
    "science": 4.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 2.0
  },
  {
    "seq": 15,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "محمد عبد العزيز محمد الخالدي",
    "science": 0.0,
    "math": 0.0,
    "lughati": 4.0,
    "english": 1.0
  },
  {
    "seq": 16,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "مهند ماجد علي كعبي",
    "science": 5.0,
    "math": 5.0,
    "lughati": 4.0,
    "english": 2.0
  },
  {
    "seq": 17,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "ناصر محمد عبد الله المزريعي",
    "science": 5.0,
    "math": 3.0,
    "lughati": 4.0,
    "english": 2.0
  },
  {
    "seq": 18,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "نواف سعد بن علي القاسم",
    "science": 4.0,
    "math": 8.0,
    "lughati": 5.0,
    "english": 0.0
  },
  {
    "seq": 19,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 302",
    "name": "ياسر تركي إسماعيل مسلمي",
    "science": 8.0,
    "math": 9.0,
    "lughati": 6.0,
    "english": 6.0
  },
  {
    "seq": 1,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "ثامر وليد بن عبد العزيز الطليحي",
    "science": 2.0,
    "math": 3.0,
    "lughati": 0.0,
    "english": 2.0
  },
  {
    "seq": 2,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "خالد بن عبد الرؤوف بن عبد الرحمن بن عبد الله الشنير",
    "science": 4.0,
    "math": 5.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 3,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "خالد عبد الله خالد الخالدي",
    "science": 4.0,
    "math": 7.0,
    "lughati": 5.0,
    "english": 3.0
  },
  {
    "seq": 4,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "خالد محمد بن عبد الله ال درعان",
    "science": 5.0,
    "math": 3.0,
    "lughati": 5.0,
    "english": 4.0
  },
  {
    "seq": 5,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "راشد صالح بن عبد العزيز الحلوان",
    "science": 4.0,
    "math": 4.0,
    "lughati": 4.0,
    "english": 3.0
  },
  {
    "seq": 6,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "رواد محمد إبراهيم الخليل",
    "science": 3.0,
    "math": 5.0,
    "lughati": 6.0,
    "english": 5.0
  },
  {
    "seq": 7,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "صالح بن محمد بن صالح الميموني المطيري",
    "science": 4.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 3.0
  },
  {
    "seq": 8,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "ضاري صالح مهنا العازمي",
    "science": 2.0,
    "math": 3.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 9,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "عبد الرحمن بدر عبد الرحمن الطريقي",
    "science": 4.0,
    "math": 3.0,
    "lughati": 0.0,
    "english": 3.0
  },
  {
    "seq": 10,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "عبد الرحمن خالد محمد سعيد",
    "science": 4.0,
    "math": 7.0,
    "lughati": 7.0,
    "english": 5.0
  },
  {
    "seq": 11,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "عبد الله تركي عبد الله الأحمد",
    "science": 4.0,
    "math": 6.0,
    "lughati": 0.0,
    "english": 7.0
  },
  {
    "seq": 12,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "عبد الله عبد الرحمن عبد الله النجراني",
    "science": 3.0,
    "math": 7.0,
    "lughati": 7.0,
    "english": 6.0
  },
  {
    "seq": 13,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "علي بن خالد بن علي العجيري",
    "science": 2.0,
    "math": 4.0,
    "lughati": 3.0,
    "english": 7.0
  },
  {
    "seq": 14,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "علي عبد الله علي آل حمود",
    "science": 6.0,
    "math": 7.0,
    "lughati": 7.0,
    "english": 10.0
  },
  {
    "seq": 15,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "فهد بن خالد بن فهد بن عبد العزيز الزيد",
    "science": 3.0,
    "math": 2.0,
    "lughati": 6.0,
    "english": 2.0
  },
  {
    "seq": 16,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "فيصل عبد الرحمن عزيز القحطاني",
    "science": 3.0,
    "math": 4.0,
    "lughati": 0.0,
    "english": 2.0
  },
  {
    "seq": 17,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "ماجد فهد عبد العزيز الكثيري",
    "science": 1.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 7.0
  },
  {
    "seq": 18,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "مازن خالد عبد ربه الزهراني",
    "science": 4.0,
    "math": 4.0,
    "lughati": 8.0,
    "english": 5.0
  },
  {
    "seq": 19,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "متعب مطر جمعان الدوسري",
    "science": 0.0,
    "math": 0.0,
    "lughati": 0.0,
    "english": 0.0
  },
  {
    "seq": 20,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "نواف فهد بن ناصر القحطاني",
    "science": 8.0,
    "math": 0.0,
    "lughati": 6.0,
    "english": 9.0
  },
  {
    "seq": 21,
    "grade": "الصف الثالث المتوسط",
    "class": "فصل 303",
    "name": "يوسف عبد الله عوض العتيبي",
    "science": 3.0,
    "math": 6.0,
    "lughati": 0.0,
    "english": 4.0
  }
]

TESTS_LIST = [
    "الاختبار التشخيصي الأول",
    "الاختبار التشخيصي الثاني",
    "الاختبار التشخيصي الثالث",
    "الاختبار التشخيصي الرابع"
]

# ---------------------------------------------------------
# 3. إدارة قاعدة البيانات / Database Manager
# ---------------------------------------------------------
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
            initial_rows.append((
                "الاختبار التشخيصي الأول",
                rec["grade"],
                rec["class"],
                rec["seq"],
                rec["name"],
                rec["science"],
                rec["math"],
                rec["lughati"],
                rec["english"]
            ))
            
            for t in ["الاختبار التشخيصي الثاني", "الاختبار التشخيصي الثالث", "الاختبار التشخيصي الرابع"]:
                initial_rows.append((
                    t,
                    rec["grade"],
                    rec["class"],
                    rec["seq"],
                    rec["name"],
                    0.0, 0.0, 0.0, 0.0
                ))
                
        c.executemany("""
            INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, initial_rows)
        conn.commit()
    conn.close()

def load_class_students(test_name, grade_name, class_name):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT id, seq_num AS 'المسلسل', student_name AS 'اسم الطالب',
               science AS 'علوم', math AS 'رياضيات', lughati AS 'لغتي', english AS 'انجليزي'
        FROM grades
        WHERE test_name = ? AND grade = ? AND class_name = ?
        ORDER BY seq_num ASC
    """, conn, params=(test_name, grade_name, class_name))
    conn.close()
    return df


def delete_student_by_id(student_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM grades WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()

def delete_student_all_tests(student_name, grade_name, class_name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM grades WHERE student_name = ? AND grade = ? AND class_name = ?", (student_name, grade_name, class_name))
    conn.commit()
    conn.close()
    
def update_student_scores(df_updated):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for _, row in df_updated.iterrows():
        c.execute("""
            UPDATE grades SET science = ?, math = ?, lughati = ?, english = ? WHERE id = ?
        """, (row['علوم'], row['رياضيات'], row['لغتي'], row['انجليزي'], row['id']))
    conn.commit()
    conn.close()
    
def update_student_scores(df_updated):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for _, row in df_updated.iterrows():
        c.execute("""
            UPDATE grades
            SET science = ?, math = ?, lughati = ?, english = ?
            WHERE id = ?
        """, (row['علوم'], row['رياضيات'], row['لغتي'], row['انجليزي'], row['id']))
    conn.commit()
    conn.close()

def load_all_db_records():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("""
        SELECT id AS 'المعرف', test_name AS 'الاختبار', grade AS 'الصف الدراسي',
               class_name AS 'الفصل', seq_num AS 'المسلسل', student_name AS 'اسم الطالب',
               science AS 'علوم', math AS 'رياضيات', lughati AS 'لغتي', english AS 'انجليزي'
        FROM grades
    """, conn)
    conn.close()
    return df

def save_new_student(test_name, grade_name, class_name, student_name, s, m, l, e):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT MAX(seq_num) FROM grades WHERE test_name = ? AND grade = ? AND class_name = ?", (test_name, grade_name, class_name))
    max_seq_res = c.fetchone()
    next_seq = ((max_seq_res[0] or 0) if max_seq_res else 0) + 1
    
    c.execute("""
        INSERT INTO grades (test_name, grade, class_name, seq_num, student_name, science, math, lughati, english)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (test_name, grade_name, class_name, next_seq, student_name, s, m, l, e))
    conn.commit()
    conn.close()

def export_to_excel_bytes(df_export):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='درجات المواد الأربع')
    output.seek(0)
    return output

init_db()
 =========================================================
# 1. القوائم المنسدلة المتسلسلة (اختبار -> صف -> فصل)
# (يجب وضعها في البداية لتعريف المتغيرات أولاً)
# =========================================================
col_t, col_g, col_c = st.columns(3)

with col_t:
    selected_test = st.selectbox("📌 1. اختر الاختبار التشخيصي:", TESTS_LIST, index=0)

grades_map = {
    "الصف الأول المتوسط": ["فصل 101", "فصل 102"],
    "الصف الثاني المتوسط": ["فصل 201", "فصل 202", "فصل 203"],
    "الصف الثالث المتوسط": ["فصل 301", "فصل 302", "فصل 303"],
}

with col_g:
    selected_grade = st.selectbox("🏫 2. اختر الصف الدراسي:", list(grades_map.keys()), index=0)

with col_c:
    selected_class = st.selectbox("📚 3. اختر الفصل:", grades_map[selected_grade], index=0)


# =========================================================
# 2. تحميل البيانات والتحقق منها وعرض الترويسة والجدول
# =========================================================
df_students = load_class_students(selected_test, selected_grade, selected_class)

if df_students.empty:
    st.warning("لا توجد بيانات طلاب لهذا الفصل في هذا الاختبار.")
else:
    # عرض الترويسة الهيكلية المخصصة للطباعة
    print_header_html = f"""<div class="print-header-only">
        <h2 style="margin:0; color:#1e3a8a; font-size:16px;">المملكة العربية السعودية - وزارة التعليم</h2>
        <h3 style="margin:2px 0; color:#1e3a8a; font-size:14px;">متوسطة الثغر النموذجية الأهلية بالرياض</h3>
        <p style="margin:2px 0; font-size:13px; font-weight:800;">سجل رصد درجات: {selected_test} | {selected_grade} - {selected_class}</p>
    </div>"""
    
    st.markdown(clean_html(print_header_html), unsafe_allow_html=True)
    
    # بناء واستدراج جدول الرصد المنسق
    table_html = build_html_grade_table(df_students, is_blank=show_blank)
    st.markdown(clean_html(table_html), unsafe_allow_html=True)
# ---------------------------------------------------------
# 6. التبويبات الرئيسية Tabs
# ---------------------------------------------------------
tab_entry, tab_charts, tab_excel, tab_add = st.tabs([
    "📋 رصد درجات الفصل والطباعة",
    "📈 الرسم البياني والمقارنة بين الفصول",
    "🟢 استيراد وتصدير Excel",
    "➕ إضافة طالب جديد"
])

# =========================================================
# التبويب الأول: رصد درجات الفصل والطباعة المنسقة
# =========================================================
with tab_entry:
    st.subheader(f"📋 سجل درجات الطلاب: ({selected_test}) - {selected_grade} - {selected_class}")
    
    df_students = load_class_students(selected_test, selected_grade, selected_class)
    
    if df_students.empty:
        st.warning("لا توجد بيانات طلاب لهذا الفصل في هذا الاختبار.")
    else:
        # 1. دليل التنسيق الشرطي
        legend_html = """<div class="color-legend">
            <span style="font-weight:800; color:#1e3a8a;">🎨 دليل التنسيق الشرطي للدرجات:</span>
            <div class="legend-item"><div class="color-box" style="background:#bbf7d0;"></div><span>درجة ≥ 5.0 (أخضر فاتح - إتقان)</span></div>
            <div class="legend-item"><div class="color-box" style="background:#fecaca;"></div><span>درجة < 5.0 (أحمر فاتح - دون الإتقان)</span></div>
            <div class="legend-item"><div class="color-box" style="background:#e5e7eb;"></div><span>بدون درجة / 0 (رصاصي فاتح - خالية)</span></div>
        </div>"""
        st.markdown(clean_html(legend_html), unsafe_allow_html=True)

        # 2. أزرار الطباعة والعرض
        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            show_blank = st.checkbox("📝 عرض وطباعة كشف رصد فارغ (بدون درجات للتصحيح الورقي)", value=False)
        with c_btn2:
            if st.button("🖨️ طباعة تقرير الفصل (PDF / Print)", type="primary"):
                st.components.v1.html("""<script>setTimeout(function() { window.parent.print(); }, 300);</script>""", height=0)

        st.write("✏️ **جدول الرصد المنظم والتعديل التفاعلي:**")

        # 3. محرر الجدول التفاعلي
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

        # 4. أزرار الحفظ والحذف
        col_s_btn, col_del_btn = st.columns(2)
        with col_s_btn:
            if st.button("💾 حفظ التعديلات في قاعدة البيانات", type="secondary"):
                update_student_scores(edited_df)
                st.success("تم حفظ درجات جميع المواد دائمياً بنجاح!")
                st.rerun()

        with col_del_btn:
            with st.popover("🗑️ حذف طالب من الفصل"):
                st.write("**حذف طالب من الكشف:**")
                student_to_del = st.selectbox("اختر الطالب المراد حذفه:", df_students['اسم الطالب'].tolist(), key=f"del_sel_{selected_test}_{selected_class}")
                del_mode = st.radio("نطاق الحذف:", ["حذف من هذا الاختبار فقط", "حذف نهائي من جميع الاختبارات"], key=f"del_mode_{selected_test}_{selected_class}")
                if st.button("❌ تأكيد حذف الطالب", type="primary", key=f"del_confirm_{selected_test}_{selected_class}"):
                    if "نهائي" in del_mode:
                        delete_student_all_tests(student_to_del, selected_grade, selected_class)
                        st.success(f"تم حذف الطالب ({student_to_del}) نهائياً من كافة الاختبارات!")
                    else:
                        st_id = df_students[df_students['اسم الطالب'] == student_to_del]['id'].values
                        delete_student_by_id(st_id)
                        st.success(f"تم حذف الطالب ({student_to_del}) من {selected_test}!")
                    st.rerun()

        # 5. طباعة سجل الدرجات ورأس الصفحة المنسق
        st.markdown("<hr>", unsafe_allow_html=True)
        st.write("📊 **عرض جدول الرصد المنسق بالكامل:**")

        print_header_html = f"""<div class="print-header-only">
            <h2 style="margin:0; color:#1e3a8a; font-size:16px;">المملكة العربية السعودية - وزارة التعليم</h2>
            <h3 style="margin:2px 0; color:#1e3a8a; font-size:14px;">متوسطة الثغر النموذجية الأهلية بالرياض</h3>
            <p style="margin:2px 0; font-size:13px; font-weight:800;">سجل رصد درجات: {selected_test} | {selected_grade} - {selected_class}</p>
        </div>"""
        st.markdown(clean_html(print_header_html), unsafe_allow_html=True)
        table_html = build_html_grade_table(df_students, is_blank=show_blank)
        st.markdown(clean_html(table_html), unsafe_allow_html=True)
# =========================================================
# التبويب الثاني: الرسم البياني والمقارنة بين عدة فصول
# =========================================================
with tab_charts:
    st.subheader(f"📈 التحليل البياني والمقارنة بين الفصول - {selected_test}")
    
    col_ch_print, col_ch_multi = st.columns([1, 3])
    
    with col_ch_multi:
        avail_classes = grades_map[selected_grade]
        selected_classes_compare = st.multiselect(
            "📚 اختر الفصول المراد المقارنة بينها:",
            avail_classes,
            default=avail_classes
        )
        
        with col_ch_print:
                st.markdown("<br>", unsafe_allow_html=True)
    
    # 💡 إضافة نمط CSS لتوجيه الصفحة للطباعة بشكل عرضي (Landscape)
                st.markdown("""
                <style>
                @media print {
            @page {
                size: landscape;
                    }
                }
                </style>
            """, unsafe_allow_html=True)

    if st.button("🖨️ طباعة الرسم البياني (PDF)", type="primary"):
        st.components.v1.html("""<script>
            setTimeout(function() { window.parent.print(); }, 460);
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
                    color_discrete_sequence=['red', 'blue', 'green', 'gray']
                )
                fig_comp.update_traces(textposition='outside')
            elif "منحنى" in chart_shape:
                fig_comp = px.line(
                    df_melted, x='class_name', y='متوسط الدرجة', color='المادة', markers=True,
                    title=f"منحنى مقارنة أداء المواد بين فصول {selected_grade}",
                    labels={'class_name': 'الفصل', 'متوسط الدرجة': 'متوسط الدرجة (من 10)'},
                    color_discrete_sequence=['#1e40af', '#2563eb', '#3b82f6', '#0284c7']
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
                fig_comp.update_layout(title=f"مخطط رادار مقارنة الفصول - {selected_grade}", polar=dict(radialaxis=dict(visible=True, range=[0, 10])))

            fig_comp.update_layout(font_family="Cairo", plot_bgcolor="white", margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_comp, use_container_width=True)

# =========================================================
# التبويب الثالث: استيراد وتصدير ملفات Excel
# =========================================================
with tab_excel:
    st.subheader("🟢 استيراد وتصدير كافة السجلات عبر Excel")
    
    col_exp_box, col_info_box = st.columns(2)
    
    with col_exp_box:
        box_html = """<div class="excel-box">
            <h4 style="color:#16a34a; margin-top:0;"><i class="fa-solid fa-file-excel"></i> تصدير جميع درجات المواد</h4>
            <p style="font-size:13px; color:#4b5563;">تحميل قاعدة بيانات كافة الصفوف والفصول والمواد الأربع في ملف Excel واحد منسق.</p>
        </div>"""
        st.markdown(clean_html(box_html), unsafe_allow_html=True)
        
        df_all_export = load_all_db_records()
        excel_data = export_to_excel_bytes(df_all_export)
        
        st.download_button(
            label="📥 تحميل كافة البيانات كملف Excel (.xlsx)",
            data=excel_data,
            file_name="درجات_المواد_الأربع_شامل.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

# =========================================================
# التبويب الرابع: إضافة طالب جديد
# =========================================================
with tab_add:
    st.subheader("➕ إضافة طالب جديد ورصد درجات المواد له")
    
    with st.form("add_student_v12_form", clear_on_submit=True):
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
                st.success(f"تمت إضافة الطالب ({add_s_name}) بنجاح إلى {add_c}!")
                st.rerun()
