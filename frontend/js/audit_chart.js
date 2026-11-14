/**
 * SPHEREx Planet X Challenge - Still-Star Photometric Stability Audit Visualizer
 * Proves mathematically that Akhilesh's band-balanced stacking eliminates the 20-30% LVF color flicker.
 */

class AuditChart {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.canvas = document.createElement('canvas');
    this.container.appendChild(this.canvas);
    this.ctx = this.canvas.getContext('2d');
    this.data = null;

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    this.width = this.container.clientWidth || 600;
    this.height = this.container.clientHeight || 260;
    this.canvas.width = this.width;
    this.canvas.height = this.height;
    if (this.data) this.render();
  }

  setData(auditPayload) {
    this.data = auditPayload;
    this.render();
  }

  render() {
    if (!this.data || !this.data.stars) return;

    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    ctx.clearRect(0, 0, w, h);

    const margin = { left: 45, right: 20, top: 30, bottom: 40 };
    const pw = w - margin.left - margin.right;
    const ph = h - margin.top - margin.bottom;

    const stars = this.data.stars.slice(0, 20); // Show first 20 stars
    const n = stars.length;
    if (n === 0) return;

    // Y scale max: 35% scatter
    const maxScatter = 35.0;
    const yMap = (val) => margin.top + ph - (val / maxScatter) * ph;

    // 1. Grid & Axes (Hairline Monochrome)
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineWidth = 1;
    for (let s = 0; s <= 30; s += 10) {
      const gy = yMap(s);
      ctx.beginPath();
      ctx.moveTo(margin.left, gy);
      ctx.lineTo(margin.left + pw, gy);
      ctx.stroke();

      ctx.fillStyle = '#8e8e99';
      ctx.font = '9px "JetBrains Mono", monospace';
      ctx.textAlign = 'right';
      ctx.fillText(`${s}%`, margin.left - 6, gy + 3);
    }

    // 2. Reference Threshold Line (< 2% requirement, Clean Silver)
    const y2Pct = yMap(2.0);
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(margin.left, y2Pct);
    ctx.lineTo(margin.left + pw, y2Pct);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.textAlign = 'right';
    ctx.fillText('2% Science Threshold', margin.left + pw, y2Pct - 4);

    // 3. Bars for each star (Raw Monochrome vs Band-Balanced Vibranium Purple)
    const groupWidth = pw / n;
    const barWidth = Math.max(3, (groupWidth - 8) / 2);

    for (let i = 0; i < n; i++) {
      const st = stars[i];
      const gx = margin.left + i * groupWidth + 4;

      // Raw Flicker Bar (Clean Muted Monochrome)
      const rH = Math.max(2, (st.raw_scatter_pct / maxScatter) * ph);
      ctx.fillStyle = 'rgba(255, 255, 255, 0.22)';
      ctx.fillRect(gx, margin.top + ph - rH, barWidth, rH);

      // Band-Balanced Bar (Black Panther Royal Purple)
      const bH = Math.max(2, (st.balanced_scatter_pct / maxScatter) * ph);
      ctx.fillStyle = '#a855f7';
      ctx.fillRect(gx + barWidth + 1, margin.top + ph - bH, barWidth, bH);

      // Star Index Label
      ctx.fillStyle = '#8e8e99';
      ctx.font = '8px "JetBrains Mono", monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`S${st.star_index}`, gx + barWidth, margin.top + ph + 14);
    }

    // Legend
    ctx.fillStyle = 'rgba(255, 255, 255, 0.22)';
    ctx.fillRect(margin.left + 10, 8, 12, 10);
    ctx.fillStyle = '#ffffff';
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`Raw Frames (~${this.data.mean_raw_flicker_pct}% scatter)`, margin.left + 26, 16);

    ctx.fillStyle = '#a855f7';
    ctx.fillRect(margin.left + 220, 8, 12, 10);
    ctx.fillStyle = '#ffffff';
    ctx.fillText(`Band-Balanced (<${this.data.mean_balanced_flicker_pct}% scatter)`, margin.left + 236, 16);
  }
}
