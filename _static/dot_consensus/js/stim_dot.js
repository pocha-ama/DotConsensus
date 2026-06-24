"use strict";
window.PILOT_STIM = window.PILOT_STIM || {};
window.PILOT_STIM.dot = {
    run(api) {
        const { ctx, CX, CY, FPS, TIME_LIMIT, rand, drawCross, setStart, endTrial } = api;

        const DOT_R       = 6;
        const APERTURE_R  = 190;
        const OUTER_R     = 200;
        const CROSS_SZ    = 40;
        const nDots       = js_vars.n_dots;
        const nBlueList   = JSON.parse(js_vars.n_blue);

        function drawOuter() {
            ctx.beginPath();
            ctx.arc(CX, CY, OUTER_R, 0, Math.PI * 2);
            ctx.strokeStyle = "white"; ctx.lineWidth = 2; ctx.stroke();
        }
        function drawDots(frameIdx) {
            const xs = [], ys = [];
            const nBlue = nBlueList[Math.min(frameIdx, nBlueList.length - 1)];
            for (let i = 0; i < nDots; i++) {
                let x, y;
                while (true) {
                    const r = rand(CROSS_SZ/2 + DOT_R, APERTURE_R);
                    const th = rand(0, Math.PI * 2);
                    x = Math.round(r * Math.cos(th) + CX);
                    y = Math.round(r * Math.sin(th) + CY);
                    if (i === 0) break;
                    let ok = true;
                    for (let j = 0; j < xs.length; j++) {
                        if (Math.hypot(xs[j]-x, ys[j]-y) < DOT_R*2) { ok = false; break; }
                    }
                    if (ok) break;
                }
                xs.push(x); ys.push(y);
                ctx.beginPath();
                ctx.arc(x, y, DOT_R, 0, Math.PI * 2);
                ctx.fillStyle = (i < nBlue) ? "rgb(0, 57, 255)" : "red";
                ctx.fill();
            }
        }

        let nLoop = 0, nFrame = 0;
        const framesPerUpdate = Math.round(60 / FPS);
        const totalLoops = TIME_LIMIT * 60;

        function loop() {
            if (nLoop >= totalLoops) { endTrial(); return; }
            if (nLoop % framesPerUpdate === 0) {
                ctx.clearRect(0, 0, api.W, api.H);
                drawCross();
                drawDots(nFrame);
                drawOuter();
                nFrame++;
            }
            if (nLoop === 0) setStart();
            nLoop++;
            requestAnimationFrame(loop);
        }
        loop();
    }
};