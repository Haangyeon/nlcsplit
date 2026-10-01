// 导出器报 files=207 / treeFiles=209，差 2。列出到底是哪两个文件没进 dist。
const fs = require('fs'), path = require('path');
const ROOT = process.argv[2] || 'E:/tmp/citree';
const walk = (d, base = '', acc = []) => {
  for (const e of fs.readdirSync(d, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const rel = base ? base + '/' + e.name : e.name;
    if (e.isDirectory()) walk(path.join(d, e.name), rel, acc); else acc.push(rel);
  }
  return acc;
};
const out = walk(path.join(ROOT, 'dist', 'nlcsplit'));
const src = walk(ROOT).filter(f => !f.startsWith('dist/'));
console.log(`src=${src.length} out=${out.length}`);
const only = (a, b) => a.filter(x => !b.includes(x));
console.log('只在 src:', only(src, out).join('\n  ') || '(无)');
console.log('只在 out:', only(out, src).join('\n  ') || '(无)');
