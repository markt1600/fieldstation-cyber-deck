(() => {
  const card = document.createElement('section');
  card.id = 'air-quality';
  card.hidden = true;
  card.setAttribute('aria-label', 'Live particulate readings');
  card.innerHTML = '<div><span class="eyebrow">AIR QUALITY</span><p id="air-status">Connecting to sensor…</p></div><div class="air-measurement"><span id="air-label">PM1.0</span><strong id="air-value">—</strong><span>µg/m³</span></div><button id="air-next" type="button" aria-label="Show next particulate measurement">1 / 3 →</button>';
  const statusRow=document.createElement('section');statusRow.id='home-status';statusRow.setAttribute('aria-label','Live station status');document.querySelector('.intro').after(statusRow);statusRow.append(card);
  const metrics = [['PM1.0', 'pm1'], ['PM2.5', 'pm25'], ['PM10', 'pm10']];
  let index = 0, sample = null, received = 0, next = Date.now() + 5000;
  function paint() {
    card.hidden = document.getElementById('home').hidden;
    statusRow.hidden=card.hidden;document.body.classList.toggle('home-view',!card.hidden);
    const age = sample ? (sample.age_seconds || 0) + (Date.now() - received) / 1000 : Infinity;
    const live = sample?.status === 'live' && age < 15;
    document.getElementById('air-label').textContent = metrics[index][0];
    document.getElementById('air-value').textContent = live ? sample.readings[metrics[index][1]] : '—';
    document.getElementById('air-status').textContent = live ? 'Live · cycles every 5 seconds' : sample?.status === 'waiting' ? 'Waiting for sensor readings' : 'Sensor readings unavailable';
    document.getElementById('air-next').textContent = `${index + 1} / 3 →`;
  }
  document.getElementById('air-next').onclick = () => { index = (index + 1) % 3; next = Date.now() + 5000; paint(); };
  async function poll() {
    try {
      const r = await fetch('/api/air-quality', {cache: 'no-store', signal: AbortSignal.timeout(4000)});
      if (!r.ok) throw Error();
      sample = await r.json(); received = Date.now();
    } catch { sample = null; }
    paint(); setTimeout(poll, 3000);
  }
  new MutationObserver(paint).observe(document.getElementById('home'), {attributes:true, attributeFilter:['hidden']});
  setInterval(() => { if (!card.hidden && Date.now() >= next) { index = (index + 1) % 3; next = Date.now() + 5000; } paint(); }, 1000);
  poll();
})();
