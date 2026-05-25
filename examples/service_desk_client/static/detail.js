document.addEventListener('DOMContentLoaded', async () => {
  const { apiSend, isObject, requestedId, showAlert, text } = window.Northstar;
  const resource = document.body.dataset.resource;
  const id = requestedId();

  if (!id) {
    showAlert('No se ha indicado el identificador del registro.');
    document.getElementById('detail-empty').hidden = false;
    return;
  }

  document.getElementById('edit-link').href = `/${resource}/edit.html?id=${encodeURIComponent(id)}`;
  const result = await apiSend('GET', `/${resource}/${encodeURIComponent(id)}`);
  if (!result.ok || !isObject(result.data)) {
    showAlert(result.error || 'No se pudo cargar el registro.');
    document.getElementById('detail-empty').hidden = false;
    return;
  }

  document.getElementById('detail-panel').hidden = false;
  document.querySelectorAll('[data-value]').forEach(element => {
    text(element.id, result.data[element.dataset.value] || 'Sin dato');
  });

  document.getElementById('delete-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (!window.confirm('¿Eliminar este registro?')) return;
    const deleted = await apiSend('DELETE', `/${resource}/${encodeURIComponent(id)}`);
    if (!deleted.ok) {
      showAlert(deleted.error);
      return;
    }
    window.location.assign(`/${resource}/`);
  });
});
