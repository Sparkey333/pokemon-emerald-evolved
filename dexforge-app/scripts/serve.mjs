import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const ROOT = join(dirname(dirname(fileURLToPath(import.meta.url))), 'dist');
const M = { '.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json',
  '.png':'image/png','.jpg':'image/jpeg','.webp':'image/webp','.csv':'text/csv','.md':'text/plain' };
createServer(async (req,res)=>{ try{
  let p = normalize(decodeURIComponent(new URL(req.url,'http://x').pathname)).replace(/^(\.\.[/\\])+/,'');
  if (p==='/'||p==='\\') p='/index.html';
  const f = await readFile(join(ROOT,p));
  res.writeHead(200,{'Content-Type':M[extname(p)]||'application/octet-stream','Cache-Control':'no-store'});
  res.end(f);
}catch{ res.writeHead(404); res.end('not found'); } })
.listen(Number(process.argv[2]||8644),()=>console.log('dexforge-app dist on '+(process.argv[2]||8644)));
