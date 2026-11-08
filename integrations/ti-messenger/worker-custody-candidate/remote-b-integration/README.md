# Strict B machine-only source candidate

Latest user separation requirement: AI identities belong to AI supervisors/staff; Founder identity stays Founder. This bounded candidate does not invent or enroll staff identities.

Base handler independently fetched from PR101 refb7e54d6, Git blob62d98e076c9cce1999099204904655b4dc6d413e. It matches the preceding reviewed machine-context candidate, including its delegated Founder branch. This revision removes that branch entirely from the B consumer. No scoped grant can turn a Founder email into a B consumer principal: rejection occurs before authorize, credential access or provider I/O.

Only the exact existing verifier B context is admissible: verification marker ACCESS_JWT_RS256_VERIFIED, B ClientID6120a6eb353588180a8f8c8ca93a39a1.access, exact existing issuer/audience, fresh expiry, nonempty verifiedAssertion, no email. A and unregistered staff IDs are denied. The context must come from existing cryptographic authenticate(req,{machine:true}), never JSON or caller headers. A trusted context shape is not itself cryptographic proof. Explicit reviewed scoped authorization remains mandatory and default-deny, even for verified B.

Root candidate is pinned adaptation of original v8 root50cf4a887… rather than an assertion about currently deployed bytes. Its B-only route invokes the machine verifier before the human gate, returns403 on missing machine identity, and never falls through into the human route for B. Existing POST Origin/content-type/fetch-site guards remain. Other Founder UI/operations and routing remain unchanged. A separately reproduced mixed-claim flaw is repaired in human authenticate: any common_name property is rejected in the human lane. Valid human claims without that machine marker retain existing policy; no email allowlist change is made. No staff registry, caller grant, secret binding or authorization module is added. Owner must supply exact current root/module inventory and a real reviewed authorizeRemoteB module before release; current candidate import intentionally cannot resolve that absent module.

Response compatibility change: B consumer response now uses targetActor='agent:daube' to identify destination role. The old unconditional actor field is removed. authenticatedActor='agent:daube' appears only after trusted verifier-context validation, including on later authorization denial; it indicates authentication, not permission. Earlier route/principal denials have no authenticatedActor. Clients relying on actor must migrate to the correct target/authenticated distinction. Office observedActor checks and read/write receipt checks remain separate and unchanged.

49/49 supplied tests pass: preceding32 integration regressions migrated to machine verifier fixtures,13 prior context/route tests adjusted for strict human denial,3 extra staff/label tests plus one static mixed-claim regression. Independent review also passed four synthetic signed-JWT tests. All fixtures are synthetic; Python fixture remains test-only. No JWT live session, provider E2E, deployment, secret access, remote write or persistent permission/configuration change was performed. Root syntax checks are not Worker bundle/runtime proof.

Proposed relative source paths under an owner-approved review folder:
- remote-b-consumer-v1.mjs (changed handler)
- worker.mjs (root candidate, not production overwrite)
- reciprocal.mjs (unchanged helper)
- remote-b-consumer-v1.test.mjs, integration.test.mjs, machine.test.mjs (tests)
- ti_messenger_mcp.py (test-only exact fixture, never install/bundle)
No __pycache__ files belong in publication.
