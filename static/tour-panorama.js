(() => {
  const element = document.getElementById('real-panorama-viewer');
  if (!element || !window.pannellum) return;
  const viewer = pannellum.viewer(element, {
    type: 'equirectangular',
    panorama: element.dataset.panorama,
    autoLoad: true,
    autoRotate: -1.2,
    autoRotateInactivityDelay: 4500,
    compass: true,
    showZoomCtrl: true,
    showFullscreenCtrl: false,
    keyboardZoom: true,
    mouseZoom: true,
    hfov: 105,
    minHfov: 45,
    maxHfov: 120,
    pitch: -8,
    yaw: 0,
    strings: {
      loadButtonLabel: 'Mở không gian 360°',
      loadingLabel: 'Đang tải…',
      bylineLabel: 'Nguồn: %s',
      noPanoramaError: 'Không thể tải ảnh 360°.',
      fileAccessError: 'Không thể truy cập ảnh 360°.',
      malformedURLError: 'Đường dẫn ảnh không hợp lệ.'
    }
  });
  element.classList.add('is-initialized');
  viewer.on('load', () => element.classList.add('is-loaded'));
  const fullscreenButton = document.getElementById('panorama-fullscreen');
  const isNativeFullscreen = () => document.fullscreenElement || document.webkitFullscreenElement;
  const updateFullscreen = active => {
    element.classList.toggle('is-fallback-fullscreen', active && !isNativeFullscreen());
    fullscreenButton.classList.toggle('is-active', active);
    fullscreenButton.setAttribute('aria-pressed', String(active));
    fullscreenButton.setAttribute('aria-label', active ? 'Thoát toàn màn hình' : 'Xem toàn màn hình');
    document.body.classList.toggle('panorama-is-fullscreen', active);
    setTimeout(() => viewer.resize(), 80);
  };
  fullscreenButton?.addEventListener('click', async event => {
    event.stopPropagation();
    const active = isNativeFullscreen() || element.classList.contains('is-fallback-fullscreen');
    if (active) {
      if (isNativeFullscreen()) {
        const exit = document.exitFullscreen || document.webkitExitFullscreen;
        if (exit) await exit.call(document);
      } else updateFullscreen(false);
      return;
    }
    const request = element.requestFullscreen || element.webkitRequestFullscreen;
    if (request) {
      try { await request.call(element); }
      catch { updateFullscreen(true); }
    } else updateFullscreen(true);
  });
  ['fullscreenchange', 'webkitfullscreenchange'].forEach(name => document.addEventListener(name, () => updateFullscreen(Boolean(isNativeFullscreen()))));
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && element.classList.contains('is-fallback-fullscreen')) updateFullscreen(false); });
})();
