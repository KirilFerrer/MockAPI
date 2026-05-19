(function () {
  const TYPES = ['string', 'integer', 'number', 'boolean', 'array', 'object'];
  const INTENTIONS = [
    {value: '', label: 'auto'},
    {value: 'ops.case_title', label: 'caso: titulo'},
    {value: 'ops.case_description', label: 'caso: descripcion'},
    {value: 'ops.impact', label: 'caso: impacto'},
    {value: 'ops.note', label: 'caso: nota'},
    {value: 'ops.queue', label: 'ops: cola'},
    {value: 'ops.sla', label: 'ops: sla'},
    {value: 'asset.tag', label: 'activo: tag'},
    {value: 'asset.hostname', label: 'activo: host'},
    {value: 'asset.name', label: 'activo: nombre'},
    {value: 'asset.serial', label: 'activo: serie'},
    {value: 'asset.os', label: 'activo: sistema'},
    {value: 'finance.invoice_number', label: 'finanzas: factura'},
    {value: 'finance.purchase_order', label: 'finanzas: pedido'},
    {value: 'finance.amount', label: 'finanzas: importe'},
    {value: 'company.name', label: 'empresa'},
    {value: 'person.employee_name', label: 'persona'},
    {value: 'person.department', label: 'departamento'},
    {value: 'person.team', label: 'equipo'},
    {value: 'person.role', label: 'rol'},
    {value: 'workflow.status', label: 'estado'},
    {value: 'workflow.priority', label: 'prioridad'},
    {value: 'general.title', label: 'titulo'},
    {value: 'general.description', label: 'descripcion'},
    {value: 'general.tag', label: 'etiqueta'}
  ];

  function createSchemaForm(root, options) {
    const onChange = options?.onChange || function () {};
    const nameInput = root.querySelector('.js-schema-name');
    const rowsElement = root.querySelector('.js-schema-rows');
    const addButton = root.querySelector('.js-add-schema-field');
    let rows = [];
    let uid = 0;
    let loadedDefinition = null;
    let dirtyDefinition = false;

    function notify() {
      onChange();
    }

    function markDefinitionChanged() {
      dirtyDefinition = true;
      notify();
    }

    function cloneJson(value) {
      return JSON.parse(JSON.stringify(value || {}));
    }

    function rowFromDefinition(name, config) {
      const fieldConfig = isPlainObject(config) ? config : {type: 'string'};
      const mockConfig = isPlainObject(fieldConfig['x-mock']) ? fieldConfig['x-mock'] : {};
      return {
        id: uid++,
        name,
        type: fieldConfig.type || 'string',
        req: Boolean(fieldConfig.required),
        generator: mockConfig.generator || '',
        examples: stringifyValues(fieldConfig.examples || mockConfig.examples),
        enumValues: stringifyValues(fieldConfig.enum),
        pattern: mockConfig.pattern || ''
      };
    }

    function rowsFromDefinition(definition) {
      const properties = editableProperties(definition);
      return Object.entries(properties).map(([name, config]) => rowFromDefinition(name, config));
    }

    function editableProperties(definition) {
      if (!isPlainObject(definition)) {
        return {};
      }

      if (isPlainObject(definition.properties)) {
        return definition.properties;
      }

      if (definition.type === 'array' && isPlainObject(definition.items?.properties)) {
        return definition.items.properties;
      }

      return definition;
    }

    function renderRows(focusLast, shouldNotify) {
      rowsElement.innerHTML = '';

      rows.forEach((row, rowIndex) => {
        const wrapper = document.createElement('div');
        wrapper.className = 'schema-row';

        const main = document.createElement('div');
        main.className = 'schema-row-main';

        const name = document.createElement('input');
        name.type = 'text';
        name.placeholder = 'nombre';
        name.value = row.name;
        name.addEventListener('input', () => {
          row.name = name.value;
          markDefinitionChanged();
        });

        const type = document.createElement('select');
        TYPES.forEach(typeName => {
          const option = document.createElement('option');
          option.textContent = typeName;
          option.selected = typeName === row.type;
          type.appendChild(option);
        });
        type.addEventListener('change', () => {
          row.type = type.value;
          markDefinitionChanged();
        });

        const intention = document.createElement('select');
        intention.className = 'schema-intention';
        INTENTIONS.forEach(({value, label}) => {
          const option = document.createElement('option');
          option.value = value;
          option.textContent = label;
          option.selected = value === row.generator;
          intention.appendChild(option);
        });
        intention.addEventListener('change', () => {
          row.generator = intention.value;
          markDefinitionChanged();
        });

        const requiredLabel = document.createElement('label');
        requiredLabel.className = 'req-wrap';
        const required = document.createElement('input');
        required.type = 'checkbox';
        required.checked = row.req;
        required.addEventListener('change', () => {
          row.req = required.checked;
          markDefinitionChanged();
        });
        requiredLabel.appendChild(required);
        requiredLabel.append(' req');

        const remove = document.createElement('button');
        remove.className = 'btn-del';
        remove.type = 'button';
        remove.title = 'Eliminar';
        remove.textContent = 'x';
        remove.addEventListener('click', () => {
          rows = rows.filter(item => item.id !== row.id);
          dirtyDefinition = true;
          renderRows(false);
        });

        main.append(name, type, intention, requiredLabel, remove);

        const extra = document.createElement('div');
        extra.className = 'schema-row-extra';

        const examples = document.createElement('input');
        examples.type = 'text';
        examples.spellcheck = false;
        examples.placeholder = 'ejemplos';
        examples.value = row.examples;
        examples.title = row.examples;
        examples.addEventListener('input', () => {
          row.examples = examples.value;
          examples.title = examples.value;
          markDefinitionChanged();
        });

        const enumValues = document.createElement('input');
        enumValues.type = 'text';
        enumValues.spellcheck = false;
        enumValues.placeholder = 'enum';
        enumValues.value = row.enumValues;
        enumValues.title = row.enumValues;
        enumValues.addEventListener('input', () => {
          row.enumValues = enumValues.value;
          enumValues.title = enumValues.value;
          markDefinitionChanged();
        });

        const pattern = document.createElement('input');
        pattern.type = 'text';
        pattern.spellcheck = false;
        pattern.placeholder = 'patron';
        pattern.value = row.pattern;
        pattern.title = row.pattern;
        pattern.addEventListener('input', () => {
          row.pattern = pattern.value;
          pattern.title = pattern.value;
          markDefinitionChanged();
        });

        const exampleField = helpField(
          examples,
          'Valores separados por coma para elegir uno al azar. Tiene prioridad sobre enum, patron e intencion.'
        );
        const enumField = helpField(
          enumValues,
          'Lista cerrada separada por coma. Tiene prioridad sobre patron e intencion.'
        );
        const patternField = helpField(
          pattern,
          'Patron rapido: ? genera letras y # genera numeros. Tiene prioridad sobre intencion. Ejemplos: INV-2026-####, AS-??-#### o TCK/###/??.'
        );

        extra.append(exampleField, enumField, patternField);
        if (rowIndex !== 0) {
          extra.querySelectorAll('.schema-help-field').forEach(field => {
            field.classList.remove('has-help');
            field.querySelectorAll('.field-help').forEach(help => help.remove());
          });
        }
        const advanced = document.createElement('details');
        advanced.className = 'schema-row-advanced';
        const advancedSummary = document.createElement('summary');
        advancedSummary.textContent = 'Configuracion adicional';
        advanced.append(advancedSummary, extra);

        wrapper.append(main, advanced);
        rowsElement.appendChild(wrapper);
      });

      if (focusLast) {
        rowsElement.querySelector('.schema-row:last-child input')?.focus();
      }

      if (shouldNotify !== false) {
        notify();
      }
    }

    function addRow(focusLast) {
      rows.push(emptyRow());
      dirtyDefinition = true;
      renderRows(focusLast);
    }

    function reset() {
      nameInput.value = '';
      loadedDefinition = null;
      dirtyDefinition = false;
      rows = [emptyRow()];
      renderRows(false);
    }

    function loadSchema(schema) {
      nameInput.value = schema?.name || '';
      loadedDefinition = cloneJson(schema?.definition || {});
      dirtyDefinition = false;
      rows = rowsFromDefinition(loadedDefinition);
      if (!rows.length) {
        rows.push(emptyRow());
      }
      renderRows(false);
    }

    function getDefinition() {
      if (loadedDefinition && !dirtyDefinition) {
        return cloneJson(loadedDefinition);
      }

      const definition = {};
      rows.forEach(row => {
        const name = row.name.trim();
        if (name) {
          definition[name] = fieldDefinition(row);
        }
      });
      return definition;
    }

    function getName() {
      return nameInput.value.trim();
    }

    function emptyRow() {
      return {
        id: uid++,
        name: '',
        type: 'string',
        req: false,
        generator: '',
        examples: '',
        enumValues: '',
        pattern: ''
      };
    }

    function fieldDefinition(row) {
      const definition = {type: row.type, required: row.req};
      const examples = parseValues(row.examples, row.type);
      const enumValues = parseValues(row.enumValues, row.type);
      const mockConfig = {};

      if (examples.length) {
        definition.examples = examples;
      }
      if (enumValues.length) {
        definition.enum = enumValues;
      }
      if (row.generator) {
        mockConfig.generator = row.generator;
      }
      if (row.pattern.trim()) {
        mockConfig.pattern = row.pattern.trim();
      }
      if (Object.keys(mockConfig).length) {
        definition['x-mock'] = mockConfig;
      }

      return definition;
    }

    nameInput.addEventListener('input', notify);
    addButton.addEventListener('click', () => addRow(true));
    rows = [emptyRow()];
    renderRows(false, false);

    return {
      getDefinition,
      getName,
      loadSchema,
      reset
    };
  }

  function parseValues(value, type) {
    return value
      .split(/[\n,]+/)
      .map(item => item.trim())
      .filter(Boolean)
      .map(item => coerceValue(item, type));
  }

  function coerceValue(value, type) {
    if (type === 'integer') {
      const parsed = Number.parseInt(value, 10);
      return Number.isNaN(parsed) ? value : parsed;
    }

    if (type === 'number') {
      const parsed = Number.parseFloat(value);
      return Number.isNaN(parsed) ? value : parsed;
    }

    if (type === 'boolean') {
      return ['true', '1', 'yes', 'si'].includes(value.toLowerCase());
    }

    return value;
  }

  function stringifyValues(value) {
    return Array.isArray(value) ? value.map(String).join(', ') : '';
  }

  function helpField(input, message) {
    const wrapper = document.createElement('div');
    wrapper.className = 'schema-help-field has-help';

    const help = document.createElement('span');
    help.className = 'field-help';
    help.tabIndex = 0;
    help.textContent = '?';
    help.setAttribute('aria-label', message);
    help.dataset.tooltip = message;
    help.addEventListener('mousedown', event => {
      event.preventDefault();
    });
    help.addEventListener('click', event => {
      event.preventDefault();
      help.blur();
    });

    wrapper.append(input, help);
    return wrapper;
  }

  function isPlainObject(value) {
    return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
  }

  window.MockAPI = window.MockAPI || {};
  window.MockAPI.createSchemaForm = createSchemaForm;
})();
