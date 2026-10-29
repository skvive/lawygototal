/** Brand home: newsletter API + public feed hook */
(function () {
  const form = document.querySelector('#newsletterSignup');
  if (form) {
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = document.querySelector('#newsletterResult');
      if (msg) msg.textContent = '구독 신청을 확인하고 있습니다.';
      const data = {
        email: document.querySelector('#newsletterEmail')?.value,
        consent: document.querySelector('#newsletterConsent')?.checked,
      };
      try {
        const r = await fetch('/api/growth/newsletter/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });
        const j = await r.json();
        if (!r.ok) throw new Error(typeof j.detail === 'string' ? j.detail : '신청을 완료할 수 없습니다.');
        if (msg) msg.textContent = j.message;
        form.reset();
      } catch (x) {
        if (msg) {
          msg.textContent = x.message;
          msg.className = 'error';
        }
      }
    });
  }
})();
