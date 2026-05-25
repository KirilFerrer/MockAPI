(function () {
  const STORAGE_KEY = 'northstar.apiBaseUrl.v2';
  const DEFAULT_API_BASE_URL = 'http://127.0.0.1:8000/mock';
  const COLLECTION_KEYS = ['items', 'tickets', 'assets', 'vendors', 'data', 'results'];

  function apiBaseUrl() {
    return (localStorage.getItem(STORAGE_KEY) || DEFAULT_API_BASE_URL).replace(/\/$/, '');
  }

  async function apiSend(method, path, payload) {
    try {
      const response = await fetch(`${apiBaseUrl()}${path}`, {
        method,
        headers: payload
          ? { Accept: 'application/json', 'Content-Type': 'application/json' }
          : { Accept: 'application/json' },
        body: payload ? JSON.stringify(payload) : undefined
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        return {
          ok: false,
          data,
          error: errorMessage(data, `La API respondio con estado ${response.status}.`)
        };
      }
      return { ok: true, data };
    } catch (error) {
      return { ok: false, error: `API no disponible: ${error.message}` };
    }
  }

  async function apiList(resource) {
    const result = await apiSend('GET', `/${resource}`);
    return { ...result, items: result.ok ? asCollection(result.data) : [] };
  }

  function asCollection(data) {
    if (Array.isArray(data)) return data.filter(isObject);
    if (isObject(data)) {
      for (const key of COLLECTION_KEYS) {
        if (Array.isArray(data[key])) return data[key].filter(isObject);
      }
    }
    return [];
  }

  function initializeSettings() {
    const form = document.getElementById('api-settings');
    const input = document.getElementById('api-url');
    if (!form || !input) return;
    input.value = apiBaseUrl();
    form.addEventListener('submit', event => {
      event.preventDefault();
      const value = input.value.trim().replace(/\/$/, '');
      if (!value) return;
      localStorage.setItem(STORAGE_KEY, value);
      window.location.reload();
    });
  }

  function recordId(item) {
    return isObject(item) ? String(item.id ?? item._id ?? item.uuid ?? '') : '';
  }

  function requestedId() {
    return new URLSearchParams(window.location.search).get('id') || '';
  }

  function payloadFromForm(form) {
    return Object.fromEntries(
      [...new FormData(form).entries()].filter(([, value]) => String(value).trim() !== '')
    );
  }

  function showAlert(message) {
    const target = document.getElementById('page-alert');
    if (!target) return;
    target.hidden = false;
    target.textContent = message;
  }

  function hideAlert() {
    const target = document.getElementById('page-alert');
    if (target) target.hidden = true;
  }

  function empty(targetId, visible) {
    const target = document.getElementById(targetId);
    if (target) target.hidden = !visible;
  }

  function text(targetId, value) {
    const target = document.getElementById(targetId);
    if (target) target.textContent = value ?? 'Sin dato';
  }

  function linkFor(resource, page, id) {
    const query = id ? `?id=${encodeURIComponent(id)}` : '';
    return `/${resource}/${page}.html${query}`;
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function errorMessage(data, fallback) {
    if (isObject(data)) return String(data.error || data.message || data.detail || fallback);
    return fallback;
  }

  function isObject(value) {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
  }

  window.Northstar = {
    apiSend,
    apiList,
    empty,
    escapeHtml,
    hideAlert,
    isObject,
    linkFor,
    payloadFromForm,
    recordId,
    requestedId,
    showAlert,
    text
  };

  document.addEventListener('DOMContentLoaded', initializeSettings);
}());
