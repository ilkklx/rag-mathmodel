# -*- coding: utf-8 -*-
"""BM25（SQLite FTS5 trigram）+ Q-1 修复的词法构造。

与 Baseline V2 一致：两字词不再补首字（旧版会造出 "一个一" 这类伪词）；
短于 3 字符的词元明确跳过并记录；全部被跳过时返回空表达式（调用方回退向量路径）。
"""
import re
import sqlite3

MIN_TRIGRAM = 3


def terms_fixed(q):
    kept, skipped = [], []
    for p in re.split(r"[\s,，。;；:：、/\\|()（）\[\]【】\"'!？?]+", q or ""):
        p = p.strip()
        if len(p) >= MIN_TRIGRAM:
            kept.append(p)
        elif p:
            skipped.append(p)
    return kept, skipped


def build_match(q):
    kept, skipped = terms_fixed(q)
    expr = " OR ".join('"%s"' % t.replace('"', "") for t in kept)
    return expr, kept, skipped


def search(conn, query, topn, filt):
    """返回 (ids, info)。info 含 match / kept / skipped，便于事后反查走的是哪套构造。"""
    expr, kept, skipped = build_match(query)
    if not expr:
        return [], {"match": "", "kept": kept, "skipped": skipped,
                    "reason": "无 >=3 字词元，回退向量路径"}
    rows = conn.execute(
        "select rowid from chunks_fts where chunks_fts match ? order by bm25(chunks_fts) limit ?",
        (expr, topn * 4)).fetchall()
    ids = []
    for (rid,) in rows:
        if filt(rid):
            ids.append(rid)
        if len(ids) >= topn:
            break
    return ids, {"match": expr, "kept": kept, "skipped": skipped, "reason": ""}


def connect(db_path, readonly=True):
    uri = "file:%s?mode=ro" % db_path.replace("\\", "/") if readonly else db_path
    con = sqlite3.connect(uri, uri=readonly)
    con.row_factory = sqlite3.Row
    return con
