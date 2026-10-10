#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 manifests/：file_manifest.json、sha256.json、version.json。"""
import hashlib
import io
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SKIP_DIRS = {"__pycache__", ".git", "manifests"}
SKIP_EXT = {".pyc", ".pyo"}
HISTORICAL = {
    "说明": "原项目（数学建模 RAG Phase 6）的冻结产物哈希，独立于本交付包，仅作溯源用",
    "15_Phase6_Aggregation/p6_pair_labels_v3.jsonl": "3d93396a58481156",
    "15_Phase6_Aggregation/p6_metrics_v3.json": "57995470e4814aeb",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    files, total = {}, 0
    for r, dirs, fs in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in fs:
            if os.path.splitext(fn)[1].lower() in SKIP_EXT:
                continue
            p = os.path.join(r, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            files[rel] = {"sha256": sha256(p), "bytes": os.path.getsize(p),
                          "mtime": time.strftime("%Y-%m-%d %H:%M:%S",
                                                 time.localtime(os.path.getmtime(p)))}
            total += os.path.getsize(p)
    os.makedirs(os.path.join(ROOT, "manifests"), exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    io.open(os.path.join(ROOT, "manifests", "file_manifest.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"生成时间": ts, "文件数": len(files), "总字节": total,
                    "files": files}, ensure_ascii=False, indent=1) + "\n")
    io.open(os.path.join(ROOT, "manifests", "sha256.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"生成时间": ts, "范围": "本交付包全部文件（不含 manifests/ 自身）",
                    "files": {k: v["sha256"] for k, v in files.items()},
                    "historical_hashes": HISTORICAL}, ensure_ascii=False, indent=1) + "\n")
    ver = open(os.path.join(ROOT, "VERSION"), encoding="utf-8").read().strip().splitlines()
    io.open(os.path.join(ROOT, "manifests", "version.json"), "w", encoding="utf-8", newline="\n").write(
        json.dumps({"生成时间": ts, "version": ver}, ensure_ascii=False, indent=1) + "\n")
    print("文件数=%d 总字节=%.1f MB" % (len(files), total / 1048576.0))
    print("已写出 manifests/file_manifest.json、sha256.json、version.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
