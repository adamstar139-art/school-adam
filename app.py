<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>الاختبار التشخيصي - متوسطة الثغر النموذجية الأهلية</title>
    <!-- الخطوط والأيقونات والمخطط البياني -->
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-light: #3b82f6;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --red-bg: #fee2e2;
            --red-text: #991b1b;
            --green-bg: #dcfce7;
            --green-text: #166534;
        }
        * { box-sizing: border-box; font-family: 'Tajawal', sans-serif; }
        body { background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; }
        .container { max-width: 1250px; margin: 0 auto; }
        
        /* الهيدر الرئيسي */
        .header {
            text-align: center;
            background: linear-gradient(135deg, #1e3a8a, #2563eb);
            color: white;
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }
        .header h1 { margin: 0 0 10px 0; font-size: 26px; font-weight: 700; }
        .header p { margin: 0; opacity: 0.9; font-size: 15px; }

        /* أيقونات التبويب للصفوف */
        .nav-tabs {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        .tab-btn {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 14px 32px;
            border: none;
            background: white;
            color: var(--primary);
            font-size: 17px;
            font-weight: 700;
            border-radius: 14px;
            cursor: pointer;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }
        .tab-btn:hover { transform: translateY(-3px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }
        .tab-btn.active { background: var(--primary); color: white; }

        /* محتوى الصفوف */
        .tab-content { display: none; }
        .tab-content.active { display: block; }

        /* بطاقات المواد الأربع */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
            border-top: 6px solid var(--primary-light);
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #f1f5f9;
        }
        .card-title { font-size: 18px; font-weight: 700; color: var(--primary); }
        .card-icon { font-size: 20px; color: var(--primary-light); }
        
        .metric { display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }
        .metric-label { color: #64748b; }
        .metric-val { font-weight: 700; color: var(--text); }
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
        }
        .badge-excel { background: #dcfce7; color: #15803d; }
        .badge-good { background: #e0f2fe; color: #0369a1; }
        .badge-need { background: #fef3c7; color: #b45309; }

        /* القسم المزدوج: الرسم البياني والجدول */
        .grid-2 {
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }
        .chart-card, .table-card {
            background: white;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
        }
        .section-h { font-size: 18px; font-weight: 700; margin-top: 0; margin-bottom: 20px; color: var(--primary); }

        /* الجدول والتنسيق الشرطي */
        .table-responsive { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; }
        th, td { padding: 12px 14px; border-bottom: 1px solid #e2e8f0; }
        th { background: #f8fafc; color: var(--primary); font-weight: 700; }
        
        /* التنسيق الشرطي للدرجات */
        .val-low { background-color: var(--red-bg) !important; color: var(--red-text) !important; font-weight: 700; border-radius: 6px; }
        .val-high { background-color: var(--green-bg) !important; color: var(--green-text) !important; font-weight: 700; border-radius: 6px; }
    </style>
</head>
<body>

<div class="container">
    <!-- العنوان الرئيسي -->
    <div class="header">
        <h1><i class="fa-solid fa-school ml-2"></i> الاختبار التشخيصي لمتوسطة الثغر النموذجية الأهلية</h1>
        <p>نظام متابعة وتحليل نتائج المواد الدراسية ومؤشرات الأداء</p>
    </div>

    <!-- أيقونات التبويب الرئيسية -->
    <div class="nav-tabs">
        <button class="tab-btn active" onclick="openTab('grade1', this)">
            <i class="fa-solid fa-graduation-cap"></i> الصف الأول
        </button>
        <button class="tab-btn" onclick="openTab('grade2', this)">
            <i class="fa-solid fa-graduation-cap"></i> الصف الثاني
        </button>
        <button class="tab-btn" onclick="openTab('grade3', this)">
            <i class="fa-solid fa-graduation-cap"></i> الصف الثالث
        </button>
    </div>

    <!-- ==================== الصف الأول ==================== -->
    <div id="grade1" class="tab-content active">
        <!-- بطاقات المواد الأربع -->
        <div class="cards-grid">
            <div class="card">
                <div class="card-header"><span class="card-title">العلوم</span><i class="fa-solid fa-flask card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">3.9 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">38.9%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-need">يحتاج دعم مكثف</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">الرياضيات</span><i class="fa-solid fa-calculator card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">0.0 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">0.0%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-need">يتطلب إعادة اختبار</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">لغتي</span><i class="fa-solid fa-book card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">4.5 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">52.9%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-good">جهد متوسط ومقبول</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">انجليزي</span><i class="fa-solid fa-language card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">4.5 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">52.9%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-good">جهد متوسط ومقبول</span></div>
            </div>
        </div>

        <!-- الرسم البياني -->
        <div class="chart-card">
            <h3 class="section-h"><i class="fa-solid fa-chart-bar ml-2"></i> الرسم البياني لمتوسط درجات المواد - الصف الأول</h3>
            <canvas id="chartG1" height="90"></canvas>
        </div>

        <!-- جدول درجات الطلاب -->
        <div class="table-card">
            <h3 class="section-h"><i class="fa-solid fa-table-list ml-2"></i> كشف درجات الطلاب (الصف الأول)</h3>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>اسم الطالب</th>
                            <th>علوم</th>
                            <th>رياضيات</th>
                            <th>لغتي</th>
                            <th>انجليزي</th>
                            <th>المجموع</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>بلال عبدالرزاق العيسى</td><td class="val-high">5</td><td class="val-low">0</td><td class="val-high">5</td><td class="val-low">4</td><td>14</td></tr>
                        <tr><td>جاسر بن عبدالله الحارثي</td><td class="val-low">4</td><td class="val-low">0</td><td class="val-low">3</td><td class="val-low">1</td><td>8</td></tr>
                        <tr><td>حسام بن محمد البارقي</td><td class="val-low">3</td><td class="val-low">0</td><td class="val-high">6</td><td class="val-high">6</td><td>15</td></tr>
                        <tr><td>ريان عبدالله الأسمري</td><td class="val-low">4</td><td class="val-low">0</td><td class="val-high">6</td><td class="val-low">3</td><td>13</td></tr>
                        <tr><td>زيد زياد ابو قبع</td><td class="val-high">6</td><td class="val-low">0</td><td class="val-high">5</td><td class="val-high">6</td><td>17</td></tr>
                        <tr><td>الوليد ابن خالد العتيبي</td><td class="val-high">5</td><td class="val-low">0</td><td class="val-high">6</td><td class="val-high">9</td><td>20</td></tr>
                        <tr><td>ريان عبدالله السبر</td><td class="val-high">7</td><td class="val-low">0</td><td class="val-high">9</td><td class="val-high">6</td><td>22</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ==================== الصف الثاني ==================== -->
    <div id="grade2" class="tab-content">
        <div class="cards-grid">
            <div class="card">
                <div class="card-header"><span class="card-title">العلوم</span><i class="fa-solid fa-flask card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">3.7 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">31.0%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-need">خطط معالجة فجوات</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">الرياضيات</span><i class="fa-solid fa-calculator card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">3.3 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">24.1%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-need">تركيز مهارات أساسية</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">لغتي</span><i class="fa-solid fa-book card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">3.6 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">31.0%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-need">دعم قرائي وكتابي</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">انجليزي</span><i class="fa-solid fa-language card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">3.7 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">34.5%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-good">جهد متوسط ومقبول</span></div>
            </div>
        </div>

        <div class="chart-card">
            <h3 class="section-h"><i class="fa-solid fa-chart-bar ml-2"></i> الرسم البياني لمتوسط درجات المواد - الصف الثاني</h3>
            <canvas id="chartG2" height="90"></canvas>
        </div>

        <div class="table-card">
            <h3 class="section-h"><i class="fa-solid fa-table-list ml-2"></i> كشف درجات الطلاب (الصف الثاني)</h3>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>اسم الطالب</th>
                            <th>علوم</th>
                            <th>رياضيات</th>
                            <th>لغتي</th>
                            <th>انجليزي</th>
                            <th>المجموع</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>ابراهيم ياسر الحلوي</td><td class="val-low">4</td><td class="val-low">3</td><td class="val-high">6</td><td class="val-high">5</td><td>18</td></tr>
                        <tr><td>محمد عبدالمحسن الحزام</td><td class="val-high">7</td><td class="val-high">7</td><td class="val-low">3</td><td class="val-high">5</td><td>22</td></tr>
                        <tr><td>ابراهيم مبارك آل موينع</td><td class="val-high">5</td><td class="val-high">6</td><td class="val-low">3</td><td class="val-high">10</td><td>24</td></tr>
                        <tr><td>حسام حسن الشهري</td><td class="val-high">6</td><td class="val-low">4</td><td class="val-low">4</td><td class="val-high">5</td><td>19</td></tr>
                        <tr><td>سعود ناصر العريفي</td><td class="val-low">4</td><td class="val-high">6</td><td class="val-high">6</td><td class="val-high">8</td><td>24</td></tr>
                        <tr><td>عبدالمجيد آل عايض הקحطاني</td><td class="val-low">4</td><td class="val-high">8</td><td class="val-high">7</td><td class="val-high">9</td><td>28</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- ==================== الصف الثالث ==================== -->
    <div id="grade3" class="tab-content">
        <div class="cards-grid">
            <div class="card">
                <div class="card-header"><span class="card-title">العلوم</span><i class="fa-solid fa-flask card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">4.0 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">41.4%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-good">جهد ملموس ومقبول</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">الرياضيات</span><i class="fa-solid fa-calculator card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">4.7 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">55.2%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-excel">جهد متميز ورائع</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">لغتي</span><i class="fa-solid fa-book card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">5.5 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">72.4%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-excel">جهد ممتازة وكفاءة عالية</span></div>
            </div>
            <div class="card">
                <div class="card-header"><span class="card-title">انجليزي</span><i class="fa-solid fa-language card-icon"></i></div>
                <div class="metric"><span class="metric-label">المتوسط:</span><span class="metric-val">4.3 / 10</span></div>
                <div class="metric"><span class="metric-label">نسبة الإتقان:</span><span class="metric-val">44.8%</span></div>
                <div class="metric"><span class="metric-label">جهد المعلم:</span><span class="badge badge-good">جهد جيد ومستمر</span></div>
            </div>
        </div>

        <div class="chart-card">
            <h3 class="section-h"><i class="fa-solid fa-chart-bar ml-2"></i> الرسم البياني لمتوسط درجات المواد - الصف الثالث</h3>
            <canvas id="chartG3" height="90"></canvas>
        </div>

        <div class="table-card">
            <h3 class="section-h"><i class="fa-solid fa-table-list ml-2"></i> كشف درجات الطلاب (الصف الثالث)</h3>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>اسم الطالب</th>
                            <th>علوم</th>
                            <th>رياضيات</th>
                            <th>لغتي</th>
                            <th>انجليزي</th>
                            <th>المجموع</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>عبدالعزيز عبدالله الاسمري</td><td class="val-high">5</td><td class="val-high">6</td><td class="val-high">7</td><td class="val-high">5</td><td>23</td></tr>
                        <tr><td>فيصل عبدالمحسن العصيمي</td><td class="val-high">5</td><td class="val-high">9</td><td class="val-low">0</td><td class="val-high">6</td><td>20</td></tr>
                        <tr><td>فيصل محمد الفنتوخ</td><td class="val-high">5</td><td class="val-high">7</td><td class="val-high">7</td><td class="val-low">4</td><td>23</td></tr>
                        <tr><td>ياسر تركي مسملي</td><td class="val-high">8</td><td class="val-high">9</td><td class="val-high">6</td><td class="val-high">6</td><td>29</td></tr>
                        <tr><td>علي عبدالله ال حمود</td><td class="val-high">6</td><td class="val-high">7</td><td class="val-high">7</td><td class="val-high">10</td><td>30</td></tr>
                        <tr><td>نواف فهد القحطاني</td><td class="val-high">8</td><td class="val-low">0</td><td class="val-high">6</td><td class="val-high">9</td><td>23</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script>
    // التنقل بين أزرار الصفوف
    function openTab(tabId, btn) {
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        btn.classList.add('active');
    }

    // إعداد الرسوم البيانية لكل صف
    const subjects = ['علوم', 'رياضيات', 'لغتي', 'انجليزي'];
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#6366f1'];

    function createChart(ctxId, data) {
        new Chart(document.getElementById(ctxId), {
            type: 'bar',
            data: {
                labels: subjects,
                datasets: [{
                    label: 'متوسط الدرجات (من 10)',
                    data: data,
                    backgroundColor: colors,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                scales: { y: { beginAtZero: true, max: 10 } },
                plugins: { legend: { display: false } }
            }
        });
    }

    // تشغيل الرسوم البيانية
    createChart('chartG1', [3.9, 0.0, 4.5, 4.5]);
    createChart('chartG2', [3.7, 3.3, 3.6, 3.7]);
    createChart('chartG3', [4.0, 4.7, 5.5, 4.3]);
</script>
</body>
</html>
