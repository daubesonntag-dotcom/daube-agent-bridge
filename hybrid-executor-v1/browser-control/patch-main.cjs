'use strict';
/**
 * Review-only source patch for the bounded Electron main-process adapter.
 * This function neither writes a file nor changes a running process.
 */
function patchMain(source) {
  if (typeof source !== 'string') throw new Error('SOURCE_DRIFT');
  const requiredImport = "const { loadWorkspaceExtensions } = require('./extensions.cjs');";
  const injectedImport = "const { startControlSocket } = require('./browser-control.cjs');";
  const bootAnchor = "  await loadCore();\n  installIpc();\n  await createMainWindow();";
  if (source.includes(injectedImport)) {
    if (source.indexOf('await startControlSocket(') < 0
      || source.indexOf('await createMainWindow();') < source.indexOf('await startControlSocket(')) {
      throw new Error('PARTIAL_PATCH_DRIFT');
    }
    return { code: source, changed: false };
  }
  if (source.split(requiredImport).length !== 2
    || source.split(bootAnchor).length !== 2
    || !source.includes('app.whenReady().then(async () => {')) {
    throw new Error('SOURCE_ANCHOR_DRIFT');
  }
  const replacement = [
    '  await loadCore();',
    '  installIpc();',
    '  await startControlSocket({',
    '    activeTab,',
    '    socketPath: process.env.DAUBE_BROWSER_CONTROL_SOCKET || "/run/daube-sovereign/browser-control-v1.sock",',
    '    navigate: async (url) => {',
    '      const tab=activeTab();',
    '      if (!tab || tab.view.webContents.isDestroyed()) throw new Error("NO_ACTIVE_TAB");',
    '      await tab.view.webContents.loadURL(url);',
    '      return tab.view.webContents.getURL();',
    '    }',
    '  });',
    '  await createMainWindow();'
  ].join('\n');
  const code = source.replace(requiredImport, requiredImport+'\n'+injectedImport).replace(bootAnchor,replacement);
  return { code, changed: true };
}
module.exports = { patchMain };
