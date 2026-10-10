#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""GT-50 验收：在本资源包里重跑 50 题，与冻结快照逐条比对，并复算内容级/legacy 指标。"""
import hashlib
import argparse
import io
import json
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from rag import retrieve  # noqa: E402

GT = os.path.join(ROOT, "data", "ground_truth", "eval_set_v2.json")
SNAP = os.path.join(ROOT, "data", "ground_truth", "baseline_v2_snapshot.json")
LAB = os.path.join(ROOT, "data", "ground_truth", "content_labels_v2.jsonl")
OUTP = os.path.join(ROOT, "manifests", "eval_gt50_result.json")


def th(t):
    return hashlib.sha1("".join((t or "").split()).encode("utf-8")).hexdigest()[:16]


def legacy_relevant(item, r):
    hits = [s for s in (item.get("primary_sources") or []) if s in r["path"]]
    hits += [s for s in (item.get("secondary_sources") or []) if s in r["path"]]
    if hits:
        return True
    kw = item.get("relevant_knowledge") or []
    n = sum(1 for k in kw if k and k in (r.get("content") or ""))
    return n >= int(item.get("min_hits") or 2)


def main():
    parser = argparse.ArgumentParser(description="GT-50 evaluation against the original snapshot")
    parser.add_argument("--output", default=OUTP, help="Output JSON path; keep historical reports separate")
    parser.add_argument("--allow-baseline-diff", action="store_true",
                        help="Report intentional ranking changes without requiring exact snapshot equality")
    args = parser.parse_args()
    items = json.load(io.open(GT, encoding="utf-8"))["items"]
    snap = json.load(io.open(SNAP, encoding="utf-8"))["snapshot"]
    labels = {}
    for line in io.open(LAB, encoding="utf-8"):
        e = json.loads(line)
        labels[(e["question_id"], e["text_hash"])] = e.get("label_final")

    same, diff, lat = 0, [], []
    h5 = h10 = 0
    mrr = 0.0
    lh5 = lh10 = 0
    cov_hit = cov_all = 0
    perq = {}
    t_all = time.time()
    for it in items:
        qid, q = it["id"], it["question"]
        t0 = time.time()
        out = retrieve(q, top_k=10)
        lat.append(time.time() - t0)
        got = [(r["path"], r["chunk_id"]) for r in out["results"]]
        exp = [(t["path"], t["chunk_id"]) for t in snap[qid]["top"]]
        same += 1 if got == exp else 0
        if got != exp:
            i = next((k for k, (a, b) in enumerate(zip(got, exp)) if a != b),
                     min(len(got), len(exp)))
            diff.append({"id": qid, "first_diff_rank": i + 1,
                         "got": got[i][1] if i < len(got) else None,
                         "exp": exp[i][1] if i < len(exp) else None})
        first = 0
        for r in out["results"]:
            lab = labels.get((qid, th(r.get("content"))))
            cov_all += 1
            cov_hit += 1 if lab else 0
            if lab == "DIRECT" and not first:
                first = r["rank"]
        if first and first <= 5:
            h5 += 1
        if first:
            h10 += 1
            mrr += 1.0 / first
        lh5 += 1 if any(legacy_relevant(it, r) for r in out["results"][:5]) else 0
        lh10 += 1 if any(legacy_relevant(it, r) for r in out["results"]) else 0
        perq[qid] = {"category": it["category"], "identical": got == exp, "first_direct": first}

    n = len(items)
    res = {
        "生成时间": time.strftime("%Y-%m-%d %H:%M:%S"),
        "题数": n,
        "一致率_vs冻结快照": "%d/%d" % (same, n),
        "一致率数值": round(same / float(n), 4),
        "DirectHit@5": round(h5 / float(n), 4),
        "DirectHit@10": round(h10 / float(n), 4),
        "MRR@10": round(mrr / float(n), 4),
        "legacyHit@5_重算": round(lh5 / float(n), 4),
        "legacyHit@10_重算": round(lh10 / float(n), 4),
        "内容标签覆盖率": "%d/%d" % (cov_hit, cov_all),
        "未标注结果数": cov_all - cov_hit,
        "指标说明": "未标注结果按非 DIRECT 处理；排序变化后需补标，不能据此宣称完整质量提升。",
        "耗时_s": {"总": round(time.time() - t_all, 2),
                   "平均每问": round(sum(lat) / len(lat), 4), "最大": round(max(lat), 4)},
        "不一致明细": diff,
        "逐题": perq,
    }
    io.open(args.output, "w", encoding="utf-8", newline="\n").write(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    brief = {k: v for k, v in res.items() if k != "逐题"}
    print(json.dumps(brief, ensure_ascii=False, indent=1))
    print("\n结果已写入 %s" % args.output)
    return 0 if same == n or args.allow_baseline_diff else 1


if __name__ == "__main__":
    sys.exit(main())
