"use strict";
// ── ガボールパッチ課題（Bahrami et al. 2010）────────────────────────────────
//  6つの垂直ガボールを円周上に等間隔配置。2区間（各約85ms）提示し、
//  片方の区間の1パッチのコントラストを上げてオッドボールを作る。
//  「1枚目/2枚目どちらにオッドボールがあったか」を判断。
//
//  刺激生成方式は Bahrami et al. (2010) に準拠：
//    ガウシアン包絡の標準偏差 0.45度・空間周波数 1.5 cycles/degree・基準コントラスト10%。
//  オンライン環境ではピクセル/視角の厳密な対応は取れないため、画面ピクセルで近似する。
window.PILOT_STIM = window.PILOT_STIM || {};
window.PILOT_STIM.gabor = {
    run(api) {
        const { ctx, CX, CY, drawCross, setStart, endTrial } = api;

        const nPatches        = js_vars.n_patches;          // 6
        const oddballInterval = js_vars.oddball_interval;   // 1 or 2
        const oddballPos      = js_vars.oddball_position;    // 0..5
        const baseContrast    = js_vars.base_contrast / 100; // 0.10
        const oddContrast     = (js_vars.base_contrast + js_vars.oddball_contrast) / 100;

        // ── ガボール描画パラメータ（ピクセル近似）──
        const PATCH_SIZE  = 120;   // パッチ1辺(px)
        const SF          = 0.08; // 空間周波数(cycles/px) 近似
        const SIGMA       = 18;   // ガウシアン包絡の標準偏差(px)
        const RING_R      = 180;  // パッチ配置円の半径(px)

        // 区間タイミング（Bahrami: 各85ms / 区間間1000ms 空白）
        const INTERVAL_MS = 85;
        const BLANK_MS    = 1000;

        // 1つのガボールパッチをオフスクリーンに生成して返す
        function makeGabor(contrast) {
            const off = document.createElement("canvas");
            off.width = PATCH_SIZE; off.height = PATCH_SIZE;
            const octx = off.getContext("2d");
            const img = octx.createImageData(PATCH_SIZE, PATCH_SIZE);
            const c = PATCH_SIZE / 2;
            for (let y = 0; y < PATCH_SIZE; y++) {
                for (let x = 0; x < PATCH_SIZE; x++) {
                    const dx = x - c, dy = y - c;
                    const grating = Math.sin(2 * Math.PI * SF * dx);
                    const env = Math.exp(-(dx*dx + dy*dy) / (2 * SIGMA * SIGMA));
                    const lum = 128 + 127 * contrast * grating * env;
                    const idx = (y * PATCH_SIZE + x) * 4;
                    img.data[idx] = img.data[idx+1] = img.data[idx+2] = lum;
                    img.data[idx+3] = 255;
                }
            }
            octx.putImageData(img, 0, 0);
            return off;
        }

        // 6パッチの配置（円周上に等間隔）
        const positions = [];
        for (let i = 0; i < nPatches; i++) {
            const th = (2 * Math.PI * i / nPatches) - Math.PI/2;
            positions.push({ x: CX + RING_R * Math.cos(th), y: CY + RING_R * Math.sin(th) });
        }

        // 区間を描く（interval=1 or 2）。該当区間ならオッドボール位置だけ高コントラスト。
        function drawInterval(interval) {
            ctx.fillStyle = "rgb(128, 128, 128)";
            ctx.fillRect(0, 0, api.W, api.H);
            drawCross();
            for (let i = 0; i < nPatches; i++) {
                const isOdd = (interval === oddballInterval) && (i === oddballPos);
                const patch = makeGabor(isOdd ? oddContrast : baseContrast);
                const p = positions[i];
                ctx.drawImage(patch, p.x - PATCH_SIZE/2, p.y - PATCH_SIZE/2);
            }
        }

        function drawBlank() {
            ctx.fillStyle = "rgb(128, 128, 128)";
            ctx.fillRect(0, 0, api.W, api.H);
            drawCross();
        }

        // シーケンス: 区間1(85ms) → 空白(1000ms) → 区間2(85ms) → 応答受付（提示終了）
        setStart();
        drawInterval(1);
        setTimeout(() => {
            drawBlank();
            setTimeout(() => {
                drawInterval(2);
                setTimeout(() => {
                    drawBlank();
                    // 提示完了 → 終了（Decision ページで応答）
                    setTimeout(endTrial, 300);
                }, INTERVAL_MS);
            }, BLANK_MS);
        }, INTERVAL_MS);
    }
};