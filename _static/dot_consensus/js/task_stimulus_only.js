"use strict;"

// ── 刺激パラメータ（task_fixation.js と同一） ─────────────────────────────────
const dotRadius    = 6;
const apertureRadius = 190;
const outerRadius  = 200;

const backgroundColor = "black";
const outerCenterX = window.innerWidth  / 2;
const outerCenterY = window.innerHeight / 2;

const fixationCrossSize      = 40;
const fixationCrossColor     = "white";
const fixationCrossThickness = 2;

// ── js_vars から受け取るパラメータ ─────────────────────────────────────────
const fps      = js_vars.fps;
const nDots    = js_vars.n_dots;
const nBlueList = JSON.parse(js_vars.n_blue);
const nRedList  = JSON.parse(js_vars.n_red);
const seed      = js_vars.seed;
const timeLimit = 10;   // 秒（experiment_settings.py の TIME_LIMIT と合わせる）
const iti       = 1000; // fixation cross 表示時間 (ms)

// ── Canvas セットアップ（task_fixation.js と同一） ──────────────────────────
let canvas = document.createElement("canvas");
document.body.appendChild(canvas);
let body = document.body;

body.style.margin          = 0;
body.style.padding         = 0;
body.style.backgroundColor = backgroundColor;

canvas.style.margin     = 0;
canvas.style.padding    = 0;
canvas.style.position   = "absolute";
canvas.style.top        = 0;
canvas.style.left       = 0;
canvas.style.cursor     = "none";

let ctx = canvas.getContext("2d");
ctx.imageSmoothingEnabled = true;

const canvasWidth  = canvas.width  = window.innerWidth;
const canvasHeight = canvas.height = window.innerHeight;
canvas.style.backgroundColor = backgroundColor;

// ── 乱数シードを設定（task_fixation.js と同一） ─────────────────────────────
Math.seedrandom(seed);

// ── タイミング変数 ────────────────────────────────────────────────────────────
let startTime;
let startTimeGlobal = 0;

// ── 描画関数（task_fixation.js からそのまま） ─────────────────────────────────

function randomNumberBetween(lowerBound, upperBound) {
    return lowerBound + Math.random() * (upperBound - lowerBound);
}

function drawFixationCross() {
    ctx.beginPath();
    ctx.strokeStyle = "white";
    ctx.lineWidth   = fixationCrossThickness;
    ctx.moveTo(canvasWidth / 2 - fixationCrossSize / 2, canvasHeight / 2);
    ctx.lineTo(canvasWidth / 2 + fixationCrossSize / 2, canvasHeight / 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.strokeStyle = "white";
    ctx.lineWidth   = fixationCrossThickness;
    ctx.moveTo(canvasWidth / 2, canvasHeight / 2 - fixationCrossSize / 2);
    ctx.lineTo(canvasWidth / 2, canvasHeight / 2 + fixationCrossSize / 2);
    ctx.stroke();
}

function drawOuterCircle(color = "white", lineWidth = 2) {
    ctx.beginPath();
    ctx.arc(outerCenterX, outerCenterY, outerRadius, 0, Math.PI * 2);
    ctx.strokeStyle = color;
    ctx.lineWidth   = lineWidth;
    ctx.stroke();
}

function drawDots(n = nDots) {
    let dotX = [], dotY = [];
    for (let i = 0; i < n; i++) {
        while (true) {
            const r     = randomNumberBetween(fixationCrossSize / 2 + dotRadius, apertureRadius);
            const theta = randomNumberBetween(0, Math.PI * 2);
            const x     = Math.round(r * Math.cos(theta) + outerCenterX);
            const y     = Math.round(r * Math.sin(theta) + outerCenterY);
            if (i === 0) { dotX.push(x); dotY.push(y); break; }
            let noOverlap = true;
            for (let j = 0; j < dotX.length; j++) {
                if (Math.sqrt((dotX[j] - x) ** 2 + (dotY[j] - y) ** 2) < dotRadius * 2) {
                    noOverlap = false;
                    break;
                }
            }
            if (noOverlap) { dotX.push(x); dotY.push(y); break; }
        }
        ctx.beginPath();
        ctx.arc(dotX[i], dotY[i], dotRadius, 0, Math.PI * 2);
        ctx.fillStyle = (i < nBlueList[nFrame]) ? "rgb(0, 57, 255)" : "red";
        ctx.fill();
    }
    nFrame += 1;
}

// ── アニメーションループ（変更: 自動終了） ────────────────────────────────────
let nLoop  = 0;
let nFrame = 0;

function drawAnimation() {
    // TIME_LIMIT 秒経過で自動終了
    if (nLoop >= timeLimit * 60) {
        endTrial();
        return;
    }

    if (nLoop % Math.round(60 / fps) === 0) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        drawFixationCross();
        drawDots(nDots);
        drawOuterCircle();
    }

    // 最初のフレームでタイマー開始
    if (nLoop === 0) {
        startTime       = performance.now();
        startTimeGlobal = Date.now().toString(16);
    }

    nLoop++;
    requestAnimationFrame(drawAnimation);
}

// ── 試行終了（変更: time_start のみ送信） ─────────────────────────────────────
function endTrial() {
    const response = {
        type:       "data",
        time_start: startTimeGlobal,
    };

    // oTree の hidden フィールドに書き込む
    const taskdataInput =
        document.getElementById("id_taskdata") ||
        document.querySelector("input[name='taskdata']");
    if (taskdataInput) {
        taskdataInput.value = JSON.stringify(response);
    }

    // oTree フォームを送信
    const form =
        document.getElementById("form") ||
        document.getElementById("otree-form") ||
        document.querySelector("form");
    if (form) {
        form.submit();
    }
}

// ── 実行 ─────────────────────────────────────────────────────────────────────
drawFixationCross();
setTimeout(drawAnimation, iti);
