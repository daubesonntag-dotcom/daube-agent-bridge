'use strict';
const http=require('node:http'),fs=require('node:fs/promises'),path=require('node:path');
const SOCKET='/run/daube-sovereign/browser-control-v1.sock';
const ALLOW=new Set(['https://daube-hybrid-staging-v1.spacew039.workers.dev/health']);
function reply(res,status,value){res.writeHead(status,{'content-type':'application/json','cache-control':'no-store','x-content-type-options':'nosniff'});res.end(JSON.stringify(value));}
async function body(req){let data='',n=0;for await(const part of req){n+=part.length;if(n>1024)throw Error('TOO_LARGE');data+=part.toString('utf8')}return JSON.parse(data);}
async function startControlSocket({activeTab,navigate,socketPath=SOCKET}){
 if(typeof activeTab!=='function'||typeof navigate!=='function'||!path.isAbsolute(socketPath))throw Error('BAD_CONFIG');
 try{await fs.lstat(socketPath);throw Error('EXISTING_SOCKET')}catch(e){if(e.code!=='ENOENT')throw e}
 const server=http.createServer(async(req,res)=>{
  const url=new URL(req.url||'/','http://local.invalid');
  if(url.search||req.headers.origin)return reply(res,403,{error:'DENIED'});
  try{
   if(req.method==='GET'&&url.pathname==='/health')return reply(res,200,{service:'daube-browser-control-v1',transport:'unix-socket',mode:'pilot'});
   const tab=activeTab();
   if(!tab?.view?.webContents||tab.view.webContents.isDestroyed())return reply(res,503,{error:'NO_TAB'});
   // Never expose page text from a manually selected tab outside the pilot URL allowlist.
   if(url.pathname==='/inspect'&&!ALLOW.has(tab.view.webContents.getURL()))return reply(res,403,{error:'DENIED'});
   if(req.method==='GET'&&url.pathname==='/inspect'){
    const snapshot=await tab.view.webContents.executeJavaScript("(() => ({title:String(document.title||'').slice(0,150),url:location.href.slice(0,600),text:String(document.body?.innerText||'').slice(0,1200)}))()",false);
    return reply(res,200,{tab:snapshot});
   }
   if(req.method==='POST'&&url.pathname==='/navigate'){
    const input=await body(req);if(typeof input.url!=='string'||!ALLOW.has(input.url))return reply(res,403,{error:'DENIED'});
    const finalUrl=await navigate(input.url);if(!ALLOW.has(finalUrl))return reply(res,403,{error:'REDIRECT_OUTSIDE_ALLOWLIST'});return reply(res,200,{navigated:true,url:finalUrl});
   }
   return reply(res,404,{error:'NOT_FOUND'});
  }catch{return reply(res,503,{error:'BROWSER_UNAVAILABLE'})}
 });
 server.requestTimeout=7000;server.headersTimeout=5000;server.maxRequestsPerSocket=25;
 await new Promise((ok,fail)=>{server.once('error',fail);server.listen(socketPath,()=>{server.off('error',fail);ok()})});
 await fs.chmod(socketPath,0o600);
 return {socketPath,close:async()=>{await new Promise(ok=>server.close(ok));await fs.unlink(socketPath).catch(e=>{if(e.code!=='ENOENT')throw e})}};
}
module.exports={startControlSocket};