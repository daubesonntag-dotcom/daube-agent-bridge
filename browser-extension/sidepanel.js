const endpoint = document.querySelector('#endpoint');
const pairingToken = document.querySelector('#pairingToken');
const connectorId = document.querySelector('#connectorId');
const snippet = document.querySelector('#snippet');
const health = document.querySelector('#health');
const save = document.querySelector('#save');
const grant = document.querySelector('#grant');
const statusDot = document.querySelector('#statusDot');
const statusText = document.querySelector('#statusText');
const permissionText = document.querySelector('#permissionText');

const ORIGINS = ['https://*/*', 'http://*/*'];

function normalizeBase(value) {
  const raw = String(value || 'http://127.0.0.1:8000').trim().replace(/\/+$/, '');
  return raw.endsWith('/mcp') ? raw.slice(0, -4) : raw;
}

function renderSnippet(base) {
  snippet.textContent = JSON.stringify({
    mcpServers: {
      'daube-browser-bridge': {
        type: 'http',
        url: normalizeBase(base) + '/mcp'
      }
    }
  }, null, 2);
}

function setStatus(state, message) {
  statusDot.className = 'dot ' + (state === 'ok' ? 'ok' : state === 'warn' ? 'warn' : 'bad');
  statusText.textContent = message;
}

async function permissionState() {
  const granted = await chrome.permissions.contains({ origins: ORIGINS });
  permissionText.textContent = granted
    ? 'Site control granted for HTTP/HTTPS pages.'
    : 'Site control is not granted yet. D’AUBE cannot click/type until you grant it.';
  grant.textContent = granted ? 'Site control granted' : 'Grant site control';
  grant.disabled = granted;
  return granted;
}

async function probeHealth() {
  const base = normalizeBase(endpoint.value);
  try {
    const response = await fetch(base + '/browser/v1/health', { cache: 'no-store' });
    if (!response.ok) throw new Error('health_http_' + response.status);
    const payload = await response.json();
    health.textContent = JSON.stringify(payload, null, 2);
    if (payload.connected) setStatus('ok', 'D’AUBE bridge connected');
    else setStatus('warn', 'Bridge reachable; extension handshake pending');
  } catch (error) {
    health.textContent = JSON.stringify({ error: String(error?.message || error) }, null, 2);
    setStatus('bad', 'Local bridge unreachable');
  }
}

async function load() {
  const stored = await chrome.storage.local.get(['endpoint', 'pairingToken', 'connectorId']);
  endpoint.value = stored.endpoint || 'http://127.0.0.1:8000';
  pairingToken.value = stored.pairingToken || '';
  connectorId.value = stored.connectorId || 'daube-browser-extension';
  renderSnippet(endpoint.value);
  await permissionState();
  await probeHealth();
}

save.addEventListener('click', async () => {
  const base = normalizeBase(endpoint.value);
  const token = pairingToken.value.trim();
  const id = connectorId.value.trim() || 'daube-browser-extension';
  if (!/^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test(base)) {
    setStatus('bad', 'Endpoint must stay on localhost');
    return;
  }
  if (token.length < 16) {
    setStatus('bad', 'Pairing token must be at least 16 characters');
    return;
  }
  await chrome.storage.local.set({ endpoint: base, pairingToken: token, connectorId: id });
  endpoint.value = base;
  renderSnippet(base);
  setStatus('warn', 'Saved; waiting for bridge handshake');
  setTimeout(probeHealth, 800);
});

grant.addEventListener('click', async () => {
  try {
    const granted = await chrome.permissions.request({ origins: ORIGINS });
    if (!granted) {
      setStatus('warn', 'Site control permission not granted');
    }
  } finally {
    await permissionState();
  }
});

endpoint.addEventListener('input', () => renderSnippet(endpoint.value));

load();
setInterval(probeHealth, 5000);
