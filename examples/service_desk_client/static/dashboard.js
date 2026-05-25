document.addEventListener('DOMContentLoaded', async () => {
  const { apiList, escapeHtml, linkFor, recordId, showAlert, text } = window.Northstar;
  const results = await Promise.all(['tickets', 'assets', 'vendors'].map(async resource => [
    resource,
    await apiList(resource)
  ]));
  const data = Object.fromEntries(results);
  const failures = results.filter(([, result]) => !result.ok);
  const tickets = data.tickets.items;
  const assets = data.assets.items;
  const vendors = data.vendors.items;

  if (failures.length) {
    showAlert(`No se pudieron cargar todos los datos: ${failures.map(([name]) => name).join(', ')}.`);
  }

  text('metric-open', countBy(tickets, 'status', ['open', 'in_progress', 'waiting']));
  text('metric-priority', countBy(tickets, 'priority', ['high', 'critical']));
  text('metric-assets', countBy(assets, 'status', ['online', 'assigned']));
  text('metric-vendors', countBy(vendors, 'status', ['active']));

  const recent = document.getElementById('recent-ticket-rows');
  const empty = document.getElementById('recent-ticket-empty');
  if (!tickets.length) {
    empty.hidden = false;
    return;
  }
  recent.innerHTML = tickets.slice(0, 5).map(ticket => {
    const id = recordId(ticket);
    return `
      <a class="compact-row" href="${linkFor('tickets', 'detail', id)}">
        <span>
          <strong>${escapeHtml(ticket.title || 'Ticket sin titulo')}</strong>
          <small>${escapeHtml(ticket.queue || ticket.assignee || 'Sin asignacion')}</small>
        </span>
        <em class="status">${escapeHtml(ticket.status || 'sin estado')}</em>
      </a>
    `;
  }).join('');
});

function countBy(items, field, expected) {
  return items.filter(item => expected.includes(String(item[field] || '').toLowerCase())).length;
}
