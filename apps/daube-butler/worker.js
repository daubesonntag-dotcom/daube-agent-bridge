/* D'AUBE Butler 0.2.1 - PUBLIC READ-ONLY MCP, isolated Cloudflare Worker.
 * Stateless; no account data, access tokens, external calls, writes or automatic delegation.
 * Only intentionally public project metadata and advisory results.
 */
const VERSION="0.2.1";
const CONTACT="founder@daubesonntag.com";
const OWNER={
"engineering":["D'AUBE engineering governance","exact-SHA independent QA"],
"documents":["D'AUBE document QA","source-provenance and human review"],
"product-design":["D'AUBE product design owner","design-review"],
"communications":["D'AUBE communications owner","outbound-send-approval"],
"scheduling":["D'AUBE scheduling owner","calendar-owner-permission"],
"deployment-infra":["D'AUBE approved infrastructure executor","release-permit and rollback"],
"backend-data":["D'AUBE data engineering owner","tenant-isolation and schema-review"],
"general-ai":["D'AUBE model governor","model, privacy and cost gate"]
};
const MODES=["observe","prepare","mutate","high_risk"];
const HIGH=/\b(delete|wipe|purge|erase|revoke|transfer money|pay|charge|purchase|deploy to prod(?:uction)?|publish|post publicly|send email|send message|api key|password|token|oauth|credential|remove owner|admin role)\b|x[oó]a|chuy[eể]n ti[eề]n|thanh to[aá]n|đ[aă]ng công khai|c[aấ]p quy[eề]n|g[uử]i mail/i;
const WRITE=/\b(write|commit|push|merge|upload|modify|update|edit|create|schedule|send|change|install|enable|disable)\b|s[uử]a|c[aậ]p nh[aậ]t|t[aạ]o|tri[eể]n khai/i;
const SECRET=/(sk-[A-Za-z0-9_-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|\b(?:password|api[_ -]?key|otp|secret|token)\s*[:=]\s*\S+)/i;
const props={
project:{type:"string",enum:["D_AUBE"],default:"D_AUBE"},
task_class:{type:"string",enum:Object.keys(OWNER)},
summary:{type:"string",minLength:1,maxLength:280},
requested_mode:{type:"string",enum:MODES,default:"prepare"},
acceptance:{type:"string",minLength:1,maxLength:300},
task_summary:{type:"string",minLength:1,maxLength:280},
source_ref:{type:"string",maxLength:250,default:""},
action_type:{type:"string",enum:["observe","prepare","mutate","public_post","financial","credential","production","destructive"]},
claimed_status:{type:"string",maxLength:40},
evidence_type:{type:"string",maxLength:80},
external_verification:{type:"boolean",default:false}
};
function tool(name,title,description,fields,required) {
 let p={}; for(const f of fields)p[f]=props[f];
 return {name,title,description,inputSchema:{type:"object",properties:p,required,additionalProperties:false},
 annotations:{readOnlyHint:true,openWorldHint:false,destructiveHint:false,idempotentHint:true}};
}
const TOOLS=[
tool("classify_task","Classify D'AUBE task risk","Classify a bounded D'AUBE task and advise an approval gate. Never starts work.",["project","task_class","summary","requested_mode"],["task_class","summary"]),
tool("suggest_route","Suggest D'AUBE work owner","Advise which existing owner class to consult, without contacting or dispatching to plugins.",["project","task_class"],["task_class"]),
tool("draft_handoff","Draft agent handoff","Prepare an unsent and unqueued draft packet for independent review.",["project","task_class","task_summary","acceptance","source_ref"],["task_class","task_summary","acceptance"]),
tool("explain_authority","Explain approval requirements","Explain which action categories must be held for registered executor and owner approval.",["action_type"],["action_type"]),
tool("check_receipt","Review completion claim","Evaluate evidence category; cannot establish independent verification or mark DONE.",["claimed_status","evidence_type","external_verification"],["claimed_status","evidence_type"])
];
function bounded(v,n){
 if(typeof v!=="string"||v.length>n||SECRET.test(v)||/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/.test(v))throw Error("Unsafe or out-of-bounds text");
 return v.trim();
}
function validate(t,vals){
 if(!vals||typeof vals!=="object"||Array.isArray(vals))throw Error("Expected an object");
 const schema=t.inputSchema;
 for(const k of Object.keys(vals)){
  const f=schema.properties[k];if(!f)throw Error("Unknown field");
  if(typeof vals[k]!==f.type)throw Error("Wrong field type");
  if(f.enum&&!f.enum.includes(vals[k]))throw Error("Invalid field value");
  if(f.type==="string"&&((f.minLength!==undefined&&vals[k].length<f.minLength)||(f.maxLength!==undefined&&vals[k].length>f.maxLength)))throw Error("Invalid field length");
  if(f.type==="string")bounded(vals[k],f.maxLength||280);
 }
 for(const k of schema.required)if(!(k in vals))throw Error("Missing required field");
}
function run(name,p){
 if(p.project!==undefined&&p.project!=="D_AUBE")throw Error("Project unavailable");
 if(name==="classify_task"||name==="draft_handoff"||name==="suggest_route"){
  if(!OWNER[p.task_class])throw Error("Unsupported task class");
 }
 if(name==="suggest_route")return {project:"D_AUBE",task_class:p.task_class,recommended_route:OWNER[p.task_class][0],required_gate:OWNER[p.task_class][1],owner_verified:false,tool_invoked:false,status:"ADVISORY_ONLY"};
 if(name==="classify_task"||name==="draft_handoff"){
  const summary=bounded(name==="classify_task"?p.summary:p.task_summary,280);
  const riskSignal=HIGH.test(summary)?"high_risk":WRITE.test(summary)?"mutate":"observe";
  const req=name==="classify_task"?(p.requested_mode||"prepare"):"prepare";
  const risk=MODES[Math.max(MODES.indexOf(req),MODES.indexOf(riskSignal))];
  const held=MODES.indexOf(risk)>=2;
  const status=held?"HOLD":"PREPARED_FOR_REVIEW";
  if(name==="classify_task")return {project:"D_AUBE",task_class:p.task_class,risk,status,suggested_owner_class:OWNER[p.task_class][0],required_gate:OWNER[p.task_class][1],external_action_authorized:false,approval_granted:false,next_step:held?"Obtain scoped owner permit and independently verified runtime approval.":"Prepare an independently reviewable handoff."};
  const acceptance=bounded(p.acceptance,300),source=bounded(p.source_ref||"",250);
  if(!acceptance||/^(?:file:|javascript:|data:)/i.test(source))throw Error("Invalid acceptance or reference");
  return {status:held?"HOLD":"DRAFT_NOT_SENT",packet:{project:"D_AUBE",task_class:p.task_class,intent:summary,acceptance,source_ref:source,risk,proposed_owner:OWNER[p.task_class][0],required_gate:OWNER[p.task_class][1]},message_sent:false,queued:false,external_action_authorized:false,approval_granted:false,owner_verified:false};
 }
 if(name==="explain_authority"){
  const allow=["observe","prepare"].includes(p.action_type);
  return {action_type:p.action_type,status:allow?"PREPARE_ONLY":"HOLD",rule:allow?"Read-only analysis is advisory. No external tools are called.":"Specific external permission, an approved executor, and independent readback are required.",permit_issued:false,external_action_authorized:false};
 }
 if(name==="check_receipt")return {status:"EXTERNAL_READBACK_REQUIRED",reported_claim:p.claimed_status,evidence_category:p.evidence_type,external_verification_claim_supplied:!!p.external_verification,independently_verified:false,may_claim_done:false,next_step:"Verify receipt at authoritative source with an authorized separate tool."};
 throw Error("Unknown tool");
}
function json(d,status=200,extra={}){return new Response(JSON.stringify(d),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff","referrer-policy":"no-referrer",...extra}})}
function rpc(id,res){return json({jsonrpc:"2.0",id,result:res})}
function err(code,msg,id=null){return json({jsonrpc:"2.0",id,error:{code,message:msg}})}
function doc(body,title){
 const css=':root{color-scheme:light dark;font:16px/1.65 system-ui,-apple-system,sans-serif;color:#183137;background:#f5f7f5}body{margin:0}.shell{max-width:880px;margin:auto;padding:24px 28px 70px}header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:15px;border-bottom:1px solid #adc1bd;padding:6px 0 20px}nav{display:flex;gap:17px;flex-wrap:wrap}a{color:#12716c}a:hover{text-decoration:underline}nav a{text-decoration:none;font-size:.9rem;font-weight:650}.brand{color:inherit;text-decoration:none;font-weight:800;font-size:1.1rem}main{padding:34px 0}h1{font-size:clamp(2rem,5vw,3rem);line-height:1.1;letter-spacing:-.035em}h2{font-size:1.2rem;margin-top:32px}p,li{max-width:76ch}footer{font-size:.85rem;border-top:1px solid #adc1bd;padding-top:20px;color:#697f80}.hint{border:1px solid #8dbcb1;border-radius:12px;background:#e8f3ef;padding:15px 18px}.muted{color:#536b70}@media(prefers-color-scheme:dark){:root{background:#101c21;color:#e0edeb}a{color:#90dacb}.hint{background:#1a3935}footer{color:#b8c8c5}}';
 return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="D’AUBE Butler operational governance: '+title+'"><title>'+title+' — D’AUBE Butler</title><style>'+css+'</style></head><body><div class="shell"><header><a class="brand" href="/">D’AUBE / BUTLER</a><nav aria-label="Primary"><a href="/">Overview</a><a href="/support">Support</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a></nav></header><main>'+body+'</main><footer>© D’AUBE Sonntag · Butler v'+VERSION+' · Contact: <a href="mailto:'+CONTACT+'">'+CONTACT+'</a></footer></div></body></html>';
}
const PAGES={
"/":doc('<p class="muted">D’AUBE SONNTAG · Task governance</p><h1>Governed task routing, without hidden execution.</h1><p>D’AUBE Butler provides five read-only MCP tools for classifying operational risk, suggesting an accountable owner, preparing a handoff, explaining approval requirements and evaluating evidence claims.</p><div class="hint"><strong>Security boundary:</strong> Butler does not read your Gmail, browser, files or other plugin accounts. It cannot call another plugin, send a message, enqueue a job, modify records, approve an action, or spend money. It only returns advisory results.</div><h2>Documentation</h2><p>Review our <a href="/privacy">Privacy Policy</a>, <a href="/terms">Terms</a> or <a href="/support">Support</a> instructions.</p><h2>Service checks</h2><p>Public status: <a href="/health">health</a>. MCP endpoint: <code>/mcp</code> (JSON-RPC, Streamable HTTP). No user login or private data access.</p>',"Overview"),
"/privacy":doc('<h1>Privacy Policy</h1><p><strong>Effective: 15 October 2026.</strong> Controller/publisher contact: D’AUBE Sonntag, <a href="mailto:'+CONTACT+'">'+CONTACT+'</a>.</p><h2>What is processed</h2><p>When you use Butler, the MCP server receives only the tool arguments supplied by the ChatGPT/Codex host: a task class, a short task summary, risk mode, acceptance criterion, source reference, or asserted evidence type. These fields may incidentally contain personal data if you include it. Do not submit customer data, authentication secrets, payment details, medical information or other sensitive material.</p><h2>Purpose and handling</h2><p>Butler processes input in memory to return a read-only advisory classification or draft. No account integrations, profile marketing, analytics identifiers, user database, outbound agent handoffs or automated third-party actions are implemented in this release. Butler does not intentionally retain tool arguments or write request bodies to an application database.</p><h2>Host and recipients</h2><p>The public MCP service and documentation are hosted through Cloudflare. Cloudflare may process security and network metadata under its own terms and configuration. ChatGPT or Codex may store conversation and tool information according to the host’s privacy policy and settings. The Butler server does not forward task content to other plugins or external agents.</p><h2>Logs and retention</h2><p>This stateless Worker does not create application-level task logs or persistent task records. Provider-operated network, security and diagnostic metadata may be retained according to Cloudflare’s applicable settings and policies; the publisher does not represent that all infrastructure logs have zero retention or that it controls host conversation retention. No exact provider-wide log retention period is asserted without verified infrastructure settings.</p><h2>Security and access</h2><p>Inputs are bounded, schema-checked and scanned for obvious secrets. The public tools never return private stored records or authorize state changes. Any future authenticated or state-changing features require separate consent, documentation and authorization testing.</p><h2>Contact and requests</h2><p>For privacy, access or deletion inquiries, email <a href="mailto:'+CONTACT+'">'+CONTACT+'</a> with non-sensitive details. Requests concerning ChatGPT account data should use OpenAI’s own controls. This policy may be updated if hosting, retention, functionality or law changes; the effective date will be updated.</p>',"Privacy"),
"/terms":doc('<h1>Terms of Service</h1><p><strong>Effective: 15 October 2026.</strong> D’AUBE Butler is provided by the D’AUBE Sonntag project. For support or legal inquiries email <a href="mailto:'+CONTACT+'">'+CONTACT+'</a>.</p><h2>Scope</h2><p>Butler is a no-charge, read-only operational advice service. It can classify D’AUBE tasks, propose an owner class, draft unsent handoffs, explain approval gates and evaluate completion claims. It is not a job executor, access control authority, messaging provider, payments service, or backup product.</p><h2>Authorized use</h2><p>Use the tools only with information you are entitled to submit. Do not include account credentials, sensitive records or instructions to bypass another provider’s permission gate. A suggested route is not permission to access another service.</p><h2>Other services</h2><p>ChatGPT, Codex, Cloudflare and separately connected tools have independent terms. Butler has no ability to invoke other plugins or perform operations on your behalf. To take action, use the authorized provider with its normal permissions and approvals.</p><h2>Availability and reliance</h2><p>Outputs are advisory and may be incomplete. Verify critical facts, receipts, approvals and operational decisions independently. We do not promise uninterrupted service or make unsupported guarantees of compatibility or results. Applicable mandatory consumer or statutory rights are unaffected.</p><h2>Changes</h2><p>Functionality, hosting and these terms may change; material changes will be reflected in dated published notices. Paid use, authenticated account access or write capabilities are not part of this version and would require a separate update.</p><h2>Contact</h2><p>Contact <a href="mailto:'+CONTACT+'">'+CONTACT+'</a>. Do not send secrets or personal customer records by email.</p>',"Terms"),
"/support":doc('<h1>Support</h1><p>For D’AUBE Butler inquiries, email <a href="mailto:'+CONTACT+'">'+CONTACT+'</a>. Response timing is not guaranteed. Do not include passwords, API keys, private account data or customer records.</p><h2>Report an issue</h2><p>Provide the tool name, approximate date and time, a redacted description, expected behavior and observed behavior. Never share access tokens or sensitive logs.</p><h2>Supported tools</h2><p><code>classify_task</code>, <code>suggest_route</code>, <code>draft_handoff</code>, <code>explain_authority</code> and <code>check_receipt</code>. The tool results are advisory; no execution or approval is performed.</p><h2>Data requests</h2><p>Email the same address for privacy-related questions. Account connections and conversation history are controlled by their respective host providers.</p>',"Support")
};
addEventListener("fetch",event=>event.respondWith(handle(event.request)));
async function handle(request){
 const url=new URL(request.url),path=url.pathname.replace(/\/$/,"")||"/";
 const origin=request.headers.get("Origin");
 if(origin&&!["https://chatgpt.com","https://platform.openai.com"].includes(origin))return new Response("Origin denied",{status:403});
 if(path==="/health"&&request.method==="GET")return json({status:"ok",version:VERSION,mode:"read-only",external_action_authorized:false,task_storage:false});
 if(path==="/.well-known/openai-apps-challenge") {
 if(request.method!=="GET")return new Response(null,{status:405});
 const token=(typeof OPENAI_APPS_CHALLENGE_TOKEN==="string"?OPENAI_APPS_CHALLENGE_TOKEN:"").trim();
 return token ? new Response(token,{headers:{"content-type":"text/plain; charset=utf-8","cache-control":"no-store","x-content-type-options":"nosniff"}}) : new Response("Challenge not configured",{status:503,headers:{"cache-control":"no-store"}});
}
 if(path==="/robots.txt")return new Response("User-agent: *\nAllow: /\n",{headers:{"content-type":"text/plain"}});
 if(PAGES[path]&&request.method==="GET")return new Response(PAGES[path],{headers:{"content-type":"text/html; charset=utf-8","cache-control":"public,max-age=3600","x-content-type-options":"nosniff","x-frame-options":"DENY","content-security-policy":"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'none';","referrer-policy":"no-referrer"}});
 if(path!=="/mcp")return new Response("Not found",{status:404});
 if(request.method==="GET"||request.method==="DELETE")return new Response(null,{status:405,headers:{"allow":"POST"}});
 if(request.method!=="POST")return new Response(null,{status:405,headers:{"allow":"POST"}});
 if(!String(request.headers.get("content-type")||"").toLowerCase().startsWith("application/json"))return new Response(null,{status:415});
 const ct=Number(request.headers.get("content-length")||"0");
 if(ct>16384)return new Response(null,{status:413});
 let raw,call;try{raw=await request.text();if(raw.length>16384)return new Response(null,{status:413});call=JSON.parse(raw)}catch{return err(-32700,"Invalid JSON")}
 if(!call||Array.isArray(call)||typeof call!=="object"||call.jsonrpc!=="2.0"||typeof call.method!=="string")return err(-32600,"Invalid Request");
 if(call.method.startsWith("notifications/"))return new Response(null,{status:202});
 const id=call.id;
 if(!("id" in call)||typeof id==="boolean"||id===null||(typeof id!=="string"&&typeof id!=="number"))return err(-32600,"Request ID required");
 if(call.method==="initialize"){
  const proposed=call.params&&call.params.protocolVersion;
  const supported=["2025-03-26","2025-06-18","2025-11-25"];
  return rpc(id,{protocolVersion:supported.includes(proposed)?proposed:"2025-03-26",capabilities:{tools:{listChanged:false}},serverInfo:{name:"daube-butler",version:VERSION}});
 }
 if(call.method==="ping")return rpc(id,{});
 if(call.method==="tools/list")return rpc(id,{tools:TOOLS});
 if(call.method==="tools/call"){
  if(!call.params||typeof call.params!=="object")return err(-32602,"Invalid params",id);
  const t=TOOLS.find(v=>v.name===call.params.name);
  if(!t)return err(-32602,"Unknown tool",id);
  try{
   const a=call.params.arguments||{};
   validate(t,a);
   const result=run(t.name,a);
   return rpc(id,{isError:false,structuredContent:result,content:[{type:"text",text:JSON.stringify(result)}]});
  }catch{return rpc(id,{isError:true,content:[{type:"text",text:"Input rejected by Butler policy or schema."}]})}
 }
 return err(-32601,"Method not found",id);
}
