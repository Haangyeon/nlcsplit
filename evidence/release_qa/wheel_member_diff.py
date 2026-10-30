#!/usr/bin/env python3
# 目的：把"重打 wheel 只动容器哈希、不动被测内容"从一句断言变成一次可重跑的实测。
# 为什么需要它：pyproject.toml 的 readme = "README.md" 让 README 的字节进了 wheel 的
# METADATA，而正文又要引用一个 wheel 哈希 —— 自指。于是任何被引用的哈希必然来自
# 更早一版 README 的构建。能救这个局面的只有一句话：除 METADATA/RECORD 之外的成员
# 逐字节相同。这句话必须由脚本判定，不能由我说。
# 用法：python3 evidence/release_qa/wheel_member_diff.py <a.whl> <b.whl>
import hashlib
import os
import sys
import zipfile

if len(sys.argv) != 3:
    sys.exit("用法：wheel_member_diff.py <a.whl> <b.whl>")


def members(path):
    out = {}
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith("/"):
                continue
            out[n] = hashlib.sha256(z.read(n)).hexdigest()
    return out


a_path, b_path = sys.argv[1], sys.argv[2]
A, B = members(a_path), members(b_path)


def dig(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


print("# wheel 成员逐字节比对")
print("# A = %s" % a_path)
print("#     sha256=%s  size=%d" % (dig(a_path), os.path.getsize(a_path)))
print("# B = %s" % b_path)
print("#     sha256=%s  size=%d" % (dig(b_path), os.path.getsize(b_path)))
print()

only_a = sorted(set(A) - set(B))
only_b = sorted(set(B) - set(A))
common = sorted(set(A) & set(B))
diff = [n for n in common if A[n] != B[n]]
same = [n for n in common if A[n] == B[n]]

print("A 成员数=%d  B 成员数=%d  两边都有=%d  哈希相同=%d  哈希不同=%d  只在A=%d  只在B=%d"
      % (len(A), len(B), len(common), len(same), len(diff), len(only_a), len(only_b)))
for n in only_a:
    print("  only-A  %s" % n)
for n in only_b:
    print("  only-B  %s" % n)
for n in diff:
    print("  DIFF    %s\n          A=%s\n          B=%s" % (n, A[n], B[n]))

# 判定：允许不同的成员只有 dist-info 里那两份记账文件。
DISTINFO_BOOKKEEPING = ("METADATA", "RECORD")
unexpected = []
for n in diff:
    base = n.split("/")[-1]
    if not (n.endswith(".dist-info/" + base) and base in DISTINFO_BOOKKEEPING):
        unexpected.append(n)
unexpected += only_a + only_b

# 被测内容：测试模块与包内 .py。这些必须逐字节相同，否则正文不能说"只有容器变了"。
tested = [n for n in common if n.startswith("nlcsplit/") and n.endswith(".py")]
tested_same = [n for n in tested if A[n] == B[n]]
print()
print("被测内容成员（nlcsplit/**.py）=%d，其中逐字节相同=%d" % (len(tested), len(tested_same)))
for n in tested:
    if A[n] != B[n]:
        print("  被测内容变了: %s" % n)

print()
if unexpected:
    print("VERDICT REFUSED —— 除 METADATA/RECORD 之外还有 %d 处差异，"
          "正文不许说'只动容器哈希'" % len(unexpected))
    sys.exit(1)
print("VERDICT OK —— 差异只在 dist-info 的 METADATA/RECORD；"
      "%d 个 nlcsplit/**.py 成员逐字节相同" % len(tested))
