"use strict";
// ══════════════════════════════════════════════════════════════════════════
//  Chat ページの刺激参照ポップアップ用レンダラ
//  参照可能な課題（rdk / avg）のみ。Task と同じ js_vars・同じシードで
//  刺激を再現する（問題内で刺激は同一なので見えるものは同じ）。
//  モーダル内の固定サイズ canvas に描画する。
// ══════════════════════════════════════════════════════════════════════════
(function () {
    if (!js_vars || !js_vars.can_review) return;

    const taskType = js_vars.task_type;
    const WRAP_ID  = "review-canvas-wrap";

    let rafId = null;
    let canvas = null, ctx = null;

    function setupCanvas() {
        const wrap = document.getElementById(WRAP_ID);
        if (!wrap) return false;
        wrap.innerHTML = "";
        canvas = document.createElement("canvas");
        canvas.width  = wrap.clientWidth  || 740;
        canvas.height = wrap.clientHeight || 480;
        canvas.style.display = "block";
        wrap.appendChild(canvas);
        ctx = canvas.getContext("2d");
        return true;
    }

    function stop() {
        if (rafId) { cancelAnimationFrame(rafId); rafId = null; }
    }

    // ── 共通：背景と注視点 ──
    function clearBg() {
        ctx.fillStyle = "black";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // ── RDK 再現（Task の stim_rdk と同じロジック・同じシード）──
    function runRDK() {
        Math.seedrandom(js_vars.seed);
        const CX = canvas.width / 2, CY = canvas.height / 2;
        const direction = js_vars.direction;
        const coherence = js_vars.coherence / 100;
        const N = js_vars.n_dots, DOT_R = js_vars.dot_radius, SPEED = js_vars.dot_speed;
        const APERTURE_R = Math.min(CX, CY) - 20;
        const dirSign = (direction === 'right') ? 1 : -1;
        function randInAp() {
            const r = Math.sqrt(Math.random()) * (APERTURE_R - DOT_R);
            const th = Math.random() * Math.PI * 2;
            return { x: CX + r*Math.cos(th), y: CY + r*Math.sin(th) };
        }
        function inAp(x,y){ return Math.hypot(x-CX,y-CY) <= (APERTURE_R-DOT_R); }
        let dots = [];
        for (let i=0;i<N;i++){ dots.push(randInAp()); }
        function step(){
            for (let i=0;i<N;i++){
                if (Math.random() < coherence){
                    dots[i].x += dirSign*SPEED;
                    dots[i].y += (Math.random()-0.5);
                    if (!inAp(dots[i].x,dots[i].y)){ const p=randInAp(); dots[i]=p; }
                } else { const p=randInAp(); dots[i]=p; }
            }
        }
        function render(){
            clearBg();
            ctx.strokeStyle="white"; ctx.lineWidth=2;
            ctx.beginPath(); ctx.arc(CX,CY,APERTURE_R+10,0,Math.PI*2); ctx.stroke();
            // 注視点
            ctx.beginPath(); ctx.moveTo(CX-20,CY); ctx.lineTo(CX+20,CY);
            ctx.moveTo(CX,CY-20); ctx.lineTo(CX,CY+20); ctx.stroke();
            ctx.fillStyle="white";
            for (let i=0;i<N;i++){ ctx.beginPath(); ctx.arc(dots[i].x,dots[i].y,DOT_R,0,Math.PI*2); ctx.fill(); }
        }
        function loop(){ step(); render(); rafId = requestAnimationFrame(loop); }
        loop();
    }

    // ── avg 再現（静止）──
    function runAVG() {
        const CX = canvas.width / 2, CY = canvas.height / 2;
        const colors = JSON.parse(js_vars.colors);
        const nEl = js_vars.n_elements;
        const RING_R = Math.min(CX, CY) - 60;
        const EL_R = 32;
        function valToColor(v){
            const t=(v+1)/2;
            return `rgb(${Math.round(255*t)},0,${Math.round(255*(1-t))})`;
        }
        clearBg();
        // 注視点
        ctx.strokeStyle="white"; ctx.lineWidth=2;
        ctx.beginPath(); ctx.moveTo(CX-20,CY); ctx.lineTo(CX+20,CY);
        ctx.moveTo(CX,CY-20); ctx.lineTo(CX,CY+20); ctx.stroke();
        for (let i=0;i<nEl;i++){
            const th=(2*Math.PI*i/nEl)-Math.PI/2;
            const x=CX+RING_R*Math.cos(th), y=CY+RING_R*Math.sin(th);
            ctx.beginPath(); ctx.arc(x,y,EL_R,0,Math.PI*2);
            ctx.fillStyle=valToColor(colors[i]); ctx.fill();
        }
    }

    function start() {
        if (!setupCanvas()) return;
        stop();
        if (taskType === 'rdk') runRDK();
        else if (taskType === 'avg') runAVG();
    }

    // モーダル表示/非表示に合わせて描画開始・停止（Bootstrap 4 イベント）
    window.addEventListener('load', function () {
        const openBtn = document.getElementById('open-review');
        if (openBtn && window.jQuery) {
            $('#reviewModal').on('shown.bs.modal', start);
            $('#reviewModal').on('hidden.bs.modal', stop);
            openBtn.addEventListener('click', function () { $('#reviewModal').modal('show'); });
        }
    });
})();