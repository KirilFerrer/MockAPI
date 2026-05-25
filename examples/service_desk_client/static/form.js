document.addEventListener('DOMContentLoaded', async () => {
  const { apiSend, isObject, payloadFromForm, recordId, requestedId, showAlert } = window.Northstar;
  const form = document.getElementById('resource-form');
  const resource = document.body.dataset.resource;
  const mode = document.body.dataset.mode;
  const id = requestedId();

  if (mode === 'edit') {
    if (!id) {
      showAlert('No se ha indicado el identificador del registro.');
      form.hidden = true;
      return;
    }
    const result = await apiSend('GET', `/${resource}/${encodeURIComponent(id)}`);
    if (!result.ok || !isObject(result.data)) {
      showAlert(result.error || 'No se pudo cargar el registro.');
      form.hidden = true;
      return;
    }
    fillForm(form, result.data);
  }

  form.addEventListener('submit', async event => {
    event.preventDefault();
    const payload = payloadFromForm(form);
    const result = mode === 'edit'
      ? await apiSend('PATCH', `/${resource}/${encodeURIComponent(id)}`, payload)
      : await apiSend('POST', `/${resource}`, payload);
    if (!result.ok) {
      showAlert(result.error);
      return;
    }
    const savedId = recordId(result.data) || id;
    window.location.assign(savedId ? `/${resource}/detail.html?id=${encodeURIComponent(savedId)}` : `/${resource}/`);
  });
});

function fillForm(form, item) {
  Object.entries(item).forEach(([name, value]) => {
    const field = form.elements.namedItem(name);
    if (field) field.value = value ?? '';
  });
}
