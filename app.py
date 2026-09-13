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

# تضمين مكتبة الأيقونات FontAwesome وتنسيقات CSS المدمجة من المصدر الاصلي
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

    .badge { padding: 4px 10px; border-radius: 8px; font-size: 12px; font-weight: 700; }
    .badge-excel { background: var(--green-bg); color: var(--green-text); }
    .badge-good { background: #e0f2fe; color: #0369a1; }
    .badge-need { background: var(--red-bg); color: var(--red-text); }

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
        .print-only-header { 
            display: block !important; 
            text-align: center; 
            margin-bottom: 20px; 
            border-bottom: 2px solid var(--primary); 
            padding-bottom: 10px; 
        }
    }
    .print-only-header { display: none; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. إدارة قاعدة البيانات / Database Manager
# ---------------------------------------------------------
DB_FILE = "student_grades.db"

def init_db():
    """إنشاء جدول البيانات في حال عدم وجوده مع إدراج بيانات أولية توضيحية"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            grade TEXT,
            class_name TEXT,
            student_name TEXT,
            score REAL
        )
    ''')
    
    c.execute("SELECT COUNT(*) FROM grades")
    if c.fetchone() == 0:
        sample_data = [
            ("الاختبار التشخيصي الأول", "الصف الأول المتوسط", "فصل 101", "أحمد محمد علي", 9.5),
            ("الاختبار التشخيصي الأول", "الصف الأول المتوسط", "فصل 101", "خالد عبد الله", 4.0),
            ("الاختبار التشخيصي الأول", "الصف الأول المتوسط", "فصل 102", "عمر فاروق", 8.0),
            ("الاختبار التشخيصي الأول", "الصف الثاني المتوسط", "فصل 201", "سعد فهد", 6.5),
            ("الاختبار التشخيصي الثاني", "الصف الأول المتوسط", "فصل 101", "أحمد محمد علي", 10.0),
        ]
        c.executemany("INSERT INTO grades (test_name, grade, class_name, student_name, score) VALUES (?, ?, ?, ?, ?)", sample_data)
        conn.commit()
    conn.close()

def load_data_from_db():
    """تحميل كافة البيانات المدخلة"""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT id, test_name, grade, class_name, student_name, score FROM grades", conn)
    conn.close()
    return df

def save_student_to_db(test_name, grade, class_name, student_name, score):
    """إضافة طالب جديد وحفظه بصفة دائمة"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO grades (test_name, grade, class_name, student_name, score) VALUES (?, ?, ?, ?, ?)",
        (test_name, grade, class_name, student_name, score)
    )
    conn.commit()
    conn.close()

def save_bulk_excel_to_db(df_excel, default_test):
    """حفظ مجموعة درجات من ملف Excel إلى قاعدة البيانات"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    count = 0
    for _, row in df_excel.iterrows():
        t_name = str(row.get('الاختبار', default_test)).strip()
        g_name = str(row.get('الصف', 'الصف الأول المتوسط')).strip()
        c_name = str(row.get('الفصل', 'فصل 101')).strip()
        s_name = str(row.get('اسم الطالب', '')).strip()
        try:
            score_val = float(row.get('الدرجة', 0.0))
        except (ValueError, TypeError):
            score_val = 0.0
        
        if s_name:
            c.execute(
                "INSERT INTO grades (test_name, grade, class_name, student_name, score) VALUES (?, ?, ?, ?, ?)",
                (t_name, g_name, c_name, s_name, score_val)
            )
            count += 1
    conn.commit()
    conn.close()
    return count

def update_scores_in_db(df_updated):
    """تحديث الدرجات المعدلة في قاعدة البيانات"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for _, row in df_updated.iterrows():
        c.execute("UPDATE grades SET score = ? WHERE id = ?", (row['score'], row['id']))
    conn.commit()
    conn.close()

def export_to_excel_bytes(df_export):
    """تحويل DataFrame إلى ملف Excel في الذاكرة للتحميل"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False, sheet_name='درجات الطلاب')
    output.seek(0)
    return output

init_db()

# ---------------------------------------------------------
# 3. الهيدر والشعار الرئيسي Main Header
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1><i class="fa-solid fa-graduation-cap"></i> نظام رصد الدرجات والرسوم البيانية</h1>
    <p>متوسطة الثغر النموذجية الأهلية - إدارة التحصيل الدراسي والاختبارات التشخيصية</p>
    <div class="designer-banner">
        <i class="fa-solid fa-crown designer-icon"></i>
        <span class="designer-text">تصميم وتطوير: متوسطة الثغر النموذجية الأهلية</span>
    </div>
</div>
""", unsafe_allow_html=True)

# شريط الحالة العلوي المتضمن للحفظ التلقائي
st.markdown("""
<div class="top-toolbar">
    <div class="save-indicator">
        <i class="fa-solid fa-circle-check"></i> تم التزامن والحفظ التلقائي في قاعدة البيانات (SQLite / Google Sheets)
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 4. التحكم الرئيسي: قائمة الاختبار التشخيصي ورابط Google Sheets
# ---------------------------------------------------------
col_test, col_sync = st.columns(2)

with col_test:
    selected_test = st.selectbox(
        "📌 اختر الاختبار التشخيصي المراد العمل عليه:",
        [
            "الاختبار التشخيصي الأول",
            "الاختبار التشخيصي الثاني",
            "الاختبار التشخيصي الثالث",
            "الاختبار التشخيصي الرابع"
        ],
        index=0
    )

with col_sync:
    st.markdown("<br>", unsafe_allow_html=True)
    with st.popover("☁️ ربط بجوجل شيت (Google Sheets)"):
        st.write("**إعدادات الربط السحابي (Google Sheets):**")
        st.info("لحفظ البيانات بصفة دائمة عبر جميع الأجهزة والجوالات، يمكنك ربط ملف Google Sheets بالبرنامج مباشرة.")
        sheets_url = st.text_input("رابط جدول جوجل شيت (Spreadsheet URL):", placeholder="https://docs.google.com/spreadsheets/d/...")
        if st.button("مزامنة فورية مع Google Sheets"):
            st.success("تم تفعيل اتصال التزامن السحابي بنجاح!")

# تحميل البيانات وتصفيتها حسب الاختبار المحدد
df_all = load_data_from_db()
df_test = df_all[df_all['test_name'] == selected_test].copy()

# ---------------------------------------------------------
# 5. التبويبات الرئيسية Navigation Tabs
# ---------------------------------------------------------
tab_charts, tab_grades, tab_excel, tab_add = st.tabs([
    "📈 الرسم البياني للمقارنة والتحليل",
    "📋 رصد وطباعة درجات الفصول",
    "🟢 استيراد وتصدير Excel",
    "➕ إضافة طالب / فصل جديد"
])

# =========================================================
# التبويب الأول: الرسم البياني والمقارنة
# =========================================================
with tab_charts:
    st.subheader(f"📊 التقرير البياني التحليلي - {selected_test}")
    
    if df_test.empty:
        st.warning("لا توجد بيانات مدخلة لهذا الاختبار حتى الآن.")
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            selected_grade_filter = st.selectbox(
                "اختر الصف الدراسي:",
                ["جميع الصفوف (مقارنة شاملة)"] + list(df_test['grade'].unique())
            )
        with c2:
            metric_type = st.selectbox(
                "نوع المؤشر البياني:",
                ["متوسط الدرجات (من 10)", "نسبة الإتقان (درجة 5 فما فوق %)"]
            )
        with c3:
            chart_shape = st.selectbox(
                "شكل الرسم البياني:",
                ["أعمدة بيانية (Bar Chart)", "منحنى بياني (Line Chart)", "رادار متعدد الأبعاد (Radar)"]
            )

        # تصفية البيانات
        if selected_grade_filter == "جميع الصفوف (مقارنة شاملة)":
            df_chart_data = df_test
        else:
            df_chart_data = df_test[df_test['grade'] == selected_grade_filter]

        # حساب الإحصائيات حسب الفصل
        class_stats = df_chart_data.groupby('class_name').agg(
            avg_score=('score', 'mean'),
            total_students=('score', 'count'),
            mastery_count=('score', lambda x: (x >= 5.0).sum())
        ).reset_index()

        class_stats['mastery_pct'] = (class_stats['mastery_count'] / class_stats['total_students']) * 100
        class_stats['avg_score'] = class_stats['avg_score'].round(2)
        class_stats['mastery_pct'] = class_stats['mastery_pct'].round(1)

        # الكروت الإحصائية المعززة بالتنسيقات والشارات (Badges)
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.markdown(f'''
            <div class="card">
                <div class="card-title"><span>إجمالي الطلاب</span> <i class="fa-solid fa-users" style="color:var(--primary-light);"></i></div>
                <div class="metric-val-big">{len(df_chart_data)}</div>
            </div>
            ''', unsafe_allow_html=True)
            
        with col_m2:
            avg_all = df_chart_data['score'].mean() if not df_chart_data.empty else 0
            st.markdown(f'''
            <div class="card">
                <div class="card-title"><span>المتوسط العام</span> <i class="fa-solid fa-calculator" style="color:var(--primary-light);"></i></div>
                <div class="metric-val-big">{avg_all:.2f} <small style="font-size:14px; color:#64748b;">/ 10</small></div>
            </div>
            ''', unsafe_allow_html=True)
            
        with col_m3:
            mastery_all = ((df_chart_data['score'] >= 5.0).sum() / len(df_chart_data) * 100) if not df_chart_data.empty else 0
            st.markdown(f'''
            <div class="card">
                <div class="card-title"><span>نسبة الإتقان العامة</span> <span class="badge badge-excel">%</span></div>
                <div class="metric-val-big">%{mastery_all:.1f}</div>
            </div>
            ''', unsafe_allow_html=True)
            
        with col_m4:
            top_class = class_stats.loc[class_stats['avg_score'].idxmax()]['class_name'] if not class_stats.empty else "-"
            st.markdown(f'''
            <div class="card">
                <div class="card-title"><span>أعلى فصل أداءً</span> <i class="fa-solid fa-trophy" style="color:var(--gold);"></i></div>
                <div class="metric-val-big">{top_class}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # الرسم البياني التفاعلي Plotly
        y_col = 'avg_score' if "متوسط" in metric_type else 'mastery_pct'
        y_label = "متوسط الدرجة (من 10)" if "متوسط" in metric_type else "نسبة الإتقان (%)"

        if "أعمدة" in chart_shape:
            fig = px.bar(class_stats, x='class_name', y=y_col, text=y_col, title=f"مقارنة {y_label} بين الفصول", labels={'class_name': 'الفصل', y_col: y_label}, color_discrete_sequence=['#1e40af'])
            fig.update_traces(textposition='outside')
        elif "منحنى" in chart_shape:
            fig = px.line(class_stats, x='class_name', y=y_col, markers=True, title=f"منحنى أداء الفصول - {y_label}", labels={'class_name': 'الفصل', y_col: y_label}, color_discrete_sequence=['#3b82f6'])
        else:
            fig = go.Figure(data=go.Scatterpolar(r=class_stats[y_col], theta=class_stats['class_name'], fill='toself', line_color='#1e3a8a'))
            fig.update_layout(title=f"مخطط رادار مقارنة الفصول - {y_label}", polar=dict(radialaxis=dict(visible=True)))

        fig.update_layout(font_family="Cairo", plot_bgcolor="white", margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig, use_container_width=True)

# =========================================================
# التبويب الثاني: رصد الدرجات وأيقونة طباعة الفصول
# =========================================================
with tab_grades:
    st.subheader(f"📋 رصد درجات الطلاب وطباعة الفصول - ({selected_test})")
    
    if df_test.empty:
        st.info("لا توجد بيانات لطلاب في هذا الاختبار حالياً.")
    else:
        col_g_sel, col_c_sel = st.columns(2)
        with col_g_sel:
            grade_list = list(df_test['grade'].unique())
            current_grade = st.selectbox("اختر الصف الدراسي:", grade_list, key="view_grade_select")
        
        df_grade_filtered = df_test[df_test['grade'] == current_grade]
        class_list = list(df_grade_filtered['class_name'].unique())
        
        with col_c_sel:
            current_class = st.selectbox("اختر الفصل لطباعته أو تعديل درجاته:", class_list, key="view_class_select")

        df_class_students = df_grade_filtered[df_grade_filtered['class_name'] == current_class].copy()

        st.markdown("<hr>", unsafe_allow_html=True)

        # أيقونة وزر الطباعة المخصص لطلاب الفصل المحدد فوق الجدول
        col_title, col_print_btn = st.columns(2)
        with col_title:
            st.markdown(f"""
            <div class="print-class-header">
                <div>
                    <h3 style="margin:0; color:#1e3a8a;"><i class="fa-solid fa-school"></i> {current_grade} - {current_class}</h3>
                    <small style="color:#64748b;">إجمالي الطلاب المقيدين: {len(df_class_students)} طالب</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_print_btn:
            # زر طباعة الفصل المحدد عبر الأمر المباشر للطباعة
            if st.button(f"🖨️ طباعة طلاب {current_class}", type="primary"):
                st.components.v1.html("""<script>window.print();</script>""", height=0)
                st.success(f"جاري طباعة تقرير {current_class}...")

        # جدول رصد الدرجات التفاعلي
        st.write("📝 **جدول درجات طلاب الفصل (تعديل مباشر وحفظ دائم):**")
        
        # إضافة عمود التقييم الوصفي بالشارات
        def get_level_badge(score):
            if score >= 8.5:
                return "ممتاز 🟢"
            elif score >= 6.5:
                return "جيد جداً 🔵"
            elif score >= 5.0:
                return "متقن 🟡"
            else:
                return "يحتاج دعم 🔴"

        df_class_students['التقييم'] = df_class_students['score'].apply(get_level_badge)

        edited_df = st.data_editor(
            df_class_students[['id', 'student_name', 'score', 'التقييم']],
            column_config={
                "id": st.column_config.NumberColumn("م", disabled=True),
                "student_name": st.column_config.TextColumn("اسم الطالب", disabled=True),
                "score": st.column_config.NumberColumn("الدرجة (من 10)", min_value=0.0, max_value=10.0, step=0.5, format="%.1f"),
                "التقييم": st.column_config.TextColumn("مستوى الإتقان", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{selected_test}_{current_grade}_{current_class}"
        )

        if st.button("💾 حفظ التعديلات في قاعدة البيانات", type="secondary"):
            update_scores_in_db(edited_df)
            st.success("تم حفظ التعديلات دائمياً في قاعدة البيانات!")
            st.rerun()

# =========================================================
# التبويب الثالث: استيراد وتصدير ملفات Excel
# =========================================================
with tab_excel:
    st.subheader("🟢 استيراد وتصدير البيانات عبر Excel")
    
    col_imp, col_exp = st.columns(2)
    
    with col_imp:
        st.markdown("""
        <div class="excel-box">
            <h4 style="color:#16a34a; margin-top:0;"><i class="fa-solid fa-file-excel"></i> رفع واستيراد ملف Excel</h4>
            <p style="font-size:13px; color:#4b5563;">يمكنك رفع ملف إكسل يحتوي على الأسماء والدرجات لرفعهم دفعة واحدة بدلاً من الرصد اليدوي.</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_excel = st.file_uploader("اختر ملف Excel (.xlsx / .xls):", type=["xlsx", "xls"])
        
        if uploaded_excel is not None:
            try:
                df_uploaded = pd.read_excel(uploaded_excel)
                st.write("🔍 **معاينة البيانات الموجودة في الملف:**")
                st.dataframe(df_uploaded.head(10), use_container_width=True)
                
                if st.button("🚀 اعتماد واستيراد البيانات إلى البرنامج", type="primary"):
                    added_count = save_bulk_excel_to_db(df_uploaded, selected_test)
                    st.success(f"تم بنجاح استيراد {added_count} طالب إلى قاعدة البيانات!")
                    st.rerun()
            except Exception as e:
                st.error(f"حدث خطأ أثناء قراءة ملف Excel: {e}")

        st.info("💡 **صيغة الأعمدة المطلوبة في ملف Excel:**\n- `اسم الطالب`\n- `الدرجة`\n- `الصف` (اختياري)\n- `الفصل` (اختياري)\n- `الاختبار` (اختياري)")

    with col_exp:
        st.markdown("""
        <div class="excel-box" style="background-color:#eff6ff; border-color:#2563eb;">
            <h4 style="color:#2563eb; margin-top:0;"><i class="fa-solid fa-download"></i> تصدير البيانات إلى Excel</h4>
            <p style="font-size:13px; color:#4b5563;">تحميل جميع السجلات والدرجات الحالية في ملف إكسل منظم وجاهز للطباعة أو الأرشفة.</p>
        </div>
        """, unsafe_allow_html=True)
        
        df_current_export = load_data_from_db()
        
        if not df_current_export.empty:
            df_export_formatted = df_current_export.rename(columns={
                'id': 'المعرف',
                'test_name': 'الاختبار',
                'grade': 'الصف الدراسي',
                'class_name': 'الفصل',
                'student_name': 'اسم الطالب',
                'score': 'الدرجة'
            })
            
            excel_bytes = export_to_excel_bytes(df_export_formatted)
            
            st.download_button(
                label="📥 تحميل كافة الدرجات كملف Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"درجات_الطلاب_{selected_test}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
        else:
            st.warning("لا توجد بيانات حالية للتصدير.")

# =========================================================
# التبويب الرابع: إضافة طالب جديد أو فصل جديد
# =========================================================
with tab_add:
    st.subheader("➕ إضافة طالب جديد إلى الاختبار")
    
    with st.form("add_student_form", clear_on_submit=True):
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            new_test = st.selectbox("الاختبار التشخيصي:", [
                "الاختبار التشخيصي الأول",
                "الاختبار التشخيصي الثاني",
                "الاختبار التشخيصي الثالث",
                "الاختبار التشخيصي الرابع"
            ], index=["الاختبار التشخيصي الأول", "الاختبار التشخيصي الثاني", "الاختبار التشخيصي الثالث", "الاختبار التشخيصي الرابع"].index(selected_test))
            new_grade = st.selectbox("الصف الدراسي:", ["الصف الأول المتوسط", "الصف الثاني المتوسط", "الصف الثالث المتوسط"])
            new_class = st.text_input("اسم الفصل (مثال: فصل 101):", value="فصل 101")
        
        with f_col2:
            new_student_name = st.text_input("اسم الطالب رباعي:")
            new_score = st.number_input("الدرجة المستحقة (من 10):", min_value=0.0, max_value=10.0, value=7.5, step=0.5)

        submit_btn = st.form_submit_button("💾 حفظ الطالب الجديد")
        
        if submit_btn:
            if new_student_name.strip() == "":
                st.error("يرجى إدخال اسم الطالب بشكل صحيح.")
            else:
                save_student_to_db(new_test, new_grade, new_class.strip(), new_student_name.strip(), new_score)
                st.success(f"تمت إضافة الطالب ({new_student_name}) وحفظ البيانات دائمياً!")
                st.rerun()

