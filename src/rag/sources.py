# -*- coding: utf-8 -*-
"""路径映射：把索引里的原始绝对路径解析成「source_id + relative_path」，并可落到本地语料根。

设计目的：新机器没有原作者电脑上的 F:/E: 目录，但必须能回答“这条结果出自哪个库、哪篇文件”。
未配置 library_roots 时，resolved_path=null、exists=false —— 这是如实状态，不是错误。
"""
import io
import json
import os

UNVERIFIED_HINTS = ("07_2026赛题参考", "数学建模老哥", "未验证")


def load_map(cfg):
    p = cfg["_source_map_path"]
    if not os.path.isfile(p):
        return {"rules": [], "note": "source_map.json 缺失"}
    with io.open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def match_rule(rules, original_path):
    best = None
    for r in rules or []:
        pre = (r.get("original_prefix") or "").rstrip("\\")
        if original_path.lower().startswith(pre.lower()):
            if best is None or len(pre) > len(best.get("original_prefix", "")):
                best = r
    return best


def trust_of(path, source_id):
    p = (path or "")
    if any(h in p for h in UNVERIFIED_HINTS):
        return "未验证（低可信度）"
    # 文件名只提示资料类别，不能据此认证发布机构或官方身份。
    if "评阅要点" in p:
        return "评阅参考（来源需人工核验）"
    if "format2026" in p.lower():
        return "规范参考（来源需人工核验）"
    if source_id in ("ROOT1", "ROOT2", "ROOT3", "ROOT6"):
        return "一般（论文库）"
    return "待人工判断"


def resolve(cfg, original_path):
    sm = cfg["_source_map"]
    rules = sm.get("rules", []) if isinstance(sm, dict) else []
    rule = match_rule(rules, original_path or "")
    sid = rule["source_id"] if rule else None
    prefix = (rule.get("original_prefix") if rule else "") or ""
    rel = (original_path or "")[len(prefix):].lstrip("\\") if prefix else (original_path or "")
    roots = (cfg.get("paths", {}) or {}).get("library_roots", {}) or {}
    local_root = roots.get(sid) or roots.get("default")
    resolved = None
    exists = False
    if local_root and rel:
        cand = os.path.join(local_root, rel.replace("/", os.sep))
        resolved = cand
        exists = os.path.isfile(cand)
    return {"source_id": sid, "relative_path": rel, "original_path": original_path,
            "resolved_path": resolved, "exists": exists,
            "trust_hint": trust_of(original_path, sid)}
