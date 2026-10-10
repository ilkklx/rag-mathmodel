# -*- coding: utf-8 -*-
"""RRF 融合（与 Baseline V2 完全一致：k=60，先按融合分排序再截断）。"""


def rrf(list_a, list_b, k=60):
    score = {}
    for lst in (list_a, list_b):
        for rank, rid in enumerate(lst):
            score[rid] = score.get(rid, 0.0) + 1.0 / (k + rank + 1)
    return sorted(score.items(), key=lambda kv: -kv[1])
