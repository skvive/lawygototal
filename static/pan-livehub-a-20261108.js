/* PAN A LiveHub micro-interaction: original RSS/CMS endpoints and viewer untouched */
(() => {
  'use strict';
  const form = document.getElementById('pan-hub-search');
  const field = document.getElementById('pan-hub-query');
  const heroField = document.getElementById('pan-hero-search');
  const initial = new URLSearchParams(location.search).get('q') || '';
  if (field) field.value = initial;
  form?.addEventListener('submit', (event) => {
    event.preventDefault();
    const q = (field?.value || '').trim().slice(0, 160);
    if (heroField) heroField.value = q;
    const url = new URL(location.href);
    if (q) url.searchParams.set('q', q); else url.searchParams.delete('q');
    history.replaceState(null, '', url.pathname + url.search);
    document.getElementById('pan-refresh-feed')?.click();
    document.getElementById('pan-content')?.scrollIntoView({behavior:'smooth',block:'start'});
  });
  const navLinks = Array.from(document.querySelectorAll('.pan-side-nav a[href^="#"]'));
  navLinks.forEach(link => link.addEventListener('click', () => {
    document.querySelectorAll('.pan-side-nav a').forEach(a => {
      a.classList.remove('is-current'); a.removeAttribute('aria-current');
    });
    link.classList.add('is-current'); link.setAttribute('aria-current', 'location');
  }));
})();