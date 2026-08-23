(() => {
  const body = document.body;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  body.classList.add('home-motion');

  const motionGroups = [
    ['.hero .eyebrow, .hero h1, .hero__inner>p, .hero .search, .hero .stats', 'up'],
    ['.results--home .section-title, .home-list-cta, .digital-tour-card', 'up'],
    ['.cards--home-preview .card', 'scale'],
    ['.memory-journey__intro', 'left'],
    ['.memory-journey li', 'right'],
    ['.about-dropcap, .about-lead>div, .about-photo--wide', 'up'],
    ['.about-history>*:first-child, .about-homecoming>*:first-child, .about-stele>*:first-child', 'left'],
    ['.about-history>*:last-child, .about-homecoming>*:last-child, .about-stele>*:last-child', 'right'],
    ['.about-final>*', 'up'],
  ];

  const items = [];
  motionGroups.forEach(([selector, type]) => {
    document.querySelectorAll(selector).forEach((element, index) => {
      element.dataset.motion = type;
      element.style.setProperty('--motion-delay', `${Math.min(index % 8, 7) * 65}ms`);
      items.push(element);
    });
  });

  body.classList.add('motion-ready');
  document.querySelectorAll('.hero [data-motion]').forEach((element) => element.classList.add('is-visible'));

  if (reduceMotion || !('IntersectionObserver' in window)) {
    items.forEach((element) => element.classList.add('is-visible'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
    items.filter((element) => !element.closest('.hero')).forEach((element) => observer.observe(element));
  }

  const header = document.querySelector('.site-header');
  const heroInner = document.querySelector('.hero__inner');
  const parallaxItems = [
    document.querySelector('.digital-tour-card__visual'),
    document.querySelector('.about-photo--wide img'),
    document.querySelector('.about-homecoming__image img'),
  ].filter(Boolean);
  parallaxItems.forEach((element) => { element.dataset.parallax = 'image'; });
  let ticking = false;
  const updateScrollEffects = () => {
    const y = window.scrollY;
    header?.classList.toggle('is-scrolled', y > 18);
    if (heroInner && !reduceMotion && window.innerWidth > 760 && y < 700) {
      heroInner.style.transform = `translate3d(0,${Math.min(y * 0.075, 32)}px,0)`;
    }
    if (!reduceMotion && window.innerWidth > 760) {
      const viewportCenter = window.innerHeight / 2;
      parallaxItems.forEach((element) => {
        const rect = element.getBoundingClientRect();
        if (rect.bottom < -120 || rect.top > window.innerHeight + 120) return;
        const delta = (rect.top + rect.height / 2 - viewportCenter) / window.innerHeight;
        element.style.setProperty('--parallax-y', `${Math.max(-18,Math.min(18,delta * -24)).toFixed(1)}px`);
      });
    }
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(updateScrollEffects);
  }, { passive: true });
  updateScrollEffects();

  document.querySelectorAll('.home-list-cta').forEach((element) => {
    element.addEventListener('pointermove', (event) => {
      const rect = element.getBoundingClientRect();
      element.style.setProperty('--mx', `${event.clientX - rect.left}px`);
      element.style.setProperty('--my', `${event.clientY - rect.top}px`);
    }, { passive: true });
  });
})();
