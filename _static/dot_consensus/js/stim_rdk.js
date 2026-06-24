"use strict";
// ── ランダムドット運動課題（Rajananda, Lau & Odegaard 2018 準拠）─────────────
//  coherence% のドットが正解方向に固定で動き続け、残りはランダム方向に動く。
//  各ドットの役割（コヒーレント/ノイズ）は初期化時に固定する。
//  コヒーレントドットは毎フレーム必ず正解方向に動き、アパーチャ外に出たら再配置。
//  ノイズドットは毎フレームランダムな方向に同速度で移動する（random direction 方式）。
window.PILOT_STIM = window.PILOT_STIM || {};
window.PILOT_STIM.rdk = {
    run(api) {
        const { ctx, CX, CY, TIME_LIMIT, rand, drawCross, setStart, endTrial } = api;

        const direction  = js_vars.direction;       // 'left' or 'right'
        const coherence  = js_vars.coherence / 100; // 割合
        const N          = js_vars.n_dots;          // ドット数
        const DOT_R      = js_vars.dot_radius;      // 半径(px)
        const SPEED      = js_vars.dot_speed;       // px/frame
        const APERTURE_R = 190;

        const dirSign = (direction === 'right') ? 1 : -1;

        // ── ヘルパー関数 ─────────────────────────────────────────────────
        function inAperture(x, y) {
            return Math.hypot(x - CX, y - CY) <= (APERTURE_R - DOT_R);
        }

        function randInAperture() {
            const r  = Math.sqrt(Math.random()) * (APERTURE_R - DOT_R);
            const th = rand(0, Math.PI * 2);
            return { x: CX + r * Math.cos(th), y: CY + r * Math.sin(th) };
        }

        // ── ドット初期化：役割を固定で割り当て ──────────────────────────
        const nCoherent = Math.round(N * coherence);

        // Fisher-Yates シャッフルで役割をランダムに割り当て
        const roleArr = new Array(N).fill(false);
        for (let i = 0; i < nCoherent; i++) roleArr[i] = true;
        for (let i = N - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            const tmp = roleArr[i]; roleArr[i] = roleArr[j]; roleArr[j] = tmp;
        }

        const dots = [];
        for (let i = 0; i < N; i++) {
            const p = randInAperture();
            // ノイズドットには初期ランダム方向を割り当て
            const angle = rand(0, Math.PI * 2);
            dots.push({ x: p.x, y: p.y, coherent: roleArr[i], angle: angle });
        }

        // ── 毎フレームの更新 ────────────────────────────────────────────
        function step() {
            for (let i = 0; i < N; i++) {
                if (dots[i].coherent) {
                    // コヒーレント：毎フレーム必ず正解方向に移動
                    dots[i].x += dirSign * SPEED;
                    dots[i].y += rand(-0.3, 0.3);
                } else {
                    // ノイズ：ランダムな方向に同速度で移動
                    // フレームごとに方向をわずかにランダムに変化させる
                    dots[i].angle += rand(-0.3, 0.3);
                    dots[i].x += Math.cos(dots[i].angle) * SPEED;
                    dots[i].y += Math.sin(dots[i].angle) * SPEED;
                }
                // アパーチャ外に出たら反対側からランダムに再登場
                if (!inAperture(dots[i].x, dots[i].y)) {
                    const p = randInAperture();
                    dots[i].x = p.x;
                    dots[i].y = p.y;
                    // ノイズドットは再登場時に新しいランダム方向を割り当て
                    if (!dots[i].coherent) {
                        dots[i].angle = rand(0, Math.PI * 2);
                    }
                }
            }
        }

        function drawOuter() {
            ctx.beginPath();
            ctx.arc(CX, CY, APERTURE_R + 10, 0, Math.PI * 2);
            ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.stroke();
        }

        function render() {
            ctx.clearRect(0, 0, api.W, api.H);
            drawCross();
            ctx.fillStyle = "white";
            for (let i = 0; i < N; i++) {
                ctx.beginPath();
                ctx.arc(dots[i].x, dots[i].y, DOT_R, 0, Math.PI * 2);
                ctx.fill();
            }
            drawOuter();
        }

        // ── メインループ ────────────────────────────────────────────────
        let nLoop = 0;
        const totalLoops = TIME_LIMIT * 60;

        function loop() {
            if (nLoop >= totalLoops) { endTrial(); return; }
            if (nLoop === 0) setStart();
            step();
            render();
            nLoop++;
            requestAnimationFrame(loop);
        }
        loop();
    }
};