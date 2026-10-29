import { validateMcpEndpoint, mcpConnectionSnippet, SCOUT_REPOSITORIES,
  normalizeRepository, classifySourceReuse } from './endpoint-policy.mjs';

const $ = (id) => document.getElementById(id);
const COUNCIL = 'https://council.daubesonntag.com/';

function setStatus(id, text) { $(id).textContent = text; }
function showSnippet(endpoint) {
  $('snippet').textContent = JSON.stringify(mcpConnectionSnippet(endpoint), null, 2);
}

$('openCouncil').addEventListener('click', () => chrome.tabs.create({ url: COUNCIL }));
$('openResearch').addEventListener('click', () => chrome.tabs.create({ url: COUNCIL + 'research/' }));

chrome.storage.local.get(['endpoint', 'localSource']).then(({ endpoint, localSource }) => {
  if (endpoint) $('endpoint').value = endpoint;
  const parsed = validateMcpEndpoint($('endpoint').value);
  if (parsed.ok) showSnippet(parsed.value);
  else setStatus('endpointStatus', parsed.reason);
  if (localSource) { $('selection').textContent = localSource.text || ''; $('copy').disabled = false; }
}).catch(() => setStatus('endpointStatus', 'Không đọc được bộ nhớ extension.'));

$('save').addEventListener('click', async () => {
  const parsed = validateMcpEndpoint($('endpoint').value);
  if (!parsed.ok) { setStatus('endpointStatus', parsed.reason); return; }
  try {
    await chrome.storage.local.set({ endpoint: parsed.value });
    showSnippet(parsed.value);
    setStatus('endpointStatus', 'Đã lưu cấu hình cục bộ. Chưa kết nối MCP tool.');
  } catch { setStatus('endpointStatus', 'Không lưu được endpoint.'); }
});

$('capture').addEventListener('click', async () => {
  setStatus('captureStatus', 'Đang đọc đoạn được chọn theo yêu cầu...');
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!Number.isInteger(tab?.id)) throw new Error('Không tìm thấy tab hiện hành.');
    const data = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => ({ selection: String(window.getSelection()?.toString() || '').slice(0, 4000),
        title: String(document.title || '').slice(0, 180),
        url: String(location.href || '').slice(0, 1200) })
    });
    const picked = data?.[0]?.result;
    if (!picked?.selection) throw new Error('Không có đoạn văn đang chọn hoặc tab không cho phép đọc.');
    const text = [picked.title, picked.url, '', picked.selection].join('\n');
    await chrome.storage.local.set({ localSource: { text, savedAt: new Date().toISOString() } });
    $('selection').textContent = text;
    $('copy').disabled = false;
    setStatus('captureStatus', 'Đã lưu trên thiết bị. Không có dữ liệu nào được gửi lên server.');
  } catch (error) {
    setStatus('captureStatus', error instanceof Error ? error.message : String(error));
  }
});

$('copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText($('selection').textContent || '');
    setStatus('captureStatus', 'Đã sao chép vào clipboard.');
  } catch { setStatus('captureStatus', 'Không sao chép được; hãy chọn văn bản thủ công.'); }
});

SCOUT_REPOSITORIES.forEach((repo) => { const option = document.createElement('option');
  option.value = repo; option.textContent = repo; $('repository').append(option); });

$('checkRepository').addEventListener('click', async () => {
  const repo = normalizeRepository($('repository').value);
  if (!repo || !SCOUT_REPOSITORIES.includes(repo)) { setStatus('repositoryStatus', 'Repository không được phê duyệt.'); return; }
  setStatus('repositoryStatus', 'Đang kiểm tra quyền truy cập công khai...');
  try {
    // Must originate inside a direct user gesture: ask only for this public API origin.
    const granted = await chrome.permissions.request({ origins: ['https://api.github.com/*'] });
    if (!granted) { setStatus('repositoryStatus', 'Chưa được cấp quyền gọi GitHub public API.'); return; }
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 6000);
    let data;
    try {
      const response = await fetch('https://api.github.com/repos/' + repo, {
        signal: controller.signal, headers: { Accept: 'application/vnd.github+json' }, cache: 'no-store'
      });
      if (!response.ok) throw new Error('GitHub HTTP ' + response.status);
      data = await response.json();
    } finally { clearTimeout(timer); }
    if (data.private !== false || data.full_name?.toLowerCase() !== repo.toLowerCase()) {
      throw new Error('GitHub public identity mismatch.');
    }
    $('repositoryResult').textContent = JSON.stringify({
      repository: data.full_name,
      stars: Number.isSafeInteger(data.stargazers_count) ? data.stargazers_count : null,
      license: data.license?.spdx_id || 'UNVERIFIED',
      archived: Boolean(data.archived),
      updated_at: data.updated_at || null,
      source_url: data.html_url,
      reuse: classifySourceReuse(data),
      authority: 'RESEARCH_ONLY_NOT_ADMITTED'
    }, null, 2);
    setStatus('repositoryStatus', 'Đã đọc từ GitHub. Chưa tải mã nguồn hoặc cấp quyền thực thi.');
  } catch (error) {
    $('repositoryResult').textContent = '';
    setStatus('repositoryStatus', error instanceof Error ? error.message : String(error));
  }
});
