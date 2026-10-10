# 项目总结 · RAG-MathModel 数学建模知识检索底座（rag-mathmodel）

> 本文档是仓库的**自包含项目说明**：目标让任何读者（或 AI）只读这一篇，就能完整了解这个系统是什么、算法细节、数据规模、怎么跑、有什么坑。关键结论标注来源文件。
> 撰写时间：2026-10-10。基于对仓库全部文件的通读核对（含 verify.py 实跑复核）。
> 注：本仓库自带一份完整的 README.md（作者版），本文是面向"快速理解全貌"的总结版。

---

## 1. 一句话定位

**RAG-MathModel v1.0.0**——数学建模知识检索底座：把历年国赛真题、获奖论文、官方评阅要点、算法资料做成一套**离线、不调用大模型、只做检索与出处标注**的本地检索系统，返回"带 `path` + `chunk_id` 的原文片段"，供人或 AI Agent 引用（README.md、AGENT_GUIDE.md）。

## 2. 技术栈

| 项 | 说明 | 证据 |
|---|---|---|
| 语言/环境 | Python 3.9+（实测 3.11.9） | QUICKSTART.md |
| 依赖 | numpy、fastembed、onnxruntime、PyYAML、pillow | requirements.txt |
| 向量模型 | BAAI/bge-small-zh-v1.5（ONNX，约 94.8MB，4 层 BERT、hidden 512），fastembed 加载，`local_files_only: true` 纯离线 | models/fastembed/、config/config.yaml |
| 词法检索 | SQLite FTS5 虚表，`tokenize='trigram'`，`bm25()` 排序 | data/index/mvp.db（只读核验） |
| 融合 | RRF（Reciprocal Rank Fusion），k = 60 | src/rag/fusion.py |
| 算法代号 | Baseline V2 = Scheme-B 查询改写 + Q-1 词法修复 + 向量/BM25/RRF 融合 | VERSION、DELIVERY_REPORT.md |

## 3. 检索全链路（src/rag/retrieve.py 编排）

1. **查询改写（rewrite.py，Scheme-B）**：全角转半角、标点归一 → 按疑问词表去除疑问词 → 用约 100 词术语词典（LEXICON）做最长匹配切分，连续 ASCII 字母数字整体保留，未命中取 2 字窗口。（Scheme-A 的同义词扩展经消融实验证明零收益，未采用，见 docs/retrieval.md）；
2. **双路召回（深度 = pool×2 = 100）**：
   - 向量路：查询编码后与 `data/index/vectors.npy`（8,951 × 512，已 L2 归一化）点积取前 100；
   - BM25 路：**Q-1 修复**——词元短于 3 字符显式跳过（trigram 盲区），词元组装为 `"..." OR "..."` 的 FTS5 表达式；词法为空时回退纯向量（bm25.py、guard.py）；
3. **融合（fusion.py）**：RRF `Σ 1/(k+rank+1)`，k=60，先排序再截断；融合前 50（pool）→ top_k（默认 10）；
4. **出处标注（sources.py）**：每条结果附 path / chunk_id / section / year / problem / content + source 映射（source_id、relative_path、original_path、resolved_path、exists、**四级可信度 trust_hint**）；meta 输出 bm25_match / n_vector / n_bm25 / latency_s 等排查字段。

## 4. 索引规模与数据来源

- 索引内含 **8,951 个知识块 / 373 篇材料**（README 与 mvp.db 实查一致）；切块按官方论文章节（摘要/问题重述/…/附录）而非字数硬切；
- 词法/向量两大资产：`data/index/mvp.db`（约 60.9MB，chunks + FTS5）、`data/index/vectors.npy`（18.3MB）；
- 语料来源（docs/research_notes.md）：原项目扫描 21,433 文件 / 5,346 篇 PDF；全库切出 17,231 块，本交付包取其中 8,951 块；
- **Ground Truth 50 题**：建模方法/算法/公式/相似赛题/综合各 10 题（data/ground_truth/eval_set_v2.json）。

## 5. 目录结构

```
├── README.md / QUICKSTART.md / AGENT_GUIDE.md / DELIVERY_REPORT.md / CHANGELOG.md / VERSION
├── query.py                 # 命令行查询入口（--json 供 Agent 调用）
├── requirements.txt
├── src/rag/                 # 9 个模块：retrieve / rewrite / bm25 / vector_search / fusion / guard / sources / config / __init__
├── data/
│   ├── index/               # mvp.db + vectors.npy（必须成对使用）
│   ├── ground_truth/        # 50 题 GT + 冻结快照 + 内容标签
│   └── metadata/            # source_map / index_meta
├── scripts/                 # check（自检）/ verify（sha256 校验）/ eval_gt50 / test_retrieval / test_paths / setup / make_manifest
├── docs/                    # architecture / retrieval / evaluation / known_issues / research_notes
├── manifests/               # version / file_manifest（49 文件全量哈希）/ sha256 / eval 结果
└── models/fastembed/        # 随包携带的 ONNX 模型（无需联网下载）
```

## 6. 如何运行

```bash
python scripts/setup.py            # 环境自检（--install 可自动安装依赖）
pip install -r requirements.txt    # numpy / fastembed / onnxruntime / PyYAML
python scripts/check.py            # 期望输出 RAG STATUS: READY
python query.py "遗传算法适合什么类型的数学建模问题" --top-k 10
python query.py "2018A 高温服装 边界条件" --top-k 5 --json    # Agent 首选
```

Python API：`from rag import retrieve`。换机只需改 `config/config.yaml` 的 `library_roots`（原文定位用）。本仓库 verify.py 已实跑复核：**49/49 文件哈希一致 PASS**。

## 7. 评测方法与结果（manifests/eval_gt50_result.json）

- 三口径分开陈述（docs/evaluation.md）：legacy 文件级 Hit、内容级 DirectHit/MRR、历史 Phase 6 槽位口径（不适用）；
- 实测：**一致率 50/50；DirectHit@5 = 0.34、@10 = 0.40；MRR@10 = 0.2509；legacy Hit@5 = Hit@10 = 0.90；标签覆盖 486/500；50 题总耗时 2.72 s**（平均 0.054 s/题）。

## 8. 已知问题（docs/known_issues.md 等，10 条要点）

- **chunk_id 跨路径碰撞**：8,951 块中唯一 chunk_id 仅 6,817（碰撞 2,134）→ **引用必须 (path, chunk_id) 双键**；
- DirectHit@10 偏低；公式图片版式本体缺失；无自动引文校验；318 篇归属未判定；43 个 chunk 乱码（3 文件）；
- 低可信度材料（标"赛题参考""数学建模老哥"）不得当权威引用；
- 原文不随包（只存索引与出处信息）。

## 9. 打包与公开说明

- **无任何密钥**（全量 grep api_key/secret/sk-/token 均为误报）；
- 配置与快照中保留了打包机器的本地路径（如 `E:\数学建模资源库\...`，见 config/config.yaml、source_map.json、baseline 快照）——仅为离线溯源设计，不含个人信息；
- 文档与实物小出入：DELIVERY_REPORT 称"48 个文件"（实为 49）、称 check.py"12 项"（实为 13 条检查）；`index_meta.json` 的 `vectors_rows` 为 null（未回填，非损坏）；
- **本包不含建库/建索引脚本**：可复现"检索"，不可复现"从原始语料建库"（流程仅存于 research_notes.md 文字描述）。

## 10. 存疑点

- BM25 的 k1/b 参数：项目未显式设置，实际使用 FTS5 内建默认权重（无项目内证据）；
- 内容标签由 GLM-4-Flash AI 初审 + agent 终审生成（reviewer 字段），"人工逐条核对"的表述与实现有出入；
- 486/500 中 14 个无标签槽位按"非 DIRECT"口径处理（设计口径，非缺陷）。
