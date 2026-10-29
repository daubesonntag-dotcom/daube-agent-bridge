/** Deliberately no remote MCP discovery or auth in the browser extension. */
export function validateMcpEndpoint(input) {
  const candidate = String(input ?? '').trim();
  if (!candidate || candidate.length > 300) return { ok: false, reason: 'Endpoint must be 1–300 characters.' };
  let url;
  try { url = new URL(candidate); } catch { return { ok: false, reason: 'Invalid URL.' }; }
  if (url.username || url.password || url.hash) return { ok: false, reason: 'Credentials and fragments are forbidden in URLs.' };
  const loopback = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if (url.protocol !== 'https:' && !(url.protocol === 'http:' && loopback)) {
    return { ok: false, reason: 'Use HTTPS; plain HTTP is permitted only for localhost.' };
  }
  if (url.hostname.endsWith('.local') && !loopback) return { ok: false, reason: 'Use a reviewed HTTPS host.' };
  if (!url.pathname.endsWith('/mcp')) return { ok: false, reason: 'Endpoint path must end with /mcp.' };
  if (url.search) return { ok: false, reason: 'Remove query parameters from MCP endpoint URLs.' };
  return { ok: true, value: url.href };
}

export function mcpConnectionSnippet(endpoint) {
  const checked = validateMcpEndpoint(endpoint);
  if (!checked.ok) throw new Error(checked.reason);
  return { mcpServers: { 'daube-agent-bridge': { type: 'http', url: checked.value } } };
}

export const SCOUT_REPOSITORIES = Object.freeze([
  'langchain-ai/langgraph', 'crewAIInc/crewAI', 'microsoft/autogen',
  'All-Hands-AI/OpenHands', 'browser-use/browser-use', 'langgenius/dify',
  'langflow-ai/langflow', 'modelcontextprotocol/registry'
]);

export function normalizeRepository(value) {
  const name = String(value ?? '').trim();
  if (!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(name) || name.length > 160) return null;
  return name;
}

export function classifySourceReuse(metadata) {
  if (!metadata || typeof metadata !== 'object' || metadata.private !== false) return 'UNKNOWN';
  if (metadata.archived) return 'REVIEW_ARCHIVED';
  const license = metadata.license?.spdx_id;
  if (['MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC'].includes(license)) return 'REVIEW_LICENSE_AND_SECURITY';
  return 'REVIEW_LEGAL_BEFORE_REUSE';
}
