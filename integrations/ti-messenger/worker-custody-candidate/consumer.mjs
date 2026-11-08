// Source-only integration seam. No fetch handler, bindings, deployment, or caller verifier.
export function createConsumer({policy, credentialBinding, verifyCaller, transport}) {
  const p = Object.freeze({...policy});
  const actors = {'8ceae31b13c0a5f495c8374e6a8aced4.access':'agent:ti', '6120a6eb353588180a8f8c8ca93a39a1.access':'agent:daube'};
  if (actors[p.clientId] !== p.actor || !['agent:ti','agent:daube'].includes(p.actor) || !p.caller ||
      !/^[a-f0-9]{32}\.access$/.test(p.clientId) ||
      !/^https:\/\/(council|office-origin)\.daubesonntag\.com\/api\/agent-chat\/rooms\/council\/messages$/.test(p.destination) ||
      typeof verifyCaller !== 'function' || typeof transport !== 'function' ||
      typeof credentialBinding?.get !== 'function') throw new Error('POLICY_INCOMPLETE');
  return Object.freeze({async send(callerEvidence, input) {
    // Nothing from an untrusted caller selects identity, destination, or binding.
    let dispatched = false;
    const unknown = () => ({status:'UNKNOWN_COMMIT',safeToRetry:false});
    try {
      if (input && typeof input === 'object') input = Object.freeze({...input});
      const grant = await verifyCaller(callerEvidence);
      if (!grant || grant.caller !== p.caller || grant.actor !== p.actor ||
          grant.operation !== 'messenger.send' || grant.destination !== p.destination) return {status:'DENIED'};
      if (!input || Object.keys(input).sort().join(',') !== 'clientMessageId,kind,text' ||
          typeof input.clientMessageId !== 'string' || input.clientMessageId.length !== 36 || !/^[a-f0-9]{8}-[a-f0-9]{4}-[1-8][a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$/i.test(input.clientMessageId) ||
          !['text','challenge'].includes(input.kind) || typeof input.text !== 'string' ||
          input.text !== input.text.trim() || !input.text || input.text.length > 4000)
        return {status:'INPUT_INVALID'};
      input = Object.freeze({...input});
      const body = JSON.stringify(input);
      if (new TextEncoder().encode(body).length > 8192) return {status:'INPUT_INVALID'};
      const raw = await credentialBinding.get();
      // Flat exact JSON grammar rejects duplicate keys, extra fields, escapes and controls.
      if (typeof raw !== 'string' || raw.length > 8192 ||
          !/^\s*\{\s*"clientId"\s*:\s*"[a-f0-9]{32}\.access"\s*,\s*"clientSecret"\s*:\s*"[!#-\[\]-~]{16,4096}"\s*\}\s*$/.test(raw))
        return {status:'CREDENTIAL_INVALID'};
      const credential = JSON.parse(raw);
      if (credential.clientId !== p.clientId) return {status:'CREDENTIAL_IDENTITY_MISMATCH'};
      dispatched = true;
      const response = await transport(p.destination, {method:'POST',redirect:'error',
        signal:AbortSignal.timeout(8000),headers:{'CF-Access-Client-Id':credential.clientId,
        'CF-Access-Client-Secret':credential.clientSecret,'Content-Type':'application/json',
        Origin:new URL(p.destination).origin},body});
      if (response.status !== 200 && response.status !== 201) return unknown();
      const reader = response.body.getReader(); const chunks=[]; let size=0;
      try { for (;;) { const {done,value}=await reader.read(); if(done) break;
        size+=value.byteLength; if(size>16384) {await reader.cancel(); return unknown();} chunks.push(value); }
      } finally { reader.releaseLock(); }
      const bytes=new Uint8Array(size); let offset=0; for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
      const receipt=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
      const m=receipt.message;
      if (!m || m.from!==p.actor || m.room!=='council' || m.tenantId!=='daube' ||
          m.clientMessageId!==input.clientMessageId || m.text!==input.text || m.kind!==input.kind ||
          typeof m.id !== 'string' || !/^[A-Za-z0-9_-]{12,90}$/.test(m.id) ||
          (receipt.authenticatedActor!==undefined && receipt.authenticatedActor!==p.actor)) return unknown();
      return {status:'STORED_BY_SERVER',messageId:m.id,actor:p.actor,recipientReadVerified:false};
    } catch { return dispatched ? unknown() : {status:'FAILED_CLOSED'}; }
  }});
}
