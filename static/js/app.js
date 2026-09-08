const menuToggle = document.querySelector('.menu-toggle');
if (menuToggle) menuToggle.addEventListener('click', () => {
  const menu = document.querySelector('#main-menu');
  const open = menu.classList.toggle('open');
  menuToggle.setAttribute('aria-expanded', String(open));
});

window.renderGroupsChart = (groups, onGroupSelect) => {
  const canvas = document.querySelector('#groups-chart');
  if (!canvas || !window.Chart) return;
  if (canvas._chartInstance) canvas._chartInstance.destroy();
  canvas._chartInstance = new window.Chart(canvas, { type: 'bar', data: { labels: groups.map((item) => item.group), datasets: [{ label: 'Saldo em aberto', data: groups.map((item) => Number(item.amount)), backgroundColor: '#9c7550', borderRadius: 4 }] }, options: { onClick: (_event, elements) => { if (elements.length && onGroupSelect) onGroupSelect(groups[elements[0].index]); }, responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => 'R$ ' + ctx.raw.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) } } }, scales: { y: { beginAtZero: true, ticks: { callback: (value) => 'R$ ' + Number(value).toLocaleString('pt-BR') } } } } });
};

window.renderCustomersChart = (customers, groupName) => {
  const canvas = document.querySelector('#customers-chart');
  if (!canvas || !window.Chart) return;
  const title = document.querySelector('#customers-chart-title');
  if (title) title.textContent = '10 maiores devedores — ' + groupName;
  if (canvas._chartInstance) canvas._chartInstance.destroy();
  canvas._chartInstance = new window.Chart(canvas, { type: 'bar', data: { labels: customers.map((item) => item.customer), datasets: [{ label: 'Saldo em aberto', data: customers.map((item) => Number(item.amount)), backgroundColor: '#3987e5', borderRadius: 4 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => 'R$ ' + ctx.raw.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) } } }, scales: { y: { beginAtZero: true, ticks: { callback: (value) => 'R$ ' + Number(value).toLocaleString('pt-BR') } } } } });
};

window.renderStateComparisonChart = (states) => {
  const canvas = document.querySelector('#state-delinquency-chart');
  if (!canvas || !window.Chart) return;
  if (canvas._chartInstance) canvas._chartInstance.destroy();
  canvas._chartInstance = new window.Chart(canvas, { type: 'bar', data: { labels: states.map((item) => item.state), datasets: [{ label: '% inadimplência', data: states.map((item) => Number(item.delinquency)), backgroundColor: '#d6a64f', borderRadius: 4 }] }, options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false }, tooltip: { callbacks: { label: (ctx) => Number(ctx.raw).toFixed(2) + '%' } } }, scales: { x: { beginAtZero: true, ticks: { callback: (value) => value + '%' } } } } });
};

document.querySelectorAll('[data-close-modal]').forEach((button) => {
  button.addEventListener('click', () => button.closest('dialog')?.close());
});

document.querySelectorAll('form[data-prevent-double-submit]').forEach((form) => {
  form.addEventListener('submit', (event) => {
    if (form.dataset.submitting === 'true') {
      event.preventDefault();
      return;
    }

    form.dataset.submitting = 'true';
    const submitter = event.submitter || form.querySelector('[type="submit"]');
    if (submitter) {
      submitter.disabled = true;
      submitter.setAttribute('aria-busy', 'true');
    }
  });
});
