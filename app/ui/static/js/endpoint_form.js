(function () {
  const ENDPOINTS_API_URL = '/api/endpoints';
  const SCHEMAS_API_URL = '/api/schemas';

  function sameJson(left, right) {
    return JSON.stringify(left || {}) === JSON.stringify(right || {});
  }

  function showToast(message) {
    const toast = document.getElementById('toast');
    if (!toast) return;

    clearTimeout(showToast.timeout);
    toast.textContent = message;
    toast.style.display = 'block';
    showToast.timeout = setTimeout(() => {
      toast.style.display = 'none';
    }, 3000);
  }

  function createOption(schema, onSelect) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'schema-option';
    button.textContent = schema.name;

    const meta = document.createElement('small');
    meta.textContent = `${Object.keys(schema.definition || {}).length} campos`;
    button.appendChild(meta);
    button.addEventListener('click', () => onSelect(schema.id));

    return button;
  }

  function initEndpointForm() {
    const form = document.querySelector('.js-endpoint-form');
    if (!form || !window.MockAPI?.createSchemaForm) return;

    let savedSchemas = [];
    let selectedSchemaId = null;

    const preview = form.querySelector('.js-preview');
    const epMethod = form.querySelector('.js-ep-method');
    const epPath = form.querySelector('.js-ep-path');
    const epName = form.querySelector('.js-ep-name');
    const epDesc = form.querySelector('.js-ep-desc');
    const schemaPicker = form.querySelector('.js-schema-picker');
    const schemaTrigger = form.querySelector('.js-schema-trigger');
    const schemaSearch = form.querySelector('.js-schema-search');
    const schemaOptions = form.querySelector('.js-schema-options');
    const btnSaveSchema = form.querySelector('.js-save-schema');
    const btnSubmit = form.querySelector('.js-save-endpoint');
    const schemaForm = window.MockAPI.createSchemaForm(form.querySelector('.js-schema-form'), {
      onChange: updatePreview
    });

    function selectedSchema() {
      return savedSchemas.find(schema => schema.id === selectedSchemaId);
    }

    function selectedSchemaWasEdited() {
      const schema = selectedSchema();
      if (!schema) return false;

      return schemaForm.getName() !== schema.name || !sameJson(schemaForm.getDefinition(), schema.definition);
    }

    async function loadSchemas() {
      try {
        const response = await fetch(SCHEMAS_API_URL);
        if (!response.ok) return;
        savedSchemas = await response.json();
        renderSchemaOptions();
      } catch (error) {
        showToast('No se pudieron cargar los schemas');
      }
    }

    function renderSchemaOptions() {
      const term = schemaSearch.value.trim().toLowerCase();
      const matches = savedSchemas.filter(schema => schema.name.toLowerCase().includes(term));

      schemaOptions.innerHTML = '';

      const createButton = document.createElement('button');
      createButton.type = 'button';
      createButton.className = 'schema-option schema-option-create';
      createButton.textContent = '+ crear nuevo schema';
      createButton.addEventListener('click', selectNewSchema);
      schemaOptions.appendChild(createButton);

      if (!matches.length) {
        const empty = document.createElement('div');
        empty.className = 'schema-empty';
        empty.textContent = 'No hay schemas con ese nombre';
        schemaOptions.appendChild(empty);
        return;
      }

      matches.forEach(schema => {
        schemaOptions.appendChild(createOption(schema, selectSchema));
      });
    }

    function closeSchemaPicker() {
      schemaPicker.classList.remove('open');
    }

    function selectNewSchema() {
      selectedSchemaId = null;
      schemaTrigger.textContent = 'Crear nuevo schema';
      schemaForm.reset();
      closeSchemaPicker();
      updatePreview();
    }

    function selectSchema(schemaId) {
      const schema = savedSchemas.find(item => item.id === Number(schemaId));
      if (!schema) return;

      selectedSchemaId = schema.id;
      schemaTrigger.textContent = schema.name;
      schemaForm.loadSchema(schema);
      closeSchemaPicker();
      updatePreview();
    }

    function payload() {
      const schema = selectedSchema();
      const schemaEdited = selectedSchemaWasEdited();
      const data = {
        name: epName.value,
        method: epMethod.value,
        path: epPath.value,
        description: epDesc.value,
        schema: schemaForm.getDefinition()
      };

      if (schema && !schemaEdited) {
        data.schema_id = schema.id;
        data.schema_name = schema.name;
      } else {
        data.schema_name = schemaForm.getName();
      }

      return data;
    }

    function updatePreview() {
      preview.textContent = JSON.stringify(payload(), null, 2);
    }

    [epMethod, epPath, epName, epDesc].forEach(element => element.addEventListener('input', updatePreview));
    epMethod.addEventListener('change', updatePreview);
    schemaSearch.addEventListener('input', renderSchemaOptions);
    schemaTrigger.addEventListener('click', () => {
      schemaPicker.classList.toggle('open');
      schemaSearch.focus();
      renderSchemaOptions();
    });
    document.addEventListener('click', event => {
      if (!schemaPicker.contains(event.target)) closeSchemaPicker();
    });

    btnSaveSchema.addEventListener('click', async () => {
      const name = schemaForm.getName();
      if (!name) {
        showToast('Nombre del schema obligatorio');
        return;
      }

      btnSaveSchema.disabled = true;
      btnSaveSchema.textContent = 'Guardando...';
      try {
        const response = await fetch(SCHEMAS_API_URL, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({name, definition: schemaForm.getDefinition()})
        });

        if (!response.ok) {
          showToast(`Error ${response.status}`);
          return;
        }

        await response.json();
        await loadSchemas();
        showToast('Schema guardado correctamente');
      } catch (error) {
        showToast(`Error de red: ${error.message}`);
      } finally {
        btnSaveSchema.disabled = false;
        btnSaveSchema.textContent = 'Guardar solo schema';
      }
    });

    btnSubmit.addEventListener('click', async () => {
      const path = epPath.value.trim();
      if (!path) {
        showToast('Path es obligatorio');
        return;
      }
      if (!selectedSchema() && !schemaForm.getName()) {
        showToast('Nombre del schema obligatorio');
        return;
      }

      btnSubmit.disabled = true;
      btnSubmit.textContent = 'Enviando...';
      try {
        const response = await fetch(ENDPOINTS_API_URL, {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify(payload())
        });
        const data = await response.json().catch(() => null);

        if (!response.ok) {
          showToast(`Error ${response.status}`);
          return;
        }
        if (data?.schema_id) {
          await loadSchemas();
          selectSchema(data.schema_id);
        }
        showToast('Guardado correctamente');
      } catch (error) {
        showToast(`Error de red: ${error.message}`);
      } finally {
        btnSubmit.disabled = false;
        btnSubmit.textContent = 'Guardar endpoint';
      }
    });

    selectNewSchema();
    loadSchemas();
  }

  document.addEventListener('DOMContentLoaded', initEndpointForm);
})();
