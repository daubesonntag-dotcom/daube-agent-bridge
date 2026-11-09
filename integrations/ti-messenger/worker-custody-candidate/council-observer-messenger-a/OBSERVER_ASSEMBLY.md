# Disabled assembly proof, not current deployment source

Exact local base observer-machine.mjs
SHA256 5cfb33d86601641a724cd964267fe8a5a8c062c4e405437555e1cee59cacb49b

observer-disabled-assembly.patch adds one import and wraps the existing SEC04ProbeOnly base. Existing ownerAck334 and sec04KeySelfTest methods are unchanged. No Messenger dependencies are passed; all four added methods return INTEGRATION_MISSING. Bundle rpc-methods.mjs and its imports with exact checked hashes. This proves composition against this known historical source only, not active Observer version compatibility. Do not apply blindly to current root. No bindings altered or OwnerACK credentials reused.

Approved activation seam is dependenciesFor(this) second argument to withMessengerA: inject independently verifying createDispatcherVerifier({fetchCerts}), pinned issuer/audience, explicit scoped authorize implementation, separately approved A credential getter and fixed Office transport. No implementation is chosen for authorize or credential custody. This is not an activation patch.

Council current source is unavailable in this artifact. Therefore no invented HTTP route, source marker, service binding name or production forwarding patch is provided. Owner must supply authorized current Council source and exact service-binding target for a source-pinned patch. Council must forward raw signed assertion plus strict inputs to the chosen method; Observer independently checks that assertion again.
