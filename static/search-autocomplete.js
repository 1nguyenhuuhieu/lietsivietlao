(() => {
  const input = document.getElementById('martyr-search');
  const list = document.getElementById('search-suggestions');
  if (!input || !list) return;

  let timer;
  let controller;
  let active = -1;
  let items = [];

  const close = () => {
    list.hidden = true;
    list.replaceChildren();
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    active = -1;
    items = [];
  };

  const locationText = (item) => [
    item.zone && `Khu ${item.zone}`,
    item.grave_row && `Hàng ${item.grave_row}`,
    item.grave_number && `Mộ ${item.grave_number}`
  ].filter(Boolean).join(' · ');

  const choose = (index) => {
    const item = items[index];
    if (item) window.location.assign(item.url);
  };

  const setActive = (index) => {
    const options = [...list.querySelectorAll('[role="option"]')];
    options.forEach(option => { option.classList.remove('is-active'); option.setAttribute('aria-selected', 'false'); });
    active = index;
    if (options[index]) {
      options[index].classList.add('is-active');
      options[index].setAttribute('aria-selected', 'true');
      input.setAttribute('aria-activedescendant', options[index].id);
      options[index].scrollIntoView({block: 'nearest'});
    }
  };

  const render = (results) => {
    items = results;
    list.replaceChildren();
    if (!results.length) return close();
    results.forEach((item, index) => {
      const option = document.createElement('button');
      option.type = 'button';
      option.id = `suggestion-${index}`;
      option.className = 'suggestion';
      option.setAttribute('role', 'option');
      option.setAttribute('aria-selected', 'false');
      const title = document.createElement('strong');
      title.textContent = item.name || 'Chưa biết tên';
      const meta = document.createElement('span');
      meta.textContent = [item.hometown, locationText(item)].filter(Boolean).join(' — ') || 'Thông tin đang cập nhật';
      option.append(title, meta);
      const action = document.createElement('small');
      action.textContent = 'Mở hồ sơ →';
      option.append(action);
      option.addEventListener('pointerdown', event => {
        event.preventDefault();
        choose(index);
      });
      list.append(option);
    });
    list.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    active = -1;
  };

  const search = async () => {
    const query = input.value.trim();
    if (query.length < 2) return close();
    controller?.abort();
    controller = new AbortController();
    input.classList.add('is-searching');
    try {
      const response = await fetch(`/api/goi-y/?q=${encodeURIComponent(query)}`, {signal: controller.signal});
      if (!response.ok) return close();
      render((await response.json()).results || []);
    } catch (error) {
      if (error.name !== 'AbortError') close();
    } finally { input.classList.remove('is-searching'); }
  };

  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(search, 160);
  });
  input.addEventListener('keydown', event => {
    if (list.hidden && event.key !== 'Escape') return;
    if (event.key === 'ArrowDown') { event.preventDefault(); setActive(Math.min(active + 1, items.length - 1)); }
    else if (event.key === 'ArrowUp') { event.preventDefault(); setActive(Math.max(active - 1, 0)); }
    else if (event.key === 'Enter' && active >= 0) { event.preventDefault(); choose(active); }
    else if (event.key === 'Escape') close();
  });
  input.addEventListener('blur', () => setTimeout(close, 120));
  document.addEventListener('pointerdown', event => {
    if (!event.target.closest('.search-input-wrap')) close();
  });
})();
