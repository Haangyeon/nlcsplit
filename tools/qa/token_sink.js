// 一次性本地收件口：浏览器把 token POST 过来，直接落盘，值不经过会话记录。
// 需要那三个头，否则 https 页面 fetch http://127.0.0.1 会被私有网络/混合内容策略拦。
const http = require('node:http');
const fs = require('node:fs');
const OUT = 'E:/tmp/nlcsplit_pat.tmp';
const srv = http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Private-Network', 'true');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }
  if (req.method !== 'POST') { res.writeHead(405); res.end('no'); return; }
  let body = '';
  req.on('data', c => { body += c; if (body.length > 200) req.destroy(); });
  req.on('end', () => {
    const t = body.trim();
    if (!/^ghp_[A-Za-z0-9]{36}$/.test(t)) {
      console.log('REJECT len=' + t.length + ' prefix=' + t.slice(0, 3));
      res.writeHead(400); res.end('bad'); return;
    }
    fs.writeFileSync(OUT, t, { mode: 0o600 });
    console.log('WROTE len=' + t.length + ' file=' + OUT);   // 只报长度，不报值
    res.writeHead(200, {'Content-Type': 'text/plain'}); res.end('ok');
  });
});
srv.listen(8797, '127.0.0.1', () => console.log('sink on 8797'));
setTimeout(() => { srv.close(); console.log('sink timeout'); }, 180000);
