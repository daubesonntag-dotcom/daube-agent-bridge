'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const http=require('node:http');
const {startControlSocket}=require('./browser-control.cjs');
const ALLOWED='https://daube-hybrid-staging-v1.spacew039.workers.dev/health';
function call(sock,method,route,body){return new Promise((ok,bad)=>{const req=http.request({socketPath:sock,method,path:route,headers:body?{'content-type':'application/json'}:{}},res=>{let data='';res.on('data',b=>data+=b);res.on('end',()=>ok({status:res.statusCode,body:JSON.parse(data)}))});req.on('error',bad);req.end(body?JSON.stringify(body):undefined)})}
async function useFixture(callbacks,run){const folder=await fs.mkdtemp(path.join(os.tmpdir(),'daube-browser-guard-'));const socketPath=path.join(folder,'guard.sock');const instance=await startControlSocket({socketPath,...callbacks});try{await run(socketPath)}finally{await instance.close();await fs.rm(folder,{recursive:true,force:true})}}
const tab=url=>({view:{webContents:{isDestroyed:()=>false,getURL:()=>url,executeJavaScript:async()=>({url,title:'test',text:'allowlisted'})}}});
test('socket is private and health is reachable',async()=>useFixture({activeTab:()=>null,navigate:async x=>x},async sock=>{assert.equal((await call(sock,'GET','/health')).status,200);const st=await fs.stat(sock);assert.equal(st.mode&0o777,0o600)}));
test('inspection limited to allowlisted active page',async()=>useFixture({activeTab:()=>tab('https://private.example.test'),navigate:async x=>x},async sock=>assert.equal((await call(sock,'GET','/inspect')).status,403)));
test('inspection of allowlisted page succeeds',async()=>useFixture({activeTab:()=>tab(ALLOWED),navigate:async x=>x},async sock=>assert.equal((await call(sock,'GET','/inspect')).status,200)));
test('navigation prevents external redirects',async()=>useFixture({activeTab:()=>tab(ALLOWED),navigate:async()=> 'https://evil.example.test'},async sock=>assert.equal((await call(sock,'POST','/navigate',{url:ALLOWED})).status,403)));
test('untrusted navigation is refused',async()=>useFixture({activeTab:()=>tab(ALLOWED),navigate:async x=>x},async sock=>assert.equal((await call(sock,'POST','/navigate',{url:'https://evil.example.test'})).status,403)));
