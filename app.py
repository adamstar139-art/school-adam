import json
import streamlit as st

st.set_page_config(
    page_title="نظام رصد الدرجات الشامل - متوسطة الثغر النموذجية الأهلية",
    layout="wide",
)

html_code = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>نظام رصد درجات الاختبار التشخيصي وتقارير PDF</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --primary: #1e3a8a;
            --primary-light: #2563eb;
            --bg: #f8fafc;
            --card: #ffffff;
            --text: #1e293b;
            --red-bg: #fee2e2;
            --red-text: #991b1b;
            --green-bg: #dcfce7;
            --green-text: #166534;
            --gold: #fef08a;
        }
        * { box-sizing: border-box; font-family: 'Tajawal', sans-serif; }
        body { background-color: var(--bg); color: var(--text); margin: 0; padding: 20px; }
        .container { max-width: 1350px; margin: 0 auto; }
        
        .header {
            text-align: center;
            background: linear-gradient(135deg, #1e3a8a, #1e40af, #3b82f6);
            color: white;
            padding: 30px 20px;
            border-radius: 22px;
            margin-bottom: 22px;
            box-shadow: 0 12px 24px rgba(30, 58, 138, 0.18);
            position: relative;
            overflow: hidden;
        }
        .header h1 { margin: 0 0 8px 0; font-size: 26px; font-weight: 800; }
        .header p { margin: 0 0 15px 0; opacity: 0.92; font-size: 15px; }

        /* تصميم الأستاذ محمد سامي السعيد */
        .designer-banner {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(8px);
            border: 2px solid rgba(255, 255, 255, 0.35);
            padding: 10px 28px;
            border-radius: 50px;
            margin-top: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.12);
            transition: all 0.3s ease;
        }
        .designer-banner:hover {
            transform: scale(1.03);
            background: rgba(255, 255, 255, 0.22);
            border-color: rgba(255, 255, 255, 0.6);
        }
        .designer-text {
            font-size: 20px;
            font-weight: 800;
            color: var(--gold);
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            letter-spacing: 0.3px;
        }
        .designer-icon {
            font-size: 22px;
            color: var(--gold);
        }

        .top-toolbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            background: white;
            padding: 15px 20px;
            border-radius: 14px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.03);
            flex-wrap: wrap;
            gap: 10px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            font-size: 14px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }
        .btn-primary { background: var(--primary); color: white; }
        .btn-primary:hover { background: #172554; }
        .btn-success { background: #10b981; color: white; }
        .btn-success:hover { background: #059669; }

        .save-indicator {
            font-size: 13px;
            color: #10b981;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 6px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .save-indicator.active { opacity: 1; }

        .main-tabs { display: flex; justify-content: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        .main-tab-btn {
            padding: 12px 26px;
            border: 2px solid var(--primary);
            background: white;
            color: var(--primary);
            font-size: 16px;
            font-weight: 700;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .main-tab-btn.active { background: var(--primary); color: white; }

        .class-tabs {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 20px;
            background: #e2e8f0;
            padding: 6px;
            border-radius: 12px;
            width: fit-content;
            margin: 0 auto 20px auto;
        }
        .class-btn {
            padding: 8px 20px;
            border: none;
            background: transparent;
            color: #475569;
            font-size: 14px;
            font-weight: 700;
            border-radius: 8px;
            cursor: pointer;
        }
        .class-btn.active { background: white; color: var(--primary); }

        .tab-content { display: none; }
        .tab-content.active { display: block; }

        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
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
        .card-title { font-size: 17px; font-weight: 700; color: var(--primary); margin-bottom: 10px; display: flex; justify-content: space-between; }
        .metric { display: flex; justify-content: space-between; font-size: 13px; margin-bottom: 6px; }
        .badge { padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
        .badge-excel { background: #dcfce7; color: #15803d; }
        .badge-good { background: #e0f2fe; color: #0369a1; }
        .badge-need { background: #fef3c7; color: #b45309; }

        .chart-card, .table-card { background: white; padding: 20px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.03); }
        .table-responsive { overflow-x: auto; max-height: 500px; }
        table { width: 100%; border-collapse: collapse; text-align: center; font-size: 14px; }
        th, td { padding: 10px; border: 1px solid #e2e8f0; }
        th { background: #f8fafc; color: var(--primary); font-weight: 700; position: sticky; top: 0; z-index: 2; }

        .score-input {
            width: 58px;
            text-align: center;
            padding: 5px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-weight: 700;
        }
        .score-low { background-color: var(--red-bg) !important; color: var(--red-text) !important; }
        .score-high { background-color: var(--green-bg) !important; color: var(--green-text) !important; }
        .score-zero { background-color: #f1f5f9 !important; color: #64748b !important; }

        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 999;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: white;
            padding: 25px;
            border-radius: 18px;
            width: 90%;
            max-width: 550px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        .modal-header { font-size: 18px; font-weight: 700; color: var(--primary); margin-bottom: 15px; display: flex; justify-content: space-between; }
        .checkbox-group { display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px; max-height: 250px; overflow-y: auto; text-align: right; }
        .checkbox-item { display: flex; align-items: center; gap: 10px; font-size: 15px; cursor: pointer; }

        @media print {
            body { background: white; padding: 0; color: black; }
            .header, .top-toolbar, .main-tabs, .class-tabs, .btn, .modal { display: none !important; }
            .tab-content { display: block !important; page-break-after: always; }
            .class-content { display: block !important; page-break-inside: avoid; margin-bottom: 30px; }
            .card, .table-card, .chart-card { box-shadow: none !important; border: 1px solid #ccc !important; }
            .score-input { border: none !important; background: transparent !important; }
            .print-only-header { display: block !important; text-align: center; margin-bottom: 20px; border-bottom: 2px solid #1e3a8a; padding-bottom: 10px; }
        }
        .print-only-header { display: none; }
    </style>
</head>
<body>

<div class="container">
    <div class="header">
        <h1><i class="fa-solid fa-school ml-2"></i> الاختبار التشخيصي - متوسطة الثغر النموذجية الأهلية</h1>
        <p>نظام رصد الدرجات التلقائي وإصدار تقارير PDF المعتمدة</p>
        
        <!-- تصميم الأستاذ محمد سامي السعيد -->
        <div class="designer-banner">
            <i class="fa-solid fa-wand-magic-sparkles designer-icon"></i>
            <span class="designer-text">تصميم الأستاذ: محمد سامي السعيد</span>
            <i class="fa-solid fa-star designer-icon"></i>
        </div>
    </div>

    <div class="top-toolbar">
        <div class="save-indicator" id="saveIndicator">
            <i class="fa-solid fa-circle-check"></i> تم الحفظ التلقائي في المتصفح
        </div>
        <div>
            <button class="btn btn-primary" onclick="openPrintModal()">
                <i class="fa-solid fa-print"></i> طباعة التقرير الشامل (PDF)
            </button>
        </div>
    </div>

    <div class="main-tabs">
        <button class="main-tab-btn active" onclick="switchGrade('g1', this)">الصف الأول المتوسط</button>
        <button class="main-tab-btn" onclick="switchGrade('g2', this)">الصف الثاني المتوسط</button>
        <button class="main-tab-btn" onclick="switchGrade('g3', this)">الصف الثالث المتوسط</button>
    </div>

    <div id="gradesContainer"></div>
</div>

<div class="modal" id="printModal">
    <div class="modal-content">
        <div class="modal-header">
            <span><i class="fa-solid fa-file-pdf"></i> خيارات طباعة التقرير الشامل</span>
            <i class="fa-solid fa-xmark" style="cursor:pointer;" onclick="closePrintModal()"></i>
        </div>
        <p style="font-size:14px; color:#64748b; margin-bottom:15px;">حدد الصفوف والفصول التي تتضمنها التقرير:</p>
        <div class="checkbox-group" id="printOptionsGroup">
            <label class="checkbox-item"><input type="checkbox" id="checkAll" onchange="toggleSelectAll(this)" checked> <b>تحديد الكل</b></label>
            <hr style="width:100%; border:0; border-top:1px solid #eee; margin:5px 0;">
            <label class="checkbox-item"><input type="checkbox" class="print-opt" value="g1-c1" checked> الصف الأول المتوسط - فصل (1 / 1)</label>
            <label class="checkbox-item"><input type="checkbox" class="print-opt" value="g1-c2" checked> الصف الأول المتوسط - فصل (1 / 2)</label>
            <label class="checkbox-item"><input type="checkbox" class="print-opt" value="g2-c1" checked> الصف الثاني المتوسط - فصل (2 / 1)</label>
            <label class="checkbox-item"><input type="checkbox" class="print-opt" value="g2-c2" checked> الصف الثاني المتوسط - فصل (2 / 2)</label>
            <label class="checkbox-item"><input type="checkbox" class="print-opt" value="g2-c3" checked> الصف الثاني المتوسط - فصل (2 / 3)</label>
            <label class="checkbox-item"><input type="checkbox" class="print-opt" value="g3-c1" checked> الصف الثالث المتوسط - فصل (3 / 1)</label>
            <label class="checkbox-item"><input type="checkbox" class="print-opt" value="g3-c2" checked> الصف الثالث المتوسط - فصل (3 / 2)</label>
            <label class="checkbox-item"><input type="checkbox" class="print-opt" value="g3-c3" checked> الصف الثالث المتوسط - فصل (3 / 3)</label>
        </div>
        <div style="display:flex; justify-content:flex-end; gap:10px;">
            <button class="btn" style="background:#cbd5e1; color:#1e293b;" onclick="closePrintModal()">إلغاء</button>
            <button class="btn btn-success" onclick="executePDFPrint()"><i class="fa-solid fa-file-export"></i> تصدير وطباعة PDF</button>
        </div>
    </div>
</div>

<script>
    let localSaved = localStorage.getItem('althaghr_scores_db');
    let db = localSaved ? JSON.parse(localSaved) : {
      "g1": {
        "c1": [
          {"name": "بلال عبدالرزاق عيسى العيسى", "s": 5, "m": 0, "l": 5, "e": 4},
          {"name": "جاسر بن عبدالله بن منصور المطارحة الحارثي", "s": 4, "m": 0, "l": 3, "e": 1},
          {"name": "حسام بن محمد بن علي ال رايان البارقي", "s": 3, "m": 0, "l": 6, "e": 6},
          {"name": "ريان عبدالله جابر الاسمري", "s": 4, "m": 0, "l": 6, "e": 3},
          {"name": "زيد زياد عبد اللطيف ابو قبع", "s": 6, "m": 0, "l": 5, "e": 6},
          {"name": "سامي سعد عباس حمد", "s": 3, "m": 0, "l": 6, "e": 5},
          {"name": "سعد ناصر سعد السيف", "s": 3, "m": 0, "l": 2, "e": 4},
          {"name": "عبدالله بن سليمان بن عبدالله الراجحي", "s": 4, "m": 0, "l": 0, "e": 4},
          {"name": "عبدالله سعد بن محمد العيشان", "s": 0, "m": 0, "l": 7, "e": 0},
          {"name": "علي احمد علي كريري", "s": 4, "m": 0, "l": 5, "e": 2},
          {"name": "علي سعد علي القحطاني", "s": 3, "m": 0, "l": 3, "e": 4},
          {"name": "عمر عبدالله سعد الجبرين", "s": 2, "m": 0, "l": 1, "e": 4},
          {"name": "مازن اسلام احمد ابراهيم موسى", "s": 4, "m": 0, "l": 5, "e": 5},
          {"name": "محمد أحمد علي عقيل", "s": 0, "m": 0, "l": 0, "e": 0},
          {"name": "محمد اسلام محمد دراز", "s": 4, "m": 0, "l": 5, "e": 6},
          {"name": "محمد اشرف مسعود ابواخاطر", "s": 0, "m": 0, "l": 0, "e": 7},
          {"name": "محمد نايف فراج الدعجاني", "s": 0, "m": 0, "l": 3, "e": 0},
          {"name": "وائل - - بولعيش", "s": 0, "m": 0, "l": 0, "e": 5}
        ],
        "c2": [
          {"name": "ابراهيم بن محمد بن علي الوهيبي", "s": 3, "m": 0, "l": 1, "e": 2},
          {"name": "الوليد ابن خالد بن فهد العتيبي", "s": 5, "m": 0, "l": 6, "e": 9},
          {"name": "باسل محمد فرج الدوسري", "s": 6, "m": 0, "l": 7, "e": 4},
          {"name": "بسام بن عبدالكريم بن عبدالله الحرقان الدوسري", "s": 4, "m": 0, "l": 3, "e": 0},
          {"name": "تركي عبدالله مسفر الدوسري", "s": 5, "m": 0, "l": 5, "e": 4},
          {"name": "تميم فهد عبدالعزيز العزاز", "s": 3, "m": 0, "l": 5, "e": 3},
          {"name": "راكان عبدالله يحي كريري", "s": 5, "m": 0, "l": 6, "e": 6},
          {"name": "ريان عبدالله منصور السبر", "s": 7, "m": 0, "l": 9, "e": 6},
          {"name": "ريان وليد - حلاق", "s": 4, "m": 0, "l": 3, "e": 0},
          {"name": "سيف عبدالكريم بريك العصيمي", "s": 3, "m": 0, "l": 0, "e": 3},
          {"name": "صالح حسن فتحى سندى", "s": 0, "m": 0, "l": 5, "e": 0},
          {"name": "عبدالرحمن ابراهيم عبدالله الحضيف", "s": 4, "m": 0, "l": 5, "e": 5},
          {"name": "عبدالله صالح حمد الصفيان", "s": 3, "m": 0, "l": 4, "e": 5},
          {"name": "فهد ابن احمد بن فهد العثمان", "s": 4, "m": 0, "l": 4, "e": 7},
          {"name": "فهد عويض ثعيل المطيري", "s": 0, "m": 0, "l": 0, "e": 0},
          {"name": "فهد نايف فهد الحسينان", "s": 2, "m": 0, "l": 4, "e": 3},
          {"name": "فيصل موينع عبدالله بن موينع", "s": 0, "m": 0, "l": 0, "e": 0},
          {"name": "فيصل ناصر سيف العريفي", "s": 6, "m": 0, "l": 6, "e": 6},
          {"name": "مشاري عثمان سعد ناصر السعد", "s": 3, "m": 0, "l": 3, "e": 7},
          {"name": "يزن محمد علي اليحيا", "s": 3, "m": 0, "l": 6, "e": 5},
          {"name": "يوسف محمد عبدالله الدوسري", "s": 4, "m": 0, "l": 2, "e": 4}
                ]
      },
      "g2": {
        "c1": [
          {"name": "ابراهيم ياسر ابراهيم الحلوي", "s": 4, "m": 3, "l": 6, "e": 5},
          {"name": "عبدالرحمن ربيع جابر خبراني", "s": 7, "m": 3, "l": 6, "e": 4},
          {"name": "محمد عبدالمحسن ناصر الحزام", "s": 7, "m": 7, "l": 3, "e": 5}
        ],
        "c2": [
          {"name": "ابراهيم بن مبارك بن راشد آل موينع", "s": 5, "m": 6, "l": 3, "e": 10},
          {"name": "حسام حسن محمد الشهري", "s": 6, "m": 4, "l": 4, "e": 5},
          {"name": "سعود خالد عبدالله الحمد", "s": 6, "m": 5, "l": 3, "e": 2}
        ],
        "c3": [
          {"name": "ثامر عمر ابرهيم عثمان", "s": 3, "m": 4, "l": 7, "e": 6},
          {"name": "سعود ناصر سيف العريفي", "s": 4, "m": 6, "l": 6, "e": 8},
          {"name": "عبدالمجيد بن محمد بن مسعود آل عايض القحطاني", "s": 4, "m": 8, "l": 7, "e": 9}
        ]
      },
      "g3": {
        "c1": [
          {"name": "عبدالعزيز عبدالله عايض الاسمري", "s": 5, "m": 6, "l": 7, "e": 5},
          {"name": "فيصل بن عبدالمحسن العصيمي العتيبي", "s": 5, "m": 9, "l": 0, "e": 6},
          {"name": "فيصل محمد صالح الفنتوخ", "s": 5, "m": 7, "l": 7, "e": 4}
        ],
        "c2": [
          {"name": "عبد الرحمن محمد صلاح بدر الدين", "s": 6, "m": 4, "l": 6, "e": 6},
          {"name": "عبدالله متعب بن عبدالرحمن الجبرين", "s": 4, "m": 7, "l": 7, "e": 4},
          {"name": "ياسر تركي اسماعيل مسملي", "s": 8, "m": 9, "l": 6, "e": 6}
        ],
        "c3": [
          {"name": "عبدالرحمن خالد محمد سعيد", "s": 4, "m": 7, "l": 7, "e": 5},
          {"name": "علي عبدالله علي ال حمود", "s": 6, "m": 7, "l": 7, "e": 10},
          {"name": "نواف فهد بن ناصر القحطاني", "s": 8, "m": 0, "l": 6, "e": 9}
        ]
      }
    };

    const gradeLabels = {
        'g1': { title: 'الصف الأول المتوسط', classes: { 'c1': 'فصل (1 / 1)', 'c2': 'فصل (1 / 2)' } },
        'g2': { title: 'الصف الثاني المتوسط', classes: { 'c1': 'فصل (2 / 1)', 'c2': 'فصل (2 / 2)', 'c3': 'فصل (2 / 3)' } },
        'g3': { title: 'الصف الثالث المتوسط', classes: { 'c1': 'فصل (3 / 1)', 'c2': 'فصل (3 / 2)', 'c3': 'فصل (3 / 3)' } }
    };

    const subjKeys = ['s', 'm', 'l', 'e'];
    const subjNames = {'s': 'العلوم', 'm': 'الرياضيات', 'l': 'لغتي', 'e': 'انجليزي'};

    function saveToLocalStorage() {
        localStorage.setItem('althaghr_scores_db', JSON.stringify(db));
        let ind = document.getElementById('saveIndicator');
        ind.classList.add('active');
        setTimeout(() => ind.classList.remove('active'), 2000);
    }

    function updateScore(gKey, cKey, stIdx, subj, value, inputElem) {
        let val = parseFloat(value) || 0;
        db[gKey][cKey][stIdx][subj] = val;
        
        inputElem.className = 'score-input ' + getInputClass(val);
        
        let st = db[gKey][cKey][stIdx];
        let sum = (st.s || 0) + (st.m || 0) + (st.l || 0) + (st.e || 0);
        let row = inputElem.closest('tr');
        row.querySelector('.st-sum').innerText = sum;

        saveToLocalStorage();
    }

    function calcMetrics(students, subj) {
        let total = 0, count = 0, passCount = 0;
        students.forEach(st => {
            let score = parseFloat(st[subj]) || 0;
            total += score;
            count++;
            if (score >= 5) passCount++;
        });
        let avg = count > 0 ? (total / count).toFixed(1) : '0.0';
        let pct = count > 0 ? ((passCount / count) * 100).toFixed(1) : '0.0';
        let effort = 'جهد متوسط ومقبول';
        let badgeClass = 'badge-good';
        if (parseFloat(pct) >= 65) { effort = 'جهد متميز ورائع'; badgeClass = 'badge-excel'; }
        else if (parseFloat(pct) < 40) { effort = 'يتطلب خطة علاجية ودعم مكثف'; badgeClass = 'badge-need'; }
        return { avg, pct, effort, badgeClass };
    }

    function renderApp() {
        const container = document.getElementById('gradesContainer');
        container.innerHTML = '';

        Object.keys(gradeLabels).forEach((gKey, gIdx) => {
            const gInfo = gradeLabels[gKey];
            const gDiv = document.createElement('div');
            gDiv.id = gKey;
            gDiv.className = `tab-content ${gIdx === 0 ? 'active' : ''}`;

            let cTabsHtml = `<div class="class-tabs">`;
            Object.keys(gInfo.classes).forEach((cKey, cIdx) => {
                cTabsHtml += `<button class="class-btn ${cIdx === 0 ? 'active' : ''}" onclick="switchClass('${gKey}-${cKey}', this)">${gInfo.classes[cKey]}</button>`;
            });
            cTabsHtml += `</div>`;
            gDiv.innerHTML += cTabsHtml;

            Object.keys(gInfo.classes).forEach((cKey, cIdx) => {
                const students = db[gKey][cKey] || [];
                const cDiv = document.createElement('div');
                cDiv.id = `${gKey}-${cKey}`;
                cDiv.className = 'class-content';
                cDiv.style.display = cIdx === 0 ? 'block' : 'none';

                let cardsHtml = `<div class="cards-grid">`;
                subjKeys.forEach(sKey => {
                    let m = calcMetrics(students, sKey);
                    cardsHtml += `
                        <div class="card">
                            <div class="card-title"><span>${subjNames[sKey]}</span></div>
                            <div class="metric"><span>المتوسط:</span><b>${m.avg} / 10</b></div>
                            <div class="metric"><span>النسبة المئوية:</span><b>${m.pct}%</b></div>
                            <div class="metric"><span>جهد المعلم:</span><span class="badge ${m.badgeClass}">${m.effort}</span></div>
                        </div>
                    `;
                });
                cardsHtml += `</div>`;

                let tableHtml = `
                    <div class="table-card">
                        <div class="print-only-header">
                            <h2>المملكة العربية السعودية - وزارة التعليم</h2>
                            <h3>متوسطة الثغر النموذجية الأهلية - تقرير ${gInfo.title} - ${gInfo.classes[cKey]}</h3>
                            <p style="font-weight: bold; font-size: 16px;">تصميم الأستاذ: محمد سامي السعيد</p>
                        </div>
                        <h3><i class="fa-solid fa-users ml-1"></i> كشف درجات الطلاب (${gInfo.title} - ${gInfo.classes[cKey]})</h3>
                        <div class="table-responsive">
                            <table>
                                <thead>
                                    <tr><th>#</th><th>اسم الطالب</th><th>علوم</th><th>رياضيات</th><th>لغتي</th><th>انجليزي</th><th>المجموع</th></tr>
                                </thead>
                                <tbody>
                `;

                students.forEach((st, idx) => {
                    let sum = (st.s || 0) + (st.m || 0) + (st.l || 0) + (st.e || 0);
                    tableHtml += `
                        <tr>
                            <td>${idx + 1}</td>
                            <td style="text-align: right; font-weight: 700;">${st.name}</td>
                            <td><input type="number" value="${st.s}" class="score-input ${getInputClass(st.s)}" onchange="updateScore('${gKey}', '${cKey}', ${idx}, 's', this.value, this)"></td>
                            <td><input type="number" value="${st.m}" class="score-input ${getInputClass(st.m)}" onchange="updateScore('${gKey}', '${cKey}', ${idx}, 'm', this.value, this)"></td>
                            <td><input type="number" value="${st.l}" class="score-input ${getInputClass(st.l)}" onchange="updateScore('${gKey}', '${cKey}', ${idx}, 'l', this.value, this)"></td>
                            <td><input type="number" value="${st.e}" class="score-input ${getInputClass(st.e)}" onchange="updateScore('${gKey}', '${cKey}', ${idx}, 'e', this.value, this)"></td>
                            <td><b class="st-sum">${sum}</b></td>
                        </tr>
                    `;
                });

                tableHtml += `</tbody></table></div></div>`;
                cDiv.innerHTML = cardsHtml + tableHtml;
                gDiv.appendChild(cDiv);
            });

            container.appendChild(gDiv);
        });
    }

    function getInputClass(val) {
        val = parseFloat(val);
        if (isNaN(val) || val === 0) return 'score-zero';
        if (val < 5) return 'score-low';
        return 'score-high';
    }

    function switchGrade(gradeId, btn) {
        document.querySelectorAll('.main-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(gradeId).classList.add('active');
    }

    function switchClass(classId, btn) {
        let parent = btn.closest('.tab-content');
        parent.querySelectorAll('.class-btn').forEach(b => b.classList.remove('active'));
        parent.querySelectorAll('.class-content').forEach(c => c.style.display = 'none');
        btn.classList.add('active');
        document.getElementById(classId).style.display = 'block';
    }

    function openPrintModal() {
        document.getElementById('printModal').style.display = 'flex';
    }

    function closePrintModal() {
        document.getElementById('printModal').style.display = 'none';
    }

    function toggleSelectAll(master) {
        document.querySelectorAll('.print-opt').forEach(chk => chk.checked = master.checked);
    }

    function executePDFPrint() {
        closePrintModal();
        let selected = [];
        document.querySelectorAll('.print-opt:checked').forEach(chk => selected.push(chk.value));

        if (selected.length === 0) {
            alert('الرجاء اختيار فصل واحد على الأقل للطباعة');
            return;
        }

        document.querySelectorAll('.class-content').forEach(el => {
            if (selected.includes(el.id)) {
                el.style.display = 'block';
                el.closest('.tab-content').style.display = 'block';
            } else {
                el.style.display = 'none';
            }
        });

        window.print();
        renderApp();
    }

    document.addEventListener('DOMContentLoaded', renderApp);
</script>
</body>
</html>
"""

st.components.v1.html(html_code, height=980, scrolling=True)
