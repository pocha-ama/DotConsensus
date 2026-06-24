"use strict";
// ── 多要素平均化課題（de Gardelle & Summerfield 2011）────────────────────────
//  8つの色要素を円周上に配置。各色は赤(+1)〜青(-1)軸上の値。
//  「平均して赤色か青色か」を判断。静止提示なので話し合い中の参照に向く。
//
//  de Gardelle & Summerfield (2011) では複数の要素の平均的特徴を統合判断させる。
//  本実装は色（赤-青軸）上の8要素の平均極性を判断する課題として構成する。
window.PILOT_STIM = window.PILOT_STIM || {};
window.PILOT_STIM.avg = {
    run(api) {
        const { ctx, CX, CY, TIME_LIMIT, drawCross, setStart, endTrial } = api;

        const colors    = JSON.parse(js_vars.colors);   // -1..+1 の配列
        const nEl       = js_vars.n_elements;            // 8
        const RING_R    = 150;   // 配置円の半径
        const EL_R      = 32;    // 各要素の半径

        // 色値 v(-1..+1) を RGB に変換（+1=赤, -1=青, 0=紫）
        function valToColor(v) {
            // v=+1 → (255,0,0) 赤, v=-1 → (0,57,255) 青, 中間は線形補間
            const t = (v + 1) / 2;  // 0..1
            const r = Math.round(255 * t);
            const g = 0;
            const b = Math.round(255 * (1 - t));
            return `rgb(${r}, ${g}, ${b})`;
        }

        // 8要素を円周上に配置
        const positions = [];
        for (let i = 0; i < nEl; i++) {
            const th = (2 * Math.PI * i / nEl) - Math.PI/2;
            positions.push({ x: CX + RING_R * Math.cos(th), y: CY + RING_R * Math.sin(th) });
        }

        function render() {
            ctx.clearRect(0, 0, api.W, api.H);
            drawCross();
            for (let i = 0; i < nEl; i++) {
                const p = positions[i];
                ctx.beginPath();
                ctx.arc(p.x, p.y, EL_R, 0, Math.PI * 2);
                ctx.fillStyle = valToColor(colors[i]);
                ctx.fill();
            }
        }

        // 静止提示：TIME_LIMIT 秒間そのまま表示して終了
        setStart();
        render();
        setTimeout(endTrial, 1500);
    }
};