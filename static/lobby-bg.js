(function () {
  const cv = document.createElement('canvas');
  cv.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;z-index:0;pointer-events:none';
  document.body.insertBefore(cv, document.body.firstChild);
  const ctx = cv.getContext('2d');
  let W, H, t = 0;

  function resize() { W = cv.width = window.innerWidth; H = cv.height = window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);

  const img = new Image();
  img.src = '/static/cat-normal.png';

  function drawBackground() {
    ctx.fillStyle = '#ddd9bf';
    ctx.fillRect(0, 0, W, H);
    if (!img.complete || img.naturalWidth === 0) return;
    const scale = Math.max(W / img.naturalWidth, H / img.naturalHeight);
    const dw = img.naturalWidth * scale;
    const dh = img.naturalHeight * scale;
    ctx.drawImage(img, 0, H - dh, dw, dh);
  }

  /* ── Sparkles ── */
  const sparkles = Array.from({ length: 55 }, () => ({
    x: Math.random(), y: Math.random() * 0.75,
    r: Math.random() * 1.6 + 0.3,
    phase: Math.random() * Math.PI * 2,
    spd: Math.random() * 0.018 + 0.005,
    dx: (Math.random() - 0.5) * 0.00008,
    dy: (Math.random() - 0.5) * 0.00004,
  }));

  function drawSparkles() {
    sparkles.forEach(s => {
      s.phase += s.spd; s.x += s.dx; s.y += s.dy;
      if (s.x < 0) s.x = 1; if (s.x > 1) s.x = 0;
      if (s.y < 0) s.y = 0.74; if (s.y > 0.75) s.y = 0;
      const a = 0.25 + Math.sin(s.phase) * 0.4;
      const sx = s.x * W, sy = s.y * H;
      ctx.beginPath(); ctx.arc(sx, sy, s.r * 3, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${a * 0.12})`; ctx.fill();
      ctx.beginPath(); ctx.arc(sx, sy, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,255,255,${a * 0.9})`; ctx.fill();
      if (s.r > 1.1 && a > 0.45) {
        const len = s.r * 3.5;
        ctx.strokeStyle = `rgba(255,255,255,${a * 0.5})`; ctx.lineWidth = 0.6;
        ctx.beginPath(); ctx.moveTo(sx - len, sy); ctx.lineTo(sx + len, sy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(sx, sy - len); ctx.lineTo(sx, sy + len); ctx.stroke();
      }
    });
  }

  /* ── Fireflies ── */
  const ff = Array.from({ length: 18 }, () => ({
    x: 0.1 + Math.random() * 0.8, y: 0.08 + Math.random() * 0.6,
    vx: (Math.random() - 0.5) * 0.0012, vy: (Math.random() - 0.5) * 0.0009,
    phase: Math.random() * Math.PI * 2, blinkSpd: Math.random() * 0.035 + 0.012,
    wobble: Math.random() * Math.PI * 2, wobSpd: Math.random() * 0.03 + 0.012,
    r: Math.random() * 2.0 + 1.0,
  }));

  function updateFireflies() {
    ff.forEach(f => {
      f.wobble += f.wobSpd; f.phase += f.blinkSpd;
      f.x += f.vx + Math.sin(f.wobble) * 0.00025;
      f.y += f.vy + Math.cos(f.wobble * 0.7) * 0.00018;
      if (f.x < 0.03) f.vx =  Math.abs(f.vx);
      if (f.x > 0.97) f.vx = -Math.abs(f.vx);
      if (f.y < 0.03) f.vy =  Math.abs(f.vy);
      if (f.y > 0.78) f.vy = -Math.abs(f.vy);
      f.vx *= 0.996; f.vy *= 0.996;
    });
  }

  function drawFireflies() {
    ff.forEach(f => {
      const a = (Math.sin(f.phase) * 0.5 + 0.5) * 0.85;
      const fx = f.x * W, fy = f.y * H;
      ctx.beginPath(); ctx.arc(fx, fy, f.r * 5, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(200,180,80,${a * 0.08})`; ctx.fill();
      ctx.beginPath(); ctx.arc(fx, fy, f.r * 2.5, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(230,210,100,${a * 0.22})`; ctx.fill();
      ctx.beginPath(); ctx.arc(fx, fy, f.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255,240,140,${a})`; ctx.fill();
    });
  }

  function draw() {
    t += 0.016;
    ctx.clearRect(0, 0, W, H);
    drawBackground();
    drawSparkles();
    updateFireflies();
    drawFireflies();
    requestAnimationFrame(draw);
  }
  draw();
})();