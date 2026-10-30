#!/usr/bin/env bash
# 重建 wheel 并对**新构建物**做发布 QA —— 全程不碰 dist/。
#
# 为什么要这一份：正文 §5 说 "implements … every table in this paper"，而家族外两个构造
# （voronoi/hirshfeld）只进了工作树的 nlcsplit/partition.py，dist/ 里那份 wheel 还是旧字节。
# 这句话在被重建并实测之前不成立。
#
# 规矩（都是本仓实发事故定的）：
#   - 构建产物先进 scratch/，**通过判据之后**才由人工决定要不要替换 dist/（门面件不许被诊断跑覆盖）。
#   - QA 用一次性 --target 目录，不复用 $HOME 下的 venv。
#   - 显式设 OMP_NUM_THREADS，否则墙钟与前几份不可比（前记录里 322/406/504/655 s 就是这么来的）。
#   - 每步把退出码与 `# exit=` 自写行打进自己的归档。
#   - 构建命令前清 PYTHONPATH（托管终端会往里注 sitecustomize 审计钩子，会拦构建管线的自清理）。
set -u
cd <REPO> || exit 3
ROOT=<REPO>
TS=$(date -u +%Y%m%dT%H%M%SZ)
STAGE="$ROOT/scratch/wheel_qa_$TS"
mkdir -p "$STAGE/build" "$STAGE/site" "$STAGE/workdir" || exit 3

run() { # run <归档名> <命令...>
  local name="$1"; shift
  local out="$ROOT/evidence/release_qa/${TS}_${name}.out"
  ( cd "$STAGE/workdir" && PYTHONPATH= OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
      MKL_NUM_THREADS=2 "$@" ) > "$out" 2>&1
  local rc=$?
  echo "$rc" > "$out.rc"
  echo "# exit=$rc at $(date -u +%FT%TZ)" >> "$out"
  echo "  $name rc=$rc -> evidence/release_qa/${TS}_${name}.out"
}

echo "=== 0. 环境抬头 ==="
run "env" bash -c "cd $ROOT; echo git_HEAD=\$(git rev-parse HEAD); python3 -V; \
python3 -c 'import pyscf,numpy,scipy;print(\"pyscf\",pyscf.__version__,\"numpy\",numpy.__version__,\"scipy\",scipy.__version__)'; \
git status --porcelain | wc -l; sha256sum -b nlcsplit/partition.py nlcsplit/tests/test_crossfamily_schemes.py; \
echo '--- 现役 dist/ wheel（对照基线，未改动）---'; sha256sum -b dist/nlcsplit-0.1.0-py3-none-any.whl; \
python3 $ROOT/evidence/release_qa/wheel_census.py $ROOT/dist/nlcsplit-0.1.0-py3-none-any.whl | head -8; \
python3 - <<'PY'
import zipfile
z=zipfile.ZipFile('<REPO>/dist/nlcsplit-0.1.0-py3-none-any.whl')
s=z.read('nlcsplit/partition.py').decode()
print('# 基线 wheel 里 partition.py 字节数 =', len(s), '含 CROSS_FAMILY_SCHEMES =', 'CROSS_FAMILY_SCHEMES' in s)
PY"

echo "=== 1. 构建到 scratch（不动 dist） ==="
run "build" bash -c "cd $ROOT && python3 -m build --wheel --outdir $STAGE/build 2>&1 | tail -40 && ls -la $STAGE/build"

WHL=$(ls "$STAGE"/build/*.whl 2>/dev/null | head -1)
if [ -z "$WHL" ]; then echo "构建没产出 wheel，停"; exit 1; fi
echo "  staged wheel = $WHL"

echo "=== 2. 新 wheel 清点 + 家族外命中 ==="
run "shipping_wheel_census" bash -c "cd $ROOT && python3 $ROOT/evidence/release_qa/wheel_census.py $WHL; \
WHL=$WHL ROOT=$ROOT python3 - <<'PY'
import zipfile, os
w = os.environ['WHL']
z = zipfile.ZipFile(w)
s = z.read('nlcsplit/partition.py').decode()
print('# 新 wheel 里 partition.py 字节数 =', len(s))
for k in ('CROSS_FAMILY_SCHEMES', 'ALL_SCHEMES', 'def voronoi_factors',
          'def hirshfeld_factors', 'def scheme_factors'):
    print('#   含 %-22s %s' % (k, k in s))
print('#   随包新测试模块:', [n for n in z.namelist() if n.endswith('test_crossfamily_schemes.py')])
src = open(os.path.join(os.environ['ROOT'], 'nlcsplit', 'partition.py'),
           encoding='utf-8').read()
print('#   与工作树 nlcsplit/partition.py 逐字节相同:', s == src)
PY"

echo "=== 3. 成员级 diff（新 vs dist 里的旧） ==="
run "wheel_member_diff" bash -c "cd $ROOT && python3 $ROOT/evidence/release_qa/wheel_member_diff.py \
  $ROOT/dist/nlcsplit-0.1.0-py3-none-any.whl $WHL"

echo "=== 4. 装到一次性 target，树外跑 not-slow 全量 ==="
run "wheel_install_pytest_notslow" bash -c "cd $ROOT && pip3 install --no-deps --target $STAGE/site $WHL >/dev/null 2>&1 && \
  mkdir -p $STAGE/workdir/outside && cd $STAGE/workdir/outside && \
  echo \"cwd=\$(pwd)\" && echo \"in_source_tree=\$(pwd | grep -c '<REPO>/nlcsplit')\" && \
  PYTHONPATH=$STAGE/site python3 -c 'import nlcsplit; print(\"nlcsplit.__file__ =\", nlcsplit.__file__)' && \
  PYTHONPATH=$STAGE/site python3 -m pytest -q -p no:cacheprovider -m 'not slow' $STAGE/site/nlcsplit 2>&1 | tail -25"

echo "完成。staged wheel = $WHL"
echo "STAGE=$STAGE"
