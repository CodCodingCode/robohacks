/*
 * annotations.js — draw bounding-box overlays on the camera feed canvases.
 *
 * Reads an `annotations` array from the dashboard state and renders
 * colored rectangles + labels on a <canvas> positioned over the camera
 * <img>. The coordinate system is Gemini's native [y_min, x_min, y_max, x_max]
 * normalised 0–1000.
 */

(function (global) {
  const COLORS = {
    threat: "#ff4444",
    person: "#00ccff",
    wire: "#ffaa00",
    device: "#ff4444",
    component: "#ffaa00",
    object: "#00ff88",
  };

  const DEFAULT_COLOR = "#888888";

  /**
   * Render bounding-box annotations on a canvas overlay.
   *
   * @param {Array}  annotations  Array of {label, bbox:[y0,x0,y1,x1], category}
   * @param {string} canvasId     ID of the <canvas> overlay element
   * @param {string} imgId        ID of the <img> underneath (for sizing)
   */
  function renderAnnotations(annotations, canvasId, imgId) {
    const canvas = document.getElementById(canvasId);
    const img = document.getElementById(imgId);
    if (!canvas || !img) return;

    const ctx = canvas.getContext("2d");

    // Match canvas pixel buffer to displayed size of the camera wrap.
    const wrap = canvas.parentElement;
    const w = wrap.clientWidth;
    const h = wrap.clientHeight;

    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w;
      canvas.height = h;
    }

    ctx.clearRect(0, 0, w, h);

    if (!annotations || annotations.length === 0) return;

    for (const ann of annotations) {
      const bbox = ann.bbox;
      if (!bbox || bbox.length !== 4) continue;

      // Gemini format: [y_min, x_min, y_max, x_max] in 0–1000
      const x0 = (bbox[1] / 1000) * w;
      const y0 = (bbox[0] / 1000) * h;
      const x1 = (bbox[3] / 1000) * w;
      const y1 = (bbox[2] / 1000) * h;
      const bw = x1 - x0;
      const bh = y1 - y0;

      const color = COLORS[ann.category] || DEFAULT_COLOR;

      // Box
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.strokeRect(x0, y0, bw, bh);

      // Corner accents (tactical look)
      const corner = Math.min(12, bw * 0.15, bh * 0.15);
      ctx.lineWidth = 3;
      // Top-left
      ctx.beginPath();
      ctx.moveTo(x0, y0 + corner);
      ctx.lineTo(x0, y0);
      ctx.lineTo(x0 + corner, y0);
      ctx.stroke();
      // Top-right
      ctx.beginPath();
      ctx.moveTo(x1 - corner, y0);
      ctx.lineTo(x1, y0);
      ctx.lineTo(x1, y0 + corner);
      ctx.stroke();
      // Bottom-left
      ctx.beginPath();
      ctx.moveTo(x0, y1 - corner);
      ctx.lineTo(x0, y1);
      ctx.lineTo(x0 + corner, y1);
      ctx.stroke();
      // Bottom-right
      ctx.beginPath();
      ctx.moveTo(x1 - corner, y1);
      ctx.lineTo(x1, y1);
      ctx.lineTo(x1, y1 - corner);
      ctx.stroke();

      // Label background + text
      if (ann.label) {
        ctx.font = "bold 11px monospace";
        const text = ann.label.toUpperCase();
        const tm = ctx.measureText(text);
        const pad = 4;
        const lx = x0;
        const ly = y0 - 18;

        ctx.fillStyle = "rgba(0, 0, 0, 0.7)";
        ctx.fillRect(lx, ly, tm.width + pad * 2, 16);

        ctx.fillStyle = color;
        ctx.fillText(text, lx + pad, ly + 12);
      }
    }
  }

  global.ReconAnnotations = { renderAnnotations };
})(window);
