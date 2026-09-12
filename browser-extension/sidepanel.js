const endpoint = document.querySelector('#endpoint');
const output = document.querySelector('#snippet');
const save = document.querySelector('#save');

function render(value) {
  output.textContent = JSON.stringify({
    mcpServers: {
      'daube-agent-bridge': { type: 'http', url: value }
    }
  }, null, 2);
}

chrome.storage.local.get(['endpoint']).then(({ endpoint: stored }) => {
  if (stored) endpoint.value = stored;
  render(endpoint.value);
});

save.addEventListener('click', async () => {
  const value = endpoint.value.trim();
  await chrome.storage.local.set({ endpoint: value });
  render(value);
});
