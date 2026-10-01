// 复现闸门 W 的两条自检探针，把子进程的 stdout/stderr 原样打出来。
// 只查，不改任何东西。
const cp = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const ROOT = process.argv[2];
const probe = (name, body) => {
  const f = path.join(os.tmpdir(), `gateW-probe-${name}.md`);
  fs.writeFileSync(f, body);
  const r = cp.spawnSync(process.execPath,
    [path.join(ROOT, 'tools', 'audit_share_rule.js'), '--files=' + f],
    { encoding: 'utf8', cwd: ROOT });
  console.log(`--- ${name}  file=${f}`);
  console.log(`    status=${r.status}  signal=${r.signal}  err=${(r.error && r.error.message) || 'none'}`);
  console.log('    stdout:\n' + (r.stdout || '').split('\n').map(l => '      ' + l).join('\n'));
  console.log('    stderr:\n' + (r.stderr || '').split('\n').map(l => '      ' + l).join('\n'));
};
probe('dirty', '# t\n\n甲烷二聚体的非局域项占 ΔE_xc 的 240%。\n');
probe('clean', '# t\n\n水二聚体的非局域项占 ΔE_xc 的 16%。\n');
