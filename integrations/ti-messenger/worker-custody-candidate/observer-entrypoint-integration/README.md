# Complete Observer assembly candidate

Local source only, Messenger disabled. No deployment, secrets, persistent access or binding changes.

observer-machine.mjs is the complete historical root, not a placeholder. It imports withMessengerA and messengerDependencies and composes the existing SEC04ProbeOnly while retaining its OwnerACK/key-self-test methods. messenger-runtime-config.mjs supplies no dependencies, so all four Messenger methods deny. SOURCE_MANIFEST.json records source provenance and the complete runtime module graph. observer-integration.patch shows the only root changes.

AUTH_FLOW.md describes separate Founder, dispatcher/A and B lanes, activation inputs, session lifecycle and evidence requirements. Historical source is not asserted to be the currently serving bundle; no latest staged scheduled-action wrapper is included.

Run: node --test assembly.test.mjs rpc.test.mjs sec04-owner-ack-transport.test.mjs

40/40 local tests pass. The assembled-root tests replace only the Cloudflare WorkerEntrypoint import with a Node test stub, resolving all production imports unchanged. They do not emulate Cloudflare deployment or validate live binding registration. No network calls or real secrets are used.

Independent review: bounded source ACK. Supplied 40/40 plus supplemental tests invoking the actual assembled SEC04ProbeOnly with synthetic configuration 22/22 passed; scenarios overlap, not 62 unique cases. Reviewer independently fetched and matched all seven published dependency/test blobs, reconstructed the historical root hash by reversing only the declared integration changes, and confirmed no withdrawn scheduled wrapper. This is not deployment readiness.
