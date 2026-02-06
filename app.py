from flask import Flask, render_template_string
import os

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>حاسبة علمية متقدمة</title>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a2e;
            --bg-button: #16213e;
            --bg-button-hover: #1f3060;
            --text-primary: #e8e8f0;
            --text-secondary: #8888aa;
            --accent-orange: #ff6b35;
            --accent-blue: #4cc9f0;
            --accent-purple: #7b2ff7;
            --accent-green: #06d6a0;
            --accent-red: #ef476f;
            --border-color: #2a2a40;
            --shadow-glow: 0 0 30px rgba(123, 47, 247, 0.15);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'IBM Plex Sans Arabic', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
            position: relative;
        }

        body::before {
            content: '';
            position: fixed;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(ellipse at 30% 20%, rgba(123, 47, 247, 0.08) 0%, transparent 50%),
                        radial-gradient(ellipse at 70% 80%, rgba(76, 201, 240, 0.06) 0%, transparent 50%),
                        radial-gradient(ellipse at 50% 50%, rgba(255, 107, 53, 0.04) 0%, transparent 60%);
            animation: bgShift 20s ease-in-out infinite alternate;
            z-index: 0;
        }

        @keyframes bgShift {
            0% { transform: translate(0, 0) rotate(0deg); }
            100% { transform: translate(-5%, -3%) rotate(3deg); }
        }

        .calculator-wrapper {
            position: relative;
            z-index: 1;
            padding: 20px;
        }

        .calculator {
            width: 420px;
            max-width: 95vw;
            background: var(--bg-secondary);
            border-radius: 24px;
            border: 1px solid var(--border-color);
            box-shadow: var(--shadow-glow), 0 25px 60px rgba(0,0,0,0.5);
            overflow: hidden;
            animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes slideUp {
            from { opacity: 0; transform: translateY(40px) scale(0.96); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .header {
            padding: 16px 20px 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header h1 {
            font-size: 14px;
            font-weight: 500;
            color: var(--text-secondary);
            letter-spacing: 1px;
        }

        .mode-indicator {
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 20px;
            background: rgba(123, 47, 247, 0.15);
            color: var(--accent-purple);
            border: 1px solid rgba(123, 47, 247, 0.3);
            font-weight: 500;
        }

        .display {
            padding: 12px 24px 20px;
        }

        .expression {
            font-family: 'JetBrains Mono', monospace;
            font-size: 15px;
            color: var(--text-secondary);
            text-align: left;
            direction: ltr;
            min-height: 24px;
            overflow-x: auto;
            white-space: nowrap;
            padding: 4px 0;
            scrollbar-width: none;
        }

        .expression::-webkit-scrollbar { display: none; }

        .result {
            font-family: 'JetBrains Mono', monospace;
            font-size: 42px;
            font-weight: 600;
            color: var(--text-primary);
            text-align: left;
            direction: ltr;
            overflow-x: auto;
            white-space: nowrap;
            padding: 4px 0;
            scrollbar-width: none;
            transition: all 0.2s ease;
        }

        .result::-webkit-scrollbar { display: none; }

        .result.computing {
            color: var(--accent-blue);
        }

        .memory-bar {
            display: flex;
            gap: 4px;
            padding: 0 20px 12px;
        }

        .memory-bar button {
            flex: 1;
            padding: 6px;
            font-size: 11px;
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
            background: rgba(6, 214, 160, 0.08);
            color: var(--accent-green);
            border: 1px solid rgba(6, 214, 160, 0.15);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .memory-bar button:hover {
            background: rgba(6, 214, 160, 0.18);
            border-color: rgba(6, 214, 160, 0.4);
        }

        .memory-bar button.active {
            background: rgba(6, 214, 160, 0.25);
            border-color: var(--accent-green);
        }

        .mode-tabs {
            display: flex;
            padding: 0 20px;
            gap: 4px;
            margin-bottom: 12px;
        }

        .mode-tab {
            flex: 1;
            padding: 8px;
            font-size: 12px;
            font-weight: 500;
            background: transparent;
            color: var(--text-secondary);
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            font-family: 'IBM Plex Sans Arabic', sans-serif;
        }

        .mode-tab.active {
            background: var(--bg-button);
            color: var(--text-primary);
        }

        .mode-tab:hover:not(.active) {
            color: var(--text-primary);
        }

        .buttons-container {
            padding: 0 12px 16px;
        }

        .btn-grid {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 6px;
        }

        .btn-grid.basic-grid {
            grid-template-columns: repeat(4, 1fr);
        }

        button.calc-btn {
            font-family: 'JetBrains Mono', monospace;
            font-size: 15px;
            font-weight: 500;
            padding: 14px 6px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.15s ease;
            position: relative;
            overflow: hidden;
            background: var(--bg-button);
            color: var(--text-primary);
        }

        button.calc-btn::after {
            content: '';
            position: absolute;
            inset: 0;
            background: radial-gradient(circle at center, rgba(255,255,255,0.1) 0%, transparent 70%);
            opacity: 0;
            transition: opacity 0.3s;
        }

        button.calc-btn:active::after {
            opacity: 1;
        }

        button.calc-btn:hover {
            background: var(--bg-button-hover);
            transform: translateY(-1px);
        }

        button.calc-btn:active {
            transform: scale(0.96);
        }

        button.calc-btn.operator {
            background: rgba(76, 201, 240, 0.1);
            color: var(--accent-blue);
            border: 1px solid rgba(76, 201, 240, 0.15);
        }

        button.calc-btn.operator:hover {
            background: rgba(76, 201, 240, 0.2);
        }

        button.calc-btn.func {
            background: rgba(123, 47, 247, 0.1);
            color: var(--accent-purple);
            border: 1px solid rgba(123, 47, 247, 0.15);
            font-size: 13px;
        }

        button.calc-btn.func:hover {
            background: rgba(123, 47, 247, 0.2);
        }

        button.calc-btn.equals {
            background: linear-gradient(135deg, var(--accent-orange), #ff8c42);
            color: #fff;
            font-size: 20px;
            font-weight: 700;
        }

        button.calc-btn.equals:hover {
            background: linear-gradient(135deg, #ff7b47, #ffa060);
            box-shadow: 0 4px 20px rgba(255, 107, 53, 0.35);
        }

        button.calc-btn.clear {
            background: rgba(239, 71, 111, 0.1);
            color: var(--accent-red);
            border: 1px solid rgba(239, 71, 111, 0.15);
        }

        button.calc-btn.clear:hover {
            background: rgba(239, 71, 111, 0.2);
        }

        button.calc-btn.number {
            background: var(--bg-card);
            font-size: 17px;
        }

        button.calc-btn.number:hover {
            background: #22223a;
        }

        button.calc-btn.span2 {
            grid-column: span 2;
        }

        .history-panel {
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            background: var(--bg-primary);
            border-top: 1px solid var(--border-color);
        }

        .history-panel.open {
            max-height: 200px;
        }

        .history-panel-inner {
            padding: 12px 20px;
            max-height: 200px;
            overflow-y: auto;
        }

        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            cursor: pointer;
            transition: color 0.2s;
            direction: ltr;
        }

        .history-item:hover {
            color: var(--accent-blue);
        }

        .history-item:last-child {
            border-bottom: none;
        }

        .history-expr {
            color: var(--text-secondary);
        }

        .history-result {
            color: var(--accent-orange);
            font-weight: 600;
        }

        .history-toggle {
            width: 100%;
            padding: 8px;
            background: transparent;
            border: none;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 12px;
            cursor: pointer;
            font-family: 'IBM Plex Sans Arabic', sans-serif;
            transition: color 0.2s;
        }

        .history-toggle:hover {
            color: var(--text-primary);
        }

        @media (max-width: 480px) {
            .calculator-wrapper {
                padding: 10px;
                height: 100vh;
                display: flex;
                align-items: center;
            }
            .calculator {
                width: 100%;
                border-radius: 24px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            }
            .result {
                font-size: 40px;
                padding-right: 4px;
            }
            .buttons-container {
                padding: 0 16px 20px;
            }
            .btn-grid {
                gap: 8px;
            }
            button.calc-btn {
                padding: 16px 0;
                font-size: 18px;
                border-radius: 14px;
            }
            button.calc-btn.func {
                font-size: 13px;
                padding: 12px 0;
            }
            .mode-tabs {
                padding: 0 16px;
                margin-bottom: 16px;
            }
            .mode-tab {
                padding: 10px;
                font-size: 14px;
            }
        }
    </style>
</head>
<body>
    <div class="calculator-wrapper">
        <div class="calculator">
            <div class="header">
                <h1>حاسبة علمية</h1>
                <span class="mode-indicator" id="modeLabel">RAD</span>
            </div>

            <div class="display">
                <div class="expression" id="expression"></div>
                <div class="result" id="result">0</div>
            </div>

            <div class="memory-bar">
                <button onclick="memoryClear()">MC</button>
                <button onclick="memoryRecall()">MR</button>
                <button onclick="memoryAdd()">M+</button>
                <button onclick="memorySub()">M−</button>
                <button onclick="memoryStore()">MS</button>
            </div>

            <div class="mode-tabs">
                <button class="mode-tab active" onclick="switchMode('scientific', this)">علمية</button>
                <button class="mode-tab" onclick="switchMode('basic', this)">أساسية</button>
            </div>

            <div class="buttons-container">
                <!-- Scientific Mode -->
                <div class="btn-grid" id="scientificGrid">
                    <button class="calc-btn func" onclick="toggleAngle()">RAD</button>
                    <button class="calc-btn func" onclick="appendFunc('sin(')">sin</button>
                    <button class="calc-btn func" onclick="appendFunc('cos(')">cos</button>
                    <button class="calc-btn func" onclick="appendFunc('tan(')">tan</button>
                    <button class="calc-btn func" onclick="appendFunc('log(')">log</button>

                    <button class="calc-btn func" onclick="toggleInverse()">INV</button>
                    <button class="calc-btn func" id="sinBtn" onclick="appendFunc('asin(')">sin⁻¹</button>
                    <button class="calc-btn func" id="cosBtn" onclick="appendFunc('acos(')">cos⁻¹</button>
                    <button class="calc-btn func" id="tanBtn" onclick="appendFunc('atan(')">tan⁻¹</button>
                    <button class="calc-btn func" onclick="appendFunc('ln(')">ln</button>

                    <button class="calc-btn func" onclick="append('π')">π</button>
                    <button class="calc-btn func" onclick="append('e')">e</button>
                    <button class="calc-btn func" onclick="appendFunc('√(')">√</button>
                    <button class="calc-btn func" onclick="append('^')">xʸ</button>
                    <button class="calc-btn func" onclick="appendFunc('abs(')">|x|</button>

                    <button class="calc-btn func" onclick="append('(')"> (</button>
                    <button class="calc-btn func" onclick="append(')')">)</button>
                    <button class="calc-btn func" onclick="append('!')">n!</button>
                    <button class="calc-btn func" onclick="append('%')">%</button>
                    <button class="calc-btn clear" onclick="clearAll()">AC</button>

                    <button class="calc-btn number" onclick="append('7')">7</button>
                    <button class="calc-btn number" onclick="append('8')">8</button>
                    <button class="calc-btn number" onclick="append('9')">9</button>
                    <button class="calc-btn operator" onclick="append('÷')">÷</button>
                    <button class="calc-btn clear" onclick="backspace()">⌫</button>

                    <button class="calc-btn number" onclick="append('4')">4</button>
                    <button class="calc-btn number" onclick="append('5')">5</button>
                    <button class="calc-btn number" onclick="append('6')">6</button>
                    <button class="calc-btn operator" onclick="append('×')">×</button>
                    <button class="calc-btn func" onclick="append('^2')">x²</button>

                    <button class="calc-btn number" onclick="append('1')">1</button>
                    <button class="calc-btn number" onclick="append('2')">2</button>
                    <button class="calc-btn number" onclick="append('3')">3</button>
                    <button class="calc-btn operator" onclick="append('−')">−</button>
                    <button class="calc-btn func" onclick="append('^3')">x³</button>

                    <button class="calc-btn number" onclick="append('0')">0</button>
                    <button class="calc-btn number" onclick="append('.')">.</button>
                    <button class="calc-btn equals" onclick="calculate()">=</button>
                    <button class="calc-btn operator" onclick="append('+')">+</button>
                    <button class="calc-btn func" onclick="append('×10^')">EXP</button>
                </div>

                <!-- Basic Mode -->
                <div class="btn-grid basic-grid" id="basicGrid" style="display:none;">
                    <button class="calc-btn clear" onclick="clearAll()">AC</button>
                    <button class="calc-btn clear" onclick="backspace()">⌫</button>
                    <button class="calc-btn operator" onclick="append('%')">%</button>
                    <button class="calc-btn operator" onclick="append('÷')">÷</button>

                    <button class="calc-btn number" onclick="append('7')">7</button>
                    <button class="calc-btn number" onclick="append('8')">8</button>
                    <button class="calc-btn number" onclick="append('9')">9</button>
                    <button class="calc-btn operator" onclick="append('×')">×</button>

                    <button class="calc-btn number" onclick="append('4')">4</button>
                    <button class="calc-btn number" onclick="append('5')">5</button>
                    <button class="calc-btn number" onclick="append('6')">6</button>
                    <button class="calc-btn operator" onclick="append('−')">−</button>

                    <button class="calc-btn number" onclick="append('1')">1</button>
                    <button class="calc-btn number" onclick="append('2')">2</button>
                    <button class="calc-btn number" onclick="append('3')">3</button>
                    <button class="calc-btn operator" onclick="append('+')">+</button>

                    <button class="calc-btn number span2" onclick="append('0')">0</button>
                    <button class="calc-btn number" onclick="append('.')">.</button>
                    <button class="calc-btn equals" onclick="calculate()">=</button>
                </div>
            </div>

            <button class="history-toggle" onclick="toggleHistory()">
                📜 سجل العمليات
            </button>
            <div class="history-panel" id="historyPanel">
                <div class="history-panel-inner" id="historyList"></div>
            </div>
        </div>
    </div>

    <script>
        let expression = '';
        let currentResult = '0';
        let memory = 0;
        let isRadians = true;
        let isInverse = false;
        let history = [];

        const exprEl = document.getElementById('expression');
        const resultEl = document.getElementById('result');

        function updateDisplay() {
            exprEl.textContent = expression;
            resultEl.textContent = currentResult;
            exprEl.scrollLeft = exprEl.scrollWidth;
            resultEl.scrollLeft = resultEl.scrollWidth;
        }

        function append(val) {
            expression += val;
            updateDisplay();
            liveEvaluate();
        }

        function appendFunc(func) {
            expression += func;
            updateDisplay();
        }

        function clearAll() {
            expression = '';
            currentResult = '0';
            updateDisplay();
        }

        function backspace() {
            // Remove multi-char functions
            const funcs = ['sin(', 'cos(', 'tan(', 'asin(', 'acos(', 'atan(', 'log(', 'ln(', 'abs(', '√(', '×10^'];
            for (let f of funcs) {
                if (expression.endsWith(f)) {
                    expression = expression.slice(0, -f.length);
                    updateDisplay();
                    liveEvaluate();
                    return;
                }
            }
            expression = expression.slice(0, -1);
            updateDisplay();
            liveEvaluate();
        }

        function toggleAngle() {
            isRadians = !isRadians;
            document.getElementById('modeLabel').textContent = isRadians ? 'RAD' : 'DEG';
            document.querySelector('.btn-grid .func').textContent = isRadians ? 'RAD' : 'DEG';
        }

        function toggleInverse() {
            isInverse = !isInverse;
            // Visual indicator handled by button styles
        }

        function factorial(n) {
            if (n < 0) return NaN;
            if (n === 0 || n === 1) return 1;
            if (n > 170) return Infinity;
            let result = 1;
            for (let i = 2; i <= n; i++) result *= i;
            return result;
        }

        function preprocessExpression(expr) {
            let e = expr;
            // Replace symbols
            e = e.replace(/×/g, '*');
            e = e.replace(/÷/g, '/');
            e = e.replace(/−/g, '-');
            e = e.replace(/π/g, '(' + Math.PI + ')');
            e = e.replace(/(?<![a-zA-Z])e(?![a-zA-Z^+\-\d])/g, '(' + Math.E + ')');
            e = e.replace(/\^/g, '**');

            // Handle factorial
            e = e.replace(/(\d+)!/g, (_, n) => factorial(parseInt(n)));

            // Handle percentage
            e = e.replace(/(\d+\.?\d*)%/g, '($1/100)');

            // Trig functions
            if (isRadians) {
                e = e.replace(/sin\(/g, 'Math.sin(');
                e = e.replace(/cos\(/g, 'Math.cos(');
                e = e.replace(/tan\(/g, 'Math.tan(');
            } else {
                e = e.replace(/sin\(/g, 'Math.sin(Math.PI/180*(');
                e = e.replace(/cos\(/g, 'Math.cos(Math.PI/180*(');
                e = e.replace(/tan\(/g, 'Math.tan(Math.PI/180*(');
                // Add closing parens for degree conversion
                // This is simplified; complex nested expressions may need more handling
            }

            e = e.replace(/asin\(/g, 'Math.asin(');
            e = e.replace(/acos\(/g, 'Math.acos(');
            e = e.replace(/atan\(/g, 'Math.atan(');
            e = e.replace(/log\(/g, 'Math.log10(');
            e = e.replace(/ln\(/g, 'Math.log(');
            e = e.replace(/√\(/g, 'Math.sqrt(');
            e = e.replace(/abs\(/g, 'Math.abs(');
            e = e.replace(/×10\*\*/g, '*10**');

            return e;
        }

        function liveEvaluate() {
            if (!expression) {
                currentResult = '0';
                resultEl.classList.remove('computing');
                updateDisplay();
                return;
            }
            try {
                let processed = preprocessExpression(expression);
                // Balance parentheses
                let open = (processed.match(/\(/g) || []).length;
                let close = (processed.match(/\)/g) || []).length;
                processed += ')'.repeat(Math.max(0, open - close));
                // Add degree conversion closing parens
                if (!isRadians) {
                    let extra = (processed.match(/Math\.PI\/180\*\(/g) || []).length;
                    processed += ')'.repeat(extra);
                }

                let result = Function('"use strict"; return (' + processed + ')')();
                if (typeof result === 'number' && !isNaN(result)) {
                    resultEl.classList.add('computing');
                    currentResult = formatNumber(result);
                } else {
                    resultEl.classList.remove('computing');
                }
            } catch {
                resultEl.classList.remove('computing');
            }
            updateDisplay();
        }

        function calculate() {
            if (!expression) return;
            try {
                let processed = preprocessExpression(expression);
                let open = (processed.match(/\(/g) || []).length;
                let close = (processed.match(/\)/g) || []).length;
                processed += ')'.repeat(Math.max(0, open - close));
                if (!isRadians) {
                    let extra = (processed.match(/Math\.PI\/180\*\(/g) || []).length;
                    processed += ')'.repeat(extra);
                }

                let result = Function('"use strict"; return (' + processed + ')')();
                if (typeof result === 'number' && !isNaN(result)) {
                    let formatted = formatNumber(result);
                    history.unshift({ expr: expression, result: formatted });
                    if (history.length > 20) history.pop();
                    renderHistory();
                    expression = formatted;
                    currentResult = formatted;
                    resultEl.classList.remove('computing');
                    updateDisplay();

                    // Animation
                    resultEl.style.transform = 'scale(1.05)';
                    setTimeout(() => resultEl.style.transform = 'scale(1)', 150);
                } else {
                    currentResult = 'خطأ';
                    updateDisplay();
                }
            } catch {
                currentResult = 'خطأ';
                updateDisplay();
            }
        }

        function formatNumber(n) {
            if (Number.isInteger(n) && Math.abs(n) < 1e15) return n.toString();
            if (Math.abs(n) > 1e15 || (Math.abs(n) < 1e-6 && n !== 0)) {
                return n.toExponential(8);
            }
            let s = parseFloat(n.toPrecision(12)).toString();
            return s;
        }

        // Memory functions
        function memoryClear() { memory = 0; }
        function memoryRecall() { if (memory !== 0) append(memory.toString()); }
        function memoryAdd() {
            let val = parseFloat(currentResult);
            if (!isNaN(val)) memory += val;
        }
        function memorySub() {
            let val = parseFloat(currentResult);
            if (!isNaN(val)) memory -= val;
        }
        function memoryStore() {
            let val = parseFloat(currentResult);
            if (!isNaN(val)) memory = val;
        }

        // Mode switching
        function switchMode(mode, btn) {
            document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            if (mode === 'scientific') {
                document.getElementById('scientificGrid').style.display = 'grid';
                document.getElementById('basicGrid').style.display = 'none';
            } else {
                document.getElementById('scientificGrid').style.display = 'none';
                document.getElementById('basicGrid').style.display = 'grid';
            }
        }

        // History
        function toggleHistory() {
            document.getElementById('historyPanel').classList.toggle('open');
        }

        function renderHistory() {
            const list = document.getElementById('historyList');
            list.innerHTML = history.map(h =>
                `<div class="history-item" onclick="useHistory('${h.result}')">
                    <span class="history-expr">${h.expr}</span>
                    <span class="history-result">= ${h.result}</span>
                </div>`
            ).join('');
        }

        function useHistory(val) {
            expression = val;
            currentResult = val;
            updateDisplay();
        }

        // Keyboard support
        document.addEventListener('keydown', (e) => {
            const key = e.key;
            if ('0123456789.'.includes(key)) append(key);
            else if (key === '+') append('+');
            else if (key === '-') append('−');
            else if (key === '*') append('×');
            else if (key === '/') { e.preventDefault(); append('÷'); }
            else if (key === '%') append('%');
            else if (key === '(' || key === ')') append(key);
            else if (key === '^') append('^');
            else if (key === 'Enter' || key === '=') { e.preventDefault(); calculate(); }
            else if (key === 'Backspace') backspace();
            else if (key === 'Escape' || key === 'Delete') clearAll();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
