(function () {
  const cv = document.createElement('canvas');
  cv.id = 'game-bg-canvas';
  cv.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none';
  document.body.insertBefore(cv, document.body.firstChild);
  const ctx = cv.getContext('2d');
  let W, H, t = 0;

  function resize() { W = cv.width = window.innerWidth; H = cv.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);

  const img = new Image();
  img.src = '/static/game-bg.png';

  function drawBackground() {
    ctx.fillStyle = '#d8d4b0';
    ctx.fillRect(0, 0, W, H);
    if (!img.complete || img.naturalWidth === 0) return;
    const scale = Math.max(W / img.naturalWidth, H / img.naturalHeight);
    const dw = img.naturalWidth * scale;
    const dh = img.naturalHeight * scale;
    // push down by 8% so the cat box sits lower and empty space below is hidden
    ctx.drawImage(img, 0, H - dh + H * 0.2, dw, dh);
  }

  const sparkles = Array.from({ length: 40 }, () => ({
    x: Math.random(), y: Math.random() * 0.7,
    r: Math.random() * 1.4 + 0.3,
    phase: Math.random() * Math.PI * 2,
    spd: Math.random() * 0.018 + 0.005,
    dx: (Math.random() - 0.5) * 0.00007,
    dy: (Math.random() - 0.5) * 0.00003,
  }));

  function drawSparkles() {
    sparkles.forEach(s => {
      s.phase += s.spd; s.x += s.dx; s.y += s.dy;
      if (s.x < 0) s.x = 1; if (s.x > 1) s.x = 0;
      if (s.y < 0) s.y = 0.68; if (s.y > 0.7) s.y = 0;
      const a = 0.2 + Math.sin(s.phase) * 0.38;
      const sx = s.x * W, sy = s.y * H;
      ctx.beginPath(); ctx.arc(sx, sy, s.r * 2.8, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${a * 0.1})`; ctx.fill();
      ctx.beginPath(); ctx.arc(sx, sy, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${a * 0.85})`; ctx.fill();
      if (s.r > 1.0 && a > 0.4) {
        ctx.strokeStyle = `rgba(255,255,255,${a * 0.4})`; ctx.lineWidth = 0.5;
        const sp = s.r * 3;
        ctx.beginPath(); ctx.moveTo(sx - sp, sy); ctx.lineTo(sx + sp, sy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(sx, sy - sp); ctx.lineTo(sx, sy + sp); ctx.stroke();
      }
    });
  }

  function draw() {
    t += 0.016;
    ctx.clearRect(0, 0, W, H);
    drawBackground();
    drawSparkles();
    requestAnimationFrame(draw);
  }
  draw();
})();