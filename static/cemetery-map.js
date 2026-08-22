(() => {
  const map = document.getElementById('cemetery-map');
  const dialog = document.getElementById('grave-dialog');
  if (!map || !dialog) return;
  const canvas = dialog.querySelector('.zone-map');
  const wrap = dialog.querySelector('.zone-map-wrap');
  const loading = dialog.querySelector('.zone-map-loading');
  const input = dialog.querySelector('input');
  const inspector = dialog.querySelector('.grave-inspector');
  const zoomLabel = dialog.querySelector('.grave-zoom span');
  let zone = '', graves = [], scale = 1, timer;
  const esc = value => String(value).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const rowNumber = value => Number((String(value).match(/\d+/) || [99999])[0]);

  const render = () => {
    const query = input.value.trim().toLocaleLowerCase('vi');
    const groups = new Map();
    graves.filter(g => g.row && g.number && g.row !== '0' && g.number !== '0').forEach(g => { if (!groups.has(g.row)) groups.set(g.row, []); groups.get(g.row).push(g); });
    const rows = [...groups.entries()].sort((a,b) => rowNumber(a[0]) - rowNumber(b[0]));
    const maxColumns = Math.max(1, ...rows.map(([, items]) => items.length));
    canvas.style.setProperty('--grave-columns', maxColumns);
    canvas.innerHTML = `<div class="zone-map__gate"><i></i>CỔNG KHU ${esc(zone)}</div>` + rows.map(([row, items]) => `<section class="grave-row" data-row="${esc(row)}"><header><span>HÀNG</span><b>${esc(row)}</b></header><div>${items.sort((a,b)=>rowNumber(a.number)-rowNumber(b.number)).map(g => { const hit = query && `${g.name} ${g.row} ${g.number}`.toLocaleLowerCase('vi').includes(query); return `<button type="button" class="grave-plot${hit?' is-match':''}${query&&!hit?' is-dimmed':''}" data-id="${g.id}" aria-label="${esc(g.name)}, hàng ${esc(g.row)}, mộ ${esc(g.number)}"><i></i><span class="grave-plot__name">${esc(g.name || 'Chưa rõ tên')}</span><span class="grave-plot__number">${esc(g.number)}</span></button>`; }).join('')}</div></section>`).join('');
    const missing = graves.filter(g => !g.row || !g.number || g.row === '0' || g.number === '0');
    if (missing.length) canvas.insertAdjacentHTML('beforeend', `<section class="grave-unpositioned"><strong>${missing.length} hồ sơ chưa đủ tọa độ hàng/số mộ</strong><span>Được giữ ngoài bản đồ để tránh đặt sai vị trí.</span></section>`);
    canvas.style.setProperty('--map-scale', scale);
    canvas.querySelectorAll('.grave-plot').forEach(button => button.addEventListener('click', () => select(graves.find(g => String(g.id) === button.dataset.id), button)));
    if (query) canvas.querySelector('.is-match')?.scrollIntoView({behavior:'smooth',block:'center',inline:'center'});
  };
  const select = (grave, button) => {
    canvas.querySelector('.is-selected')?.classList.remove('is-selected'); button.classList.add('is-selected');
    inspector.querySelector('h3').textContent = grave.name;
    inspector.querySelector('p').textContent = `Khu ${zone} · Hàng ${grave.row} · Mộ số ${grave.number}`;
    inspector.querySelector('a').href = grave.url; inspector.classList.add('is-visible');
  };
  const load = async () => {
    loading.hidden = false; canvas.hidden = true; inspector.classList.remove('is-visible');
    try {
      const response = await fetch(`/trai-nghiem-360/khu-mo/${encodeURIComponent(zone)}/?view=map`);
      if (!response.ok) throw new Error(); const data = await response.json(); graves = data.results;
      dialog.querySelector('.grave-dialog__head p strong').textContent = new Intl.NumberFormat('vi-VN').format(data.count);
      dialog.querySelector('.grave-dialog__head p em').textContent = `${new Intl.NumberFormat('vi-VN').format(data.positioned)} mộ đã định vị`;
      loading.hidden = true; canvas.hidden = false; render(); wrap.scrollTo({top:0,left:0});
    } catch { loading.textContent = 'Chưa thể dựng bản đồ. Vui lòng thử lại.'; }
  };
  map.querySelectorAll('.map3d-zone').forEach(button => button.addEventListener('click', () => {
    zone = button.dataset.zone; scale = 1; input.value = ''; zoomLabel.textContent = '100%';
    dialog.querySelector('h2 b').textContent = zone; dialog.querySelector('.grave-dialog__tools>a').href = `/danh-sach-liet-si/?zone=${encodeURIComponent(zone)}`;
    dialog.showModal(); document.body.classList.add('scene-open'); load();
  }));
  dialog.querySelector('.grave-dialog__close').onclick = () => dialog.close();
  inspector.querySelector('button').onclick = () => inspector.classList.remove('is-visible');
  dialog.addEventListener('click', e => { if (e.target === dialog) dialog.close(); });
  dialog.addEventListener('close', () => document.body.classList.remove('scene-open'));
  input.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(render, 180); });
  dialog.querySelectorAll('.grave-zoom button').forEach(button => button.onclick = () => { scale = Math.max(.7, Math.min(1.6, scale + (button.dataset.zoom === 'in' ? .15 : -.15))); zoomLabel.textContent = `${Math.round(scale*100)}%`; canvas.style.setProperty('--map-scale', scale); });
})();
