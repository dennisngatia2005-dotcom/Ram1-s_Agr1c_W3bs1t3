/* AgriSoc Kenya — main.js */

/* Flash auto-dismiss */
document.querySelectorAll('.flash').forEach(el => setTimeout(() => el.remove(), 5500));

/* Tabs */
document.querySelectorAll('.tabs-wrapper').forEach(wrapper => {
  const btns   = wrapper.querySelectorAll('.tab-btn');
  const panels = wrapper.querySelectorAll('.tab-panel');
  btns.forEach(btn => btn.addEventListener('click', () => {
    btns.forEach(b => b.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    wrapper.querySelector('#' + btn.dataset.target)?.classList.add('active');
  }));
  if (btns[0]) { btns[0].classList.add('active'); panels[0]?.classList.add('active'); }
});

/* Stat counter animation */
function animateCounter(el) {
  const target = parseFloat(el.dataset.target);
  if (isNaN(target)) return;
  const isCurrency = el.dataset.prefix === 'KES ';
  const duration = 1400, step = 16;
  let current = 0;
  const inc = target / (duration / step);
  const t = setInterval(() => {
    current = Math.min(current + inc, target);
    const val = Math.round(current).toLocaleString();
    el.textContent = (el.dataset.prefix || '') + val;
    if (current >= target) clearInterval(t);
  }, step);
}
const io = new IntersectionObserver(entries => entries.forEach(e => {
  if (e.isIntersecting) {
    e.target.querySelectorAll('[data-target]').forEach(animateCounter);
    io.unobserve(e.target);
  }
}), { threshold: 0.25 });
document.querySelectorAll('.hero-stats-row,.stats-bar,.admin-stat-grid').forEach(el => io.observe(el));

/* Resource filter */
const filterBtns = document.querySelectorAll('.filter-btn');
filterBtns.forEach(btn => btn.addEventListener('click', () => {
  filterBtns.forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const f = btn.dataset.filter;
  document.querySelectorAll('.resource-item').forEach(c => {
    c.style.display = (f === 'all' || c.dataset.type === f) ? '' : 'none';
  });
}));

/* Simple search filter for admin member table */
const memberSearch = document.getElementById('live-search');
if (memberSearch) {
  memberSearch.addEventListener('input', () => {
    const q = memberSearch.value.toLowerCase();
    document.querySelectorAll('.member-row').forEach(row => {
      row.style.display = row.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}