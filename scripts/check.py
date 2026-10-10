#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""环境检查：python check.py —— 逐项 PASS/FAIL，最后给 RAG STATUS。"""
import io
import json
import os
import sqlite3
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RES = []


def rec(name, ok, detail="", fix=""):
    RES.append({"item": name, "ok": bool(ok), "detail": detail, "fix": fix})
    print("[%s] %s%s" % ("PASS" if ok else "FAIL", name, ("  — " + detail) if detail else ""))
    if not ok and fix:
        print("       Fix: %s" % fix)


def main():
    # 1 Python
    v = sys.version_info
    rec("Python >= 3.9", v >= (3, 9), "当前 %d.%d.%d" % (v[0], v[1], v[2]),
        "安装 Python 3.9+")

    # 2 依赖
    missing = []
    for mod in ("numpy", "fastembed", "yaml"):
        try:
            __import__(mod)
        except Exception:
            missing.append(mod)
    rec("Dependencies", not missing, "缺少: %s" % (missing or "无"),
        "pip install -r requirements.txt")

    # 3 配置文件
    from rag import config as cfgmod
    cfg = cfgmod.load()
    rec("Config", bool(cfg.get("_config_file")), "使用 %s" % cfg.get("_config_file"),
        "检查 config/config.yaml")
    cfg["_db_path"] = cfgmod.abspath(cfg, cfg["index"]["db"])
    cfg["_vectors_path"] = cfgmod.abspath(cfg, cfg["index"]["vectors"])
    cfg["_source_map_path"] = cfgmod.abspath(cfg, cfg["paths"]["source_map"])
    cfg["model"]["cache_dir"] = cfgmod.abspath(cfg, cfg["model"]["cache_dir"])

    # 4 数据库
    ok = os.path.isfile(cfg["_db_path"])
    rec("Index DB exists", ok, cfg["_db_path"], "确认 data/index/mvp.db 存在")
    if not ok:
        return summary()

    # 5 向量
    okv = os.path.isfile(cfg["_vectors_path"])
    rec("Vectors exist", okv, cfg["_vectors_path"], "确认 data/index/vectors.npy 存在")

    # 6 模型
    md = cfg["model"]["cache_dir"]
    nm = sum(len(f) for _r, _d, f in os.walk(md)) if os.path.isdir(md) else 0
    rec("Embedding model present", nm > 0, "%s (%d files)" % (md, nm),
        "放置 fastembed 模型缓存或改 config 的 model.cache_dir")

    # 7 数据库完整性 + FTS
    try:
        from rag import bm25
        con = bm25.connect(cfg["_db_path"])
        integ = con.execute("pragma integrity_check").fetchone()[0]
        n = con.execute("select count(*) from chunks").fetchone()[0]
        rec("SQLite integrity", integ == "ok", "integrity_check=%s, chunks=%d" % (integ, n), "重新拷贝 mvp.db")
        try:
            con.execute("select rowid from chunks_fts where chunks_fts match ? limit 1", ('"遗传算法"',)).fetchall()
            rec("BM25 (FTS5 trigram)", True, "chunks_fts 可查询")
        except Exception as e:
            rec("BM25 (FTS5 trigram)", False, str(e), "确认 mvp.db 含 FTS5 虚表")
        con.close()
    except Exception as e:
        rec("SQLite integrity", False, str(e))
        rec("BM25 (FTS5 trigram)", False, "跳过")

    # 8 向量与 chunk 对齐
    try:
        import numpy as np
        m = np.load(cfg["_vectors_path"], mmap_mode="r")
        con = bm25.connect(cfg["_db_path"])
        n = con.execute("select count(*) from chunks").fetchone()[0]
        con.close()
        rec("Vectors rows == chunks rows", m.shape[0] == n, "vectors=%d, chunks=%d" % (m.shape[0], n),
            "向量与库必须成对拷贝")
    except Exception as e:
        rec("Vectors rows == chunks rows", False, str(e))

    # 9 guard
    try:
        from rag import guard as g
        r = g.check()
        rec("Guard (Q-1 lexical)", r["ok"], "probe_expr=%s" % r["probe_expr"], "确认 src/rag/bm25.py 未被改回旧 terms()")
    except Exception as e:
        rec("Guard (Q-1 lexical)", False, str(e))

    # 10 端到端检索
    try:
        from rag import retrieve
        out = retrieve("遗传算法适合什么类型的数学建模问题", top_k=3)
        ok = len(out["results"]) > 0 and all("chunk_id" in r and "path" in r for r in out["results"])
        rec("Retrieval end-to-end", ok, "Top%d 返回，耗时 %.3fs" % (len(out["results"]), out["meta"]["latency_s"]),
            "检查模型/索引/配置三项")
    except Exception as e:
        rec("Retrieval end-to-end", False, str(e))
        traceback.print_exc()

    # 11 完整性
    man = os.path.join(ROOT, "manifests", "sha256.json")
    if os.path.isfile(man):
        import hashlib
        d = json.load(io.open(man, encoding="utf-8"))
        bad = []
        for rel, exp in d.get("files", {}).items():
            p = os.path.join(ROOT, rel)
            if not os.path.isfile(p):
                bad.append("missing:" + rel)
                continue
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            if h != exp:
                bad.append("changed:" + rel)
        rec("Integrity (sha256)", not bad, ("全部一致(%d 项)" % len(d.get("files", {}))) if not bad else "; ".join(bad[:5]),
            "运行 python scripts/make_manifest.py 重新生成（若确为有意修改）")
    else:
        rec("Integrity (sha256)", False, "manifests/sha256.json 不存在", "运行 python scripts/make_manifest.py")

    # 12 原文可定位（非阻塞）
    roots = (cfg.get("paths", {}) or {}).get("library_roots", {}) or {}
    configured = [k for k, v in roots.items() if v]
    rec("Original-file roots configured", bool(configured),
        "已配置 %s" % (configured or "无（索引可用，但打不开原文）"),
        "在 config/config.yaml 的 paths.library_roots 填本机语料目录")
    return summary()


def summary():
    fails = [r for r in RES if not r["ok"]]
    hard = [r for r in fails if r["item"] != "Original-file roots configured"]
    print()
    print("RAG STATUS: %s" % ("READY" if not hard else "NOT READY"))
    if hard:
        print("阻塞项：")
        for r in hard:
            print("  - %s：%s" % (r["item"], r["detail"]))
    if fails and not hard:
        print("提示（非阻塞）：%s" % "；".join(r["item"] for r in fails))
    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
