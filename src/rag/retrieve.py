# -*- coding: utf-8 -*-
"""统一检索入口：retrieve(query, top_k) —— 与 Baseline V2 完全同构。

链路：Scheme-B 改写 → 向量(深度 pool*2) ‖ BM25(深度 pool*2) → RRF(k=60) → 取 pool → 取 top_k
返回结构稳定，且每条结果都带 (path, chunk_id) 与 source 映射，可追溯。
"""
import time
import os
from numbers import Integral

from . import bm25, config as cfgmod, fusion, guard as guardmod, rewrite as rwmod
from . import sources as srcmod
from . import vector_search as vs

_STATE = {}


def _validate_top_k(value):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
        raise ValueError("top_k must be a positive integer")
    return int(value)


def _init(config_path=None):
    key = config_path or "__default__"
    if key in _STATE:
        return _STATE[key]
    cfg = cfgmod.load(config_path)
    cfg["_db_path"] = cfgmod.abspath(cfg, cfg["index"]["db"])
    cfg["_vectors_path"] = cfgmod.abspath(cfg, cfg["index"]["vectors"])
    cfg["_source_map_path"] = cfgmod.abspath(cfg, cfg["paths"]["source_map"])
    cfg["model"]["cache_dir"] = cfgmod.abspath(cfg, cfg["model"]["cache_dir"])
    cfg["_source_map"] = srcmod.load_map(cfg)
    con = bm25.connect(cfg["_db_path"])
    rows = con.execute("select id, path, chunk_id, section, year, problem from chunks").fetchall()
    by_id = {r["id"]: dict(r) for r in rows}
    cfg["_by_id"] = by_id
    cfg["_n_rows"] = len(by_id)
    cfg["_con"] = con
    _STATE[key] = cfg
    return cfg


def retrieve(query, top_k=None, config_path=None):
    """检索入口。返回 dict：{query, results[], meta{}}。"""
    if top_k is not None:
        top_k = _validate_top_k(top_k)
    t0 = time.time()
    cfg = _init(config_path)
    rc = cfg["retrieval"]
    topk = _validate_top_k(rc["topk"] if top_k is None else top_k)
    pool = int(rc["pool"])
    if topk > pool:
        raise ValueError("top_k must not exceed retrieval.pool (%d)" % pool)
    depth = pool * int(rc["recall_multiplier"])

    def filt(rid):
        return rid in cfg["_by_id"]

    rw = rwmod.rewrite(query, rc.get("rewrite_scheme", "B"))
    lex, emb = rw["bm25_query"], rw["emb_query"]
    if rw.get("fallback"):
        lex = emb = query

    vids, _sims = vs.search(cfg, emb, depth, filt)
    bids, binfo = bm25.search(cfg["_con"], lex, depth, filt)
    fused = fusion.rrf(bids, vids, k=int(rc["rrf_k"]))
    fused_pool = fused[:pool]
    top = fused_pool[:topk]

    results = []
    for rank, (rid, score) in enumerate(top, 1):
        m = cfg["_by_id"][rid]
        text = cfg["_con"].execute("select text from chunks where id=?", (rid,)).fetchone()["text"]
        s = srcmod.resolve(cfg, m["path"])
        results.append({
            "rank": rank,
            "score": round(float(score), 6),
            "path": m["path"],
            "chunk_id": m["chunk_id"],
            "title": os.path.basename(m["path"]),
            "year": m["year"],
            "problem": m["problem"],
            "section": m["section"],
            "content": text,
            "content_preview": text[:300],
            "source_type": "数学建模资料库",
            "retrieval_method": "RRF(vector+BM25)",
            "source": s,
        })
    return {
        "query": query,
        "results": results,
        "meta": {
            "package": cfg["package"],
            "baseline": "Baseline V2 + empty lexical query rescue (v1.0.1)",
            "rewrite": {"scheme": rc.get("rewrite_scheme", "B"), "lex_query": lex,
                        "emb_query": emb, "terms": rw["terms"], "fallback": rw.get("fallback", False)},
            "pool": pool, "depth_per_route": depth, "rrf_k": rc["rrf_k"], "top_k": topk,
            "bm25_match": binfo.get("match", ""), "bm25_kept": binfo.get("kept", []),
            "bm25_skipped": binfo.get("skipped", []),
            "n_vector": len(vids), "n_bm25": len(bids), "n_fused": len(fused),
            "config_file": cfg["_config_file"], "root": cfg["_root"],
            "latency_s": round(time.time() - t0, 4),
        },
    }
