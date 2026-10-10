# 检索链路

v1.0.1 沿用 Baseline V2 的两路召回、深度和 RRF 参数；仅在原词元全部短于 3 字符时，重新识别被未知片段跨过的术语或 ASCII 词起点。例如「怎么用时间序列预测」可保留「时间序列」，恢复 BM25 召回。已有有效词法查询仍使用原分词。

## 一、为什么是这套

原项目做过对照实验，结论已登记为 **Baseline V2**：

| 组成 | 实现 | 为什么 |
|------|------|--------|
| 查询改写 | Scheme-B：规范化 + 术语最长匹配切分 | 让 BM25 从"整句短语"变成"多词元 OR"，实测 Hit@5 +6pp / Hit@10 +4pp / MRR +0.109 |
| 词法构造 | Q-1 修复：**不造伪词**、<3 字词元显式跳过 | 修复 FTS5 trigram 对 2 字词的盲区（旧版会给 "一个" 补成 "一个一"） |
| 向量 | bge-small-zh-v1.5（ONNX） | 中文语义召回，弥补纯关键词 |
| 融合 | RRF，k=60 | 两路名次融合，不需要分数可比 |
| 深度 | 每路 `pool*2 = 100` → RRF 取 50 → 输出 10 | 与冻结实验一致 |

**Scheme-A（额外做同义词扩展）经消融证明零额外收益，故未采用。**

## 二、一次调用的完整过程

```text
query
 1) rewrite(query,"B") → normalized / terms / bm25_query / emb_query / fallback
 2) vector_search(emb_query, depth=100) → vids（按余弦相似度降序）
 3) bm25_search(bm25_query, depth=100)  → bids（FTS5 bm25() 排序）
 4) rrf(bids, vids, k=60)               → 全序融合表
 5) 截断：取融合前 50 → 再取前 top_k
 6) 每条补充：path / chunk_id / section / year / problem / content / source 映射
```

## 三、默认参数（`config/config.yaml`）

| 参数 | 值 | 含义 |
|------|-----|------|
| `rewrite_scheme` | `B` | 只用 Scheme-B |
| `pool` | 50 | 融合后保留的候选数 |
| `recall_multiplier` | 2 | 每路召回深度 = pool × 2 = 100 |
| `topk` | 10 | 默认输出条数 |
| `rrf_k` | 60 | RRF 平滑常数 |

## 四、常见现象的解释

| 现象 | 原因 |
|------|------|
| `bm25_match` 为空 | 查询里没有 ≥3 字的词元（trigram 限制），此时**自动回退纯向量**，`rewrite.fallback` 可能为 true |
| 某条材料"明明在库里却没进 Top-10" | 它在两条召回路的深度 100 内可能都没出现——这时要看 `meta.n_vector` / `n_bm25`，**不能直接说"库里没有"** |
| 融合把低名次材料拉上来 | RRF 的正常行为：两路都进榜的材料会被显著提升（实测有"向量第 93 + BM25 第 35 → 融合第 5"的案例） |
| 分数很小（如 0.016） | RRF 是 `Σ 1/(k+rank)`，**不是概率**，不要当相似度百分比 |

## 五、与原始项目的一致性

原项目用 `verify_baseline_v2.py` 在 50 题上重跑，与已验收结果 **50/50 完全一致** 后才封版。
本包用 `scripts/eval_gt50.py` 做同样的事，比对对象是随包的 `data/ground_truth/baseline_v2_snapshot.json`。

上述 50/50 是 v1.0.0 移植验收结果。v1.0.1 的 M10 启用了原先为空的词法召回，因此 49/50 排序一致；原始快照保持不变，当前报告单独存于 `manifests/eval_v1_0_1_result.json`。评测细节见 `evaluation.md`。
