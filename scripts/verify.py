#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""完整性校验：python verify.py —— 对照 manifests/sha256.json 检查缺失/改动。"""
import hashlib
import io
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    man = os.path.join(ROOT, "manifests", "sha256.json")
    if not os.path.isfile(man):
        print("[FAIL] 找不到 manifests/sha256.json")
        return 1
    d = json.load(io.open(man, encoding="utf-8"))
    miss, chg, ok = [], [], 0
    for rel, exp in sorted(d.get("files", {}).items()):
        p = os.path.join(ROOT, rel)
        if not os.path.isfile(p):
            miss.append(rel)
            continue
        h = hashlib.sha256(open(p, "rb").read()).hexdigest()
        if h == exp:
            ok += 1
        else:
            chg.append(rel)
    print("校验项：%d ｜ 一致：%d ｜ 改动：%d ｜ 缺失：%d" % (len(d.get("files", {})), ok, len(chg), len(miss)))
    for x in chg[:20]:
        print("  [CHANGED] %s" % x)
    for x in miss[:20]:
        print("  [MISSING] %s" % x)
    print("VERIFY: %s" % ("PASS" if not chg and not miss else "FAIL"))
    print("历史验收 Hash（独立于本包，不参与校验）：%s" % json.dumps(d.get("historical_hashes", {}), ensure_ascii=False))
    return 0 if not chg and not miss else 1


if __name__ == "__main__":
    sys.exit(main())
