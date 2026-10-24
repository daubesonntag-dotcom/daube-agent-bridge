'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const {patchMain}=require('./patch-main.cjs');
const input=[
"const { loadWorkspaceExtensions } = require('./extensions.cjs');",
"app.whenReady().then(async () => {",
"  await loadCore();",
"  installIpc();",
"  await createMainWindow();",
"  app.on('activate', async () => {});",
"});"
].join("\n");
test('patch starts private adapter before loading the browser UI',()=>{
 const p=patchMain(input);
 assert.equal(p.changed,true);
 assert.match(p.code,/const \{ startControlSocket \} = require\('\.\/browser-control\.cjs'\)/);
 assert.ok(p.code.indexOf('await startControlSocket(')<p.code.indexOf('await createMainWindow();'));
 assert.match(p.code,/DAUBE_BROWSER_CONTROL_SOCKET/);
});
test('patcher rejects drifting source rather than silently applying partial changes',()=>{
 assert.throws(()=>patchMain("app.whenReady().then(()=>{})"),/ANCHOR|DRIFT/);
});
test('patching is idempotent',()=>{
 const a=patchMain(input);
 const b=patchMain(a.code);
 assert.equal(b.changed,false);
 assert.equal(b.code,a.code);
});
