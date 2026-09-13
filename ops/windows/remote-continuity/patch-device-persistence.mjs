import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

export const PATCH_MARKER = 'DAUBE_PATCH_REMOTE_SESSION_PERSISTENCE_v1';

const INSERT = `
            // DAUBE_PATCH_REMOTE_SESSION_PERSISTENCE_v1
            const persistRotatedSession = async () => {
                try {
                    const current = await this.remoteChannel.getSession();
                    const session = current?.data?.session;
                    if (this.persistSession && session?.refresh_token) {
                        await this.savePersistedConfig();
                    }
                } catch (error) {
                    console.warn('⚠️ Failed to persist rotated remote session:', error?.message ?? error);
                }
            };
            setInterval(() => { void persistRotatedSession(); }, 300000).unref?.();`;

export function patchDeviceSource(source) {
  if (source.includes(PATCH_MARKER)) return source;

  const anchors = [
    '            this.remoteChannel.startHeartbeat(this.deviceId);',
    '            this.remoteChannel.startHeartbeat(this.deviceId!);',
    'this.remoteChannel.startHeartbeat(this.deviceId);',
    'this.remoteChannel.startHeartbeat(this.deviceId!);',
  ];
  const anchor = anchors.find((candidate) => source.includes(candidate));
  if (!anchor) {
    throw new Error('No supported heartbeat anchor found; refusing to patch unknown Desktop Commander build');
  }
  return source.replace(anchor, `${anchor}${INSERT}`);
}

async function main() {
  const target = process.argv[2];
  if (!target) throw new Error('Usage: node patch-device-persistence.mjs <device.js>');
  const source = fs.readFileSync(target, 'utf8');
  const patched = patchDeviceSource(source);
  if (patched !== source) fs.writeFileSync(target, patched, 'utf8');
  console.log(patched === source ? 'PATCH_ALREADY_PRESENT' : 'PATCH_APPLIED');
}

if (process.argv[1] && fileURLToPath(import.meta.url) === fileURLToPath(new URL(`file://${process.argv[1]}`))) {
  await main();
}
