const CAPABILITIES = [
  'tabs.read',
  'page.read',
  'navigate',
  'click',
  'type',
  'screenshot'
];

let loopRunning = false;
let loopGeneration = 0;

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function normalizeBase(value) {
  const raw = String(value || 'http://127.0.0.1:8000').trim().replace(/\/+$/, '');
  return raw.endsWith('/mcp') ? raw.slice(0, -4) : raw;
}

async function config() {
  const stored = await chrome.storage.local.get(['endpoint', 'pairingToken', 'connectorId']);
  return {
    base: normalizeBase(stored.endpoint),
    token: String(stored.pairingToken || ''),
    connectorId: String(stored.connectorId || 'daube-browser-extension')
  };
}

async function tabFor(tabId) {
  if (Number.isInteger(tabId)) return chrome.tabs.get(tabId);
  const [active] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!active?.id) throw new Error('browser_no_active_tab');
  return active;
}

function assertWebUrl(url) {
  const value = String(url || '');
  if (!/^https?:\/\//i.test(value)) throw new Error('browser_non_web_url_blocked');
  return value;
}

async function waitForTab(tabId, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const tab = await chrome.tabs.get(tabId);
    if (tab.status === 'complete') return tab;
    await sleep(250);
  }
  throw new Error('browser_navigation_timeout');
}

async function pageSnapshot(tabId) {
  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => {
      const safeText = value => String(value || '').replace(/\s+/g, ' ').trim();
      const visible = element => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
      };
      const selectorHint = element => {
        if (element.id) return '#' + CSS.escape(element.id);
        if (element.getAttribute('name')) return element.tagName.toLowerCase() + '[name="' + CSS.escape(element.getAttribute('name')) + '"]';
        if (element.getAttribute('data-testid')) return '[data-testid="' + CSS.escape(element.getAttribute('data-testid')) + '"]';
        return null;
      };
      const interactive = [...document.querySelectorAll('a,button,input,textarea,select,[role="button"],[contenteditable="true"]')]
        .filter(visible)
        .slice(0, 400)
        .map((element, index) => ({
          index,
          tag: element.tagName.toLowerCase(),
          role: element.getAttribute('role'),
          text: safeText(element.innerText || element.textContent).slice(0, 500),
          ariaLabel: safeText(element.getAttribute('aria-label')).slice(0, 300),
          placeholder: safeText(element.getAttribute('placeholder')).slice(0, 300),
          inputType: element.getAttribute('type') || null,
          disabled: Boolean(element.disabled),
          selectorHint: selectorHint(element)
        }));
      return {
        url: location.href,
        title: document.title,
        text: safeText(document.body?.innerText || '').slice(0, 120000),
        interactive
      };
    }
  });
  return result?.result || null;
}

async function clickElement(tabId, selector, text) {
  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    args: [selector || null, text || null],
    func: (selectorValue, textValue) => {
      const normalize = value => String(value || '').replace(/\s+/g, ' ').trim().toLowerCase();
      const visible = element => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
      };
      let target = null;
      if (selectorValue) {
        target = document.querySelector(selectorValue);
      } else if (textValue) {
        const wanted = normalize(textValue);
        const candidates = [...document.querySelectorAll('button,a,[role="button"],input[type="button"],input[type="submit"]')].filter(visible);
        target = candidates.find(element => {
          const label = normalize(element.innerText || element.textContent || element.getAttribute('aria-label') || element.value);
          return label === wanted;
        }) || candidates.find(element => {
          const label = normalize(element.innerText || element.textContent || element.getAttribute('aria-label') || element.value);
          return label.includes(wanted);
        });
      }
      if (!target || !visible(target)) return { found: false };
      target.scrollIntoView({ block: 'center', inline: 'center' });
      const summary = {
        tag: target.tagName.toLowerCase(),
        text: String(target.innerText || target.textContent || target.getAttribute('aria-label') || '').trim().slice(0, 300)
      };
      target.click();
      return { found: true, ...summary };
    }
  });
  return result?.result || { found: false };
}

async function typeIntoElement(tabId, selector, text, value) {
  const [result] = await chrome.scripting.executeScript({
    target: { tabId },
    args: [selector || null, text || null, String(value ?? '')],
    func: (selectorValue, textValue, nextValue) => {
      const normalize = value => String(value || '').replace(/\s+/g, ' ').trim().toLowerCase();
      const visible = element => {
        const style = getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
      };
      let target = selectorValue ? document.querySelector(selectorValue) : null;
      if (!target && textValue) {
        const wanted = normalize(textValue);
        const fields = [...document.querySelectorAll('input,textarea,[contenteditable="true"]')].filter(visible);
        target = fields.find(element => {
          const id = element.id;
          const label = id ? document.querySelector('label[for="' + CSS.escape(id) + '"]') : null;
          const haystack = [
            label?.innerText,
            element.getAttribute('aria-label'),
            element.getAttribute('placeholder'),
            element.getAttribute('name')
          ].map(normalize).join(' ');
          return haystack.includes(wanted);
        });
      }
      if (!target || !visible(target)) return { found: false };
      target.focus();
      if (target.isContentEditable) {
        target.textContent = nextValue;
      } else {
        const proto = target instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
        const descriptor = Object.getOwnPropertyDescriptor(proto, 'value');
        if (descriptor?.set) descriptor.set.call(target, nextValue);
        else target.value = nextValue;
      }
      target.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: null }));
      target.dispatchEvent(new Event('change', { bubbles: true }));
      const inputType = target.getAttribute('type') || null;
      const currentLength = target.isContentEditable ? String(target.textContent || '').length : String(target.value || '').length;
      return { found: true, inputType, valueLength: currentLength, expectedLength: nextValue.length };
    }
  });
  return result?.result || { found: false };
}

async function executeJob(job) {
  const action = job.action;
  const args = job.arguments || {};
  const beforeTab = ['navigate', 'click', 'type'].includes(action) ? await tabFor(args.tabId) : null;
  let result;

  if (action === 'tabs.read') {
    const tabs = await chrome.tabs.query({});
    result = {
      tabs: tabs.map(tab => ({
        id: tab.id,
        windowId: tab.windowId,
        active: tab.active,
        title: tab.title || '',
        url: tab.url || '',
        status: tab.status || null
      }))
    };
  } else if (action === 'page.read') {
    const tab = await tabFor(args.tabId);
    assertWebUrl(tab.url);
    result = { tabId: tab.id, page: await pageSnapshot(tab.id) };
  } else if (action === 'screenshot') {
    const tab = await tabFor(args.tabId);
    assertWebUrl(tab.url);
    const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'png' });
    result = { tabId: tab.id, dataUrl };
  } else if (action === 'navigate') {
    const tab = await tabFor(args.tabId);
    const requestedUrl = assertWebUrl(args.url);
    await chrome.tabs.update(tab.id, { url: requestedUrl });
    const after = await waitForTab(tab.id);
    result = { requestedUrl, tab: { id: after.id, url: after.url || '', title: after.title || '' }, page: await pageSnapshot(tab.id) };
  } else if (action === 'click') {
    const tab = await tabFor(args.tabId);
    assertWebUrl(tab.url);
    const clicked = await clickElement(tab.id, args.selector, args.text);
    if (!clicked.found) throw new Error('browser_click_target_not_found');
    await sleep(750);
    const after = await chrome.tabs.get(tab.id);
    result = { clicked, tab: { id: after.id, url: after.url || '', title: after.title || '' }, page: await pageSnapshot(tab.id) };
  } else if (action === 'type') {
    const tab = await tabFor(args.tabId);
    assertWebUrl(tab.url);
    const typed = await typeIntoElement(tab.id, args.selector, args.text, args.value);
    if (!typed.found) throw new Error('browser_type_target_not_found');
    if (typed.valueLength !== typed.expectedLength) throw new Error('browser_type_readback_mismatch');
    result = { typed, tab: { id: tab.id, url: tab.url || '', title: tab.title || '' } };
  } else {
    throw new Error('browser_action_not_supported');
  }

  const afterTab = ['navigate', 'click', 'type'].includes(action) ? await tabFor(args.tabId || beforeTab?.id) : null;
  return {
    schema: 'daube.browser-action-receipt.v1',
    jobId: job.id,
    action,
    ok: true,
    verified: ['navigate', 'click', 'type'].includes(action) ? true : undefined,
    stateBefore: beforeTab ? { id: beforeTab.id, url: beforeTab.url || '', title: beforeTab.title || '' } : null,
    stateAfter: afterTab ? { id: afterTab.id, url: afterTab.url || '', title: afterTab.title || '' } : null,
    result,
    observedAt: new Date().toISOString()
  };
}

async function sendReceipt(base, token, receipt) {
  const response = await fetch(base + '/browser/v1/jobs/' + encodeURIComponent(receipt.jobId) + '/receipt', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-daube-browser-token': token
    },
    body: JSON.stringify(receipt)
  });
  if (!response.ok) throw new Error('browser_receipt_rejected_' + response.status);
}

async function pollOnce(generation) {
  const current = await config();
  if (!current.token) throw new Error('browser_pairing_token_missing');
  const response = await fetch(current.base + '/browser/v1/jobs/next', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-daube-browser-token': current.token
    },
    body: JSON.stringify({
      connectorId: current.connectorId,
      capabilities: CAPABILITIES
    })
  });
  if (generation !== loopGeneration) return;
  if (response.status === 204) return;
  if (!response.ok) throw new Error('browser_job_poll_failed_' + response.status);
  const job = await response.json();
  try {
    const receipt = await executeJob(job);
    await sendReceipt(current.base, current.token, receipt);
  } catch (error) {
    await sendReceipt(current.base, current.token, {
      schema: 'daube.browser-action-receipt.v1',
      jobId: job.id,
      action: job.action,
      ok: false,
      verified: false,
      error: String(error?.message || error),
      observedAt: new Date().toISOString()
    });
  }
}

async function startLoop() {
  if (loopRunning) return;
  loopRunning = true;
  const generation = ++loopGeneration;
  try {
    while (generation === loopGeneration) {
      try {
        await pollOnce(generation);
      } catch (error) {
        await chrome.storage.local.set({
          connectorStatus: {
            state: 'DEGRADED',
            error: String(error?.message || error),
            observedAt: new Date().toISOString()
          }
        });
        await sleep(2000);
      }
    }
  } finally {
    if (generation === loopGeneration) loopRunning = false;
  }
}

function restartLoop() {
  loopGeneration += 1;
  loopRunning = false;
  void startLoop();
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true });
  chrome.alarms.create('daube-browser-connector-health', { periodInMinutes: 0.5 });
  void startLoop();
});

chrome.runtime.onStartup.addListener(() => {
  chrome.alarms.create('daube-browser-connector-health', { periodInMinutes: 0.5 });
  void startLoop();
});

chrome.alarms.onAlarm.addListener(alarm => {
  if (alarm.name === 'daube-browser-connector-health') void startLoop();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && (changes.endpoint || changes.pairingToken || changes.connectorId)) restartLoop();
});

void startLoop();
