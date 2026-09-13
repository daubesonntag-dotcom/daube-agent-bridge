import test from 'node:test';
import assert from 'node:assert/strict';
import { patchDeviceSource, PATCH_MARKER } from './patch-device-persistence.mjs';

test('inserts guarded persistence timer after remote heartbeat', () => {
  const source = `class MCPDevice {\n  async start() {\n            this.remoteChannel.startHeartbeat(this.deviceId);\n  }\n}\n`;
  const out = patchDeviceSource(source);
  assert.match(out, new RegExp(PATCH_MARKER));
  assert.match(out, /session\?\.refresh_token/);
  assert.match(out, /300000/);
  assert.ok(out.indexOf(PATCH_MARKER) > out.indexOf('startHeartbeat'));
});

test('is idempotent', () => {
  const source = `this.remoteChannel.startHeartbeat(this.deviceId);\n`;
  const once = patchDeviceSource(source);
  const twice = patchDeviceSource(once);
  assert.equal(twice, once);
  assert.equal((twice.match(new RegExp(PATCH_MARKER, 'g')) ?? []).length, 1);
});

test('fails closed when the supported anchor is absent', () => {
  assert.throws(
    () => patchDeviceSource('console.log("different version")'),
    /supported heartbeat anchor/,
  );
});
