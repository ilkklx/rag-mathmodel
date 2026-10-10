# CHANGELOG

## v1.0.1 — 2026-10-10

- 当原切词全部短于 FTS5 trigram 下限时，按术语/ASCII 词起点二次切分，修复「怎么用时间序列预测」等问法的空关键词检索；已有有效词法查询沿用原分词。
- Python API 和 CLI 拒绝零、负数、非整数及超过候选池的 `top_k`，给出明确错误。
- 来源提示不再通过文件名中的「竞赛」认证官方身份；评阅/规范文件仅提示类别，来源仍须人工核验。
- 添加 6 项针对性回归检查；评测支持输出独立的新版本报告，并显式允许预期排序变化；保留原始快照和历史报告。
- Git 属性固定文本为 LF，模型缓存保留原始字节，避免 Windows 检出触发缓存长度或 SHA-256 警告。
- 当前 GT-50 中 49 道排序与旧快照一致，M10 的原空关键词检索被补救；现有标注下 DirectHit@5/10 和 MRR@10 保持原值。新结果仍有未标注条目，不宣称整体检索质量提高。

## v1.0.0 — 2026-09-13

首个可移植交付版本。相对原项目（`F:\competition\数学建模省赛\资源\11_RAG化改造方案\`）的差异：

### 新增（为可移植与 Agent 可调用而做）

- 统一 Python 接口 `from rag import retrieve`，返回结构固定（含 `path` / `chunk_id` / `source` 映射）；
- CLI `query.py`，支持 `--json` / `--top-k` / `--no-content`；
- `config/config.yaml` 集中配置，**全部相对资源包根目录解析**；
- `scripts/check.py` 环境自检（12 项）、`scripts/verify.py` 完整性校验、`scripts/eval_gt50.py` GT-50 验收、`scripts/test_retrieval.py` 五类冒烟测试；
- `manifests/`（file_manifest / sha256 / version）；
- `AGENT_GUIDE.md`（给 Agent 的调用与引用规则）、`README.md`、`QUICKSTART.md`。

### 变更

- 原 `14_BaselineV2/ask_mvp.py` 中的硬编码路径（`F:\...\rag_mvp`、`E:\fastembed_cache`）全部移除；
- 原 `p52_lexical.py` / `baseline_v2.py` 的检索逻辑**逐行等价**移植到 `src/rag/{bm25,vector_search,fusion,retrieve}.py`，未改任何算法与参数；
- 原 `p5_rewrite.py` 原样复制为 `src/rag/rewrite.py`（无路径依赖）。

### 携带

- 索引与向量：`data/index/mvp.db`（8,951 chunks）、`data/index/vectors.npy`；
- 模型：`models/fastembed`（bge-small-zh-v1.5，ONNX，约 91 MB，离线可用）；
- 评测：`data/ground_truth/{eval_set_v2.json, baseline_v2_snapshot.json, content_labels_v2.jsonl}`。

### 未完成（沿用原项目状态，未隐藏）

公式恢复、自动来源原文校验、语料补全（318 篇未判定／研赛辅库／乱码 43 chunk）、2 字词检索、聚合展示层、身份规则登记项 D-11 / D-1b、主索引双键重建。
