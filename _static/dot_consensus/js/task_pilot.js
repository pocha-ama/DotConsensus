"use strict";
const TASK_TYPE = js_vars.task_type;
const SEED = js_vars.seed;
const FPS = js_vars.fps;
const TIME_LIMIT = js_vars.time_limit;
const ITI = 1000;

const BG = (TASK_TYPE === 'gabor') ? "rgb(128,128,128)" : "black";
const CROSS_COLOR = (TASK_TYPE === 'gabor') ? "black" : "white";
const CROSS_SZ = 40;
const CROSS_TH = 2;

Math.seedrandom(SEED);
function rand(lo, hi) { return lo + Math.random() * (hi - lo); }

const canvas = document.createElement("canvas");
document.body.appendChild(canvas);
const body = document.body;
body.style.margin = 0; body.style.padding = 0; body.style.backgroundColor = BG;

canvas.style.position = "fixed";
canvas.style.top = "0";
canvas.style.left = "0";
canvas.style.zIndex = "9999";
canvas.style.margin = 0; canvas.style.padding = 0;
canvas.style.cursor = "none";

canvas.style.cursor = "none";
const ctx = canvas.getContext("2d");
ctx.imageSmoothingEnabled = true;
const W = canvas.width = window.innerWidth;
const H = canvas.height = window.innerHeight;
const CX = W / 2, CY = H / 2;
canvas.style.backgroundColor = BG;
ctx.fillStyle = BG;
ctx.fillRect(0, 0, W, H);

function drawCross() {
    ctx.beginPath(); ctx.strokeStyle = CROSS_COLOR; ctx.lineWidth = CROSS_TH;
    ctx.moveTo(CX - CROSS_SZ/2, CY); ctx.lineTo(CX + CROSS_SZ/2, CY); ctx.stroke();
    ctx.beginPath(); ctx.strokeStyle = CROSS_COLOR; ctx.lineWidth = CROSS_TH;
    ctx.moveTo(CX, CY - CROSS_SZ/2); ctx.lineTo(CX, CY + CROSS_SZ/2); ctx.stroke();
}

let startTime = 0;
let startTimeGlobal = "0";

function endTrial() {
    const response = { type: "data", time_start: startTimeGlobal, task_type: TASK_TYPE };
    const input = document.getElementById("id_taskdata") || document.querySelector("input[name='taskdata']");
    if (input) input.value = JSON.stringify(response);
    const form = document.getElementById("form") || document.getElementById("otree-form") || document.querySelector("form");
    if (form) form.submit();
}

const api = {
    ctx, W, H, CX, CY, FPS, TIME_LIMIT, ITI,
    rand, drawCross,
    setStart() {
        startTime = performance.now();
        startTimeGlobal = Date.now().toString(16);
    },
    getStartTime() { return startTime; },
    endTrial,
};

function launch() {
    const mod = (window.PILOT_STIM || {})[TASK_TYPE];
    if (!mod) {
        console.error("No stimulus module for task_type:", TASK_TYPE);
        drawCross();
        setTimeout(endTrial, ITI + TIME_LIMIT * 1000);
        return;
    }
    mod.run(api);
}

drawCross();
setTimeout(launch, ITI);
