const TABLE_COLUMNS = {
  tickets: ['title', 'priority', 'status', 'queue', 'assignee'],
  assets: ['name', 'asset_tag', 'status', 'owner', 'location'],
  vendors: ['name', 'category', 'status', 'owner', 'contact_email']
};

document.addEventListener('DOMContentLoaded', async () => {
  const { apiList, escapeHtml, linkFor, recordId, showAlert, text } = window.Northstar;
  const resource = document.body.dataset.resource;
  const result = await apiList(resource);
  text('record-count', String(result.items.length));
  if (!result.ok) showAlert(result.error);

  if (!result.items.length) {
    document.getElementById('records-empty').hidden = false;
    return;
  }

  const table = document.getElementById('records-table');
  table.hidden = false;
  table.querySelector('tbody').innerHTML = result.items.map(item => {
    const id = recordId(item);
    const cells = TABLE_COLUMNS[resource].map(field => {
      const value = escapeHtml(item[field] || 'sin dato');
      return `<td>${field === 'status' || field === 'priority' ? `<span class="tag">${value}</span>` : value}</td>`;
    }).join('');
    return `
      <tr>
        ${cells}
        <td class="actions">
          <a href="${linkFor(resource, 'detail', id)}">Detalle</a>
          <a href="${linkFor(resource, 'edit', id)}">Editar</a>
        </td>
      </tr>
    `;
  }).join('');
});
