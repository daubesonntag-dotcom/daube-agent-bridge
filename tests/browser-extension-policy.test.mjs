import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateMcpEndpoint, mcpConnectionSnippet, normalizeRepository,
  classifySourceReuse, SCOUT_REPOSITORIES } from '../browser-extension/endpoint-policy.mjs';

const root = new URL('../', import.meta.url);
test('allow secure MCP endpoint and loopback development', () => {
  assert.equal(validateMcpEndpoint('https://agent.example.com/mcp').ok, true);
  assert.equal(validateMcpEndpoint('http://localhost:8000/mcp').ok, true);
  assert.equal(validateMcpEndpoint('http://127.0.0.1:8000/mcp').ok, true);
  assert.equal(validateMcpEndpoint('http://[::1]:8000/mcp').ok, true);
});
test('reject credential exfiltration, HTTP remote, wrong path and fragments', () => {
  for (const url of ['https://token:pass@agent.example.com/mcp','http://agent.example.com/mcp',
    'https://agent.example.com/tools','https://agent.example.com/mcp#secret',
    'javascript:alert(1)', 'file:///etc/passwd','https://agent.example.com/mcp?token=abc',
    'http://192.168.1.3/mcp','']) assert.equal(validateMcpEndpoint(url).ok, false, url);
});
test('emit MCP config only for checked endpoint', () => {
  assert.equal(mcpConnectionSnippet('https://agent.example.com/mcp').mcpServers['daube-agent-bridge'].type, 'http');
  assert.throws(() => mcpConnectionSnippet('http://evil.example.com/mcp'));
});
test('public GitHub repository allowlist and license gates', () => {
  assert.equal(normalizeRepository('langchain-ai/langgraph'),'langchain-ai/langgraph');
  assert.equal(normalizeRepository('https://evil.local'),null);
  assert.equal(SCOUT_REPOSITORIES.length,8);
  assert.equal(classifySourceReuse({private:false,archived:false,license:{spdx_id:'MIT'}}),'REVIEW_LICENSE_AND_SECURITY');
  assert.equal(classifySourceReuse({private:false,archived:false,license:{spdx_id:'NOASSERTION'}}),'REVIEW_LEGAL_BEFORE_REUSE');
  assert.equal(classifySourceReuse({private:true,license:{spdx_id:'MIT'}}),'UNKNOWN');
});
test('manifest permissions and browser UI are constrained', () => {
  const manifest=JSON.parse(readFileSync(new URL('./browser-extension/manifest.json',root),'utf8'));
  assert.equal(manifest.manifest_version,3);
  assert.ok(manifest.permissions.includes('activeTab'));
  assert.ok(!manifest.host_permissions);
  assert.deepEqual(manifest.optional_host_permissions,['https://api.github.com/*']);
  const ui=readFileSync(new URL('./browser-extension/sidepanel.js',root),'utf8');
  assert.ok(ui.includes('https://council.daubesonntag.com/'));
  assert.ok(!ui.includes('chrome.cookies'));
  assert.ok(!ui.includes('eval('));
  assert.ok(ui.includes('localSource: { text, savedAt:'));
});
