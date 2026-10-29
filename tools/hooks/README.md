# 闸门层（tools/hooks/）

这一层不是给我的提示词，是**装在我外面的机械检查**。写它的理由：本模型的会话越长越会把
"我记得的状态"当成"状态"，本仓一周内的真实事故全是这一类（搬错版本的数、把计数当测量、
引用不存在的文件、把注释里的数当出处）。靠我"下次注意"是无效的，注意本身就是那条会漏的环节。

## 六个闸门

| 文件 | 事件 | 判据（只判机械可判的） | 失败动作 |
|---|---|---|---|
| `../claim_gate.js` | PostToolUse / PreToolUse(`git commit`) / Stop | 已发出的稿里每个小数必须能在**被 git 跟踪的证据工件**里找到；每个反引号里的路径必须存在且已跟踪 | exit 2，stderr 是修法 |
| `comment_sentinel.js` | PostToolUse | 代码注释里出现 ≥4 位小数或带单位的数——注释不是测量，不该长得像 | exit 2 |
| `precommit_gate.js` | PreToolUse(`Bash(git commit*)`) | MANIFEST 新鲜 + 数字出处 + 路径入库 | exit 2（拦提交） |
| `route_decisions_to_referee.js` | PreToolUse(`AskUserQuestion`) | 判断/评审/取舍问题必须走 referee MCP；只有凭据、花钱、投稿/删除等不可逆授权或作者元数据可问用户 | exit 2，stderr 指向 referee |
| `stop_gate.js` | Stop（`asyncRewake`） | 还有未提交的实质改动 / 清单陈旧 / 数字无原件 | exit 2 并把我叫醒 |
| `session_brief.js` | SessionStart / PreCompact | 不拦；把 HEAD、脏文件、清单状态、注册状态、闸门计数注入上下文 | — |

## 装 / 查

`.qoder/` 在 .gitignore 里，所以**注册不在版本库**。入库的是 `settings.fragment.json`：

```bash
node tools/hooks/install.js --check    # 只回答"当前注册 == 入库那份吗"
node tools/hooks/install.js            # 装；已存在且不同则拒绝（--force 才覆盖）
```

`session_brief.js` 每次开场都会把 `--check` 的结果打进简报。这条是防"我改了脚本就以为闸门在跑"
——本仓真栽过一次（注册不触发，五个闸门全静默）。

## 跑自检（每个闸门必须能证明自己能失败）

```bash
node tools/claim_gate.js --selftest          # 真数不拦 / 假数拦 / 假路径拦 / 未跟踪拦 / 作用域双向
node tools/hooks/lib.js --selftest           # 清单核对：新鲜 0、改一字节 1、多文件 1、清单读不出 1
node tools/hooks/install.js --selftest       # 注册比较器：相同/缺事件/改命令/键序不同
node tools/hooks/route_decisions_to_referee.js --selftest  # 判断问题拦 / 授权与元数据放行
node tools/hooks/comment_sentinel.js --selftest
node tools/hooks/precommit_gate.js --selftest   # 含临时坏仓的反向验证 + 逃生口留痕验证
node tools/hooks/stop_gate.js --selftest
```

自检全绿之前，不要把任何闸门当"在跑"。

## 逃生口（有，但不是静默的）

- 提交：commit message 里写 `[gate-bypass: 一句话理由]`。
- 收工：最后一段话里写同样格式。

两者都会把"绕过时的问题清单"追加到 `tools/hooks/GATE-OVERRIDES.log`（故意不放 `evidence/`：
那里每个目录都被 `MANIFEST.sha256` 锁着，一个只增的日志放进去，逃生口自己就会制造下一条违规）。
留痕失败时闸门**不免除拦截**。

## 明确不做的

- 不跑 pytest（慢的守卫会被绕开）；不碰网络；不查集群状态（那是任务清单的活）。
- 不判语义："这个数是不是在说另一件事"看不见，那仍然是人（和 `evidence/` 里的原件）的活。
- 台账 `paper/notes/`、`paper/software_notes/` 不在拦的范围里——那里本来就是攒"还没找到原件的数"
  的队列；拦它等于逼着把台账塞进 allowlist，闸门一吵就没人信它的红了。要查单份台账用
  `node tools/claim_gate.js --dump paper/notes/number_audit.md`。
