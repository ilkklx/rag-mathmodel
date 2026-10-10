# DELIVERY_REPORT —— RAG-MathModel v1.0.0

> 历史报告：以下为 v1.0.0 的原始交付记录，指标和包体积不代表 v1.0.1。当前补丁及评测见 CHANGELOG.md、docs/evaluation.md 和 manifests/eval_v1_0_1_result.json。

> 给项目负责人看的交付报告。所有数字均为脚本实测，可在 `manifests/` 复算。
> 构建时间：2026-09-13｜包体积：**167.2 MB / 48 个文件**（`make_manifest.py` 实测）

---

## 1. 原项目是什么

`F:\competition\数学建模省赛\资源\11_RAG化改造方案\` —— 为 2026 全国大学生数学建模竞赛（本科组）建设的**数学建模知识检索底座**（RAG）。
它经历了 Phase 0–6、五题失败归因诊断（四轮）、任务一核验、任务二分层记录，最终封版为 **Baseline V2**（Scheme-B 改写 + Q-1 修复 + 向量/BM25/RRF，50/50 验证）。

**但原项目是"工程现场"**：代码里写死了 `F:\...`、`E:\fastembed_cache` 等本机路径，没有对外接口说明，别人拿到也跑不起来。

## 2. 本次做了什么

把上述成果**产品化**为可移植资源包：

1. **审计**：区分"运行必需 / 实验记录 / 历史版本"，找出全部硬编码路径与未记录依赖；
2. **重构**：把检索逻辑等价移植为 `src/rag/` 包，**零绝对路径**，配置外置；
3. **接口**：统一 Python API + CLI（`--json`）+ 稳定返回结构（含出处与 source 映射）；
4. **可移植**：模型随包携带（离线）、路径映射机制（`source_id + relative_path`）；
5. **自检与校验**：`check.py`（12 项）、`verify.py`（sha256）、`eval_gt50.py`（50 题验收）；
6. **文档**：README / QUICKSTART / **AGENT_GUIDE** / docs×5 / 示例 / 清单；
7. **验证**：环境自检、五类冒烟、GT-50 重跑、路径测试、**独立目录测试**（全部实跑）。

## 3. 打包了什么

### A. 必须携带（运行依赖）

| 文件 | 说明 | 大小 |
|------|------|------|
| `data/index/mvp.db` | 索引：chunks(8,951) + FTS5 trigram | 58.1 MB |
| `data/index/vectors.npy` | 向量矩阵（8,951 × 512，与 chunks 行序对应） | 17.5 MB |
| `models/fastembed/` | bge-small-zh-v1.5（ONNX，离线） | 约 91 MB |
| `src/rag/*.py` | 检索实现（8 个模块） | < 60 KB |
| `config/` | 配置与模板 | < 5 KB |

### B. 建议携带（评测与文档）

`data/ground_truth/`（50 题 GT、冻结快照、内容标签）、`scripts/`、`docs/`、`manifests/`、`README/QUICKSTART/AGENT_GUIDE/CHANGELOG/VERSION`、`examples/`。

### C. 不携带（已排除）

原始语料（8.75 GB / 21,433 文件）、全部 PDF、Phase 1–6 的实验中间产物、历史交付包、`__pycache__`、临时文件。

> **原始 PDF 未随包**：是否携带的判断依据是"体积 vs 必要性"——8.75 GB 不可接受，而索引已保留 `path + relative_path`，配合 `config.yaml` 的 `library_roots` 即可定位你自己的语料副本。

## 4. 删除了什么

- 原 `ask_mvp.py` 中的 `RAGDIR/DB/VEC/FE_CACHE` 等**硬编码绝对路径**；
- `baseline_v2.py` 里对原目录的 `sys.path` 注入与模块级全表加载（改为按需）；
- 与本包运行无关的实验脚本、历史版本、中间产物（**未删除原件**，只在打包范围上排除）。

## 5. 修改了什么

| 原文件 | 新位置 | 改动 |
|--------|--------|------|
| `14_BaselineV2/p5_rewrite.py` | `src/rag/rewrite.py` | **原样复制**，无改动 |
| `14_BaselineV2/p52_lexical.py` | `src/rag/bm25.py` | 等价移植，仅去掉对 `ask_mvp` 的依赖、连接改为只读 |
| `14_BaselineV2/ask_mvp.py`（vec/rrf） | `src/rag/vector_search.py` + `fusion.py` | 等价移植，参数从 config 读取 |
| `14_BaselineV2/baseline_v2.py` | `src/rag/retrieve.py` | 编排逻辑一致，扩展返回字段（source 映射、meta） |

**算法、参数、链路顺序、深度（pool=50 / 深度 100 / RRF k=60 / topk=10）一律未改。**

## 6. 为什么这么修改

| 改动 | 原因 |
|------|------|
| 路径外置到 config | 换机器只改一处；代码可复用 |
| 模型随包 + `local_files_only` | 目标环境可能无网络 |
| 新增 `sources.py` 路径映射 | 否则换机后"检索到了却打不开原文"，且无法判断材料出处 |
| 统一返回结构 | 让 Agent 不必读源码就能用；`path+chunk_id` 是引用的最小凭据 |
| 保留三份 Ground Truth | 让验收可复算（一致率 / DirectHit / legacy 三种口径） |

## 7. 如何调用

```python
import sys; sys.path.insert(0, r"E:\数学建模资源库\rag\src")
from rag import retrieve
out = retrieve("遗传算法适合什么类型的数学建模问题", top_k=10)
print(out["results"][0]["chunk_id"], out["results"][0]["path"])
```

```bash
cd E:\数学建模资源库\rag
python query.py "隐式差分格式的稳定性" --top-k 10 --json
```

## 8. 如何验证

```bash
python scripts/check.py          # 12 项环境自检 → RAG STATUS
python scripts/test_retrieval.py # 五类冒烟
python scripts/eval_gt50.py      # 50 题 GT，与冻结快照逐条比对
python scripts/test_paths.py     # 原文能否定位
python scripts/verify.py         # 文件完整性（sha256）
```

## 9. 测试结果（全部实跑）

| 测试 | 结果 | 依据 |
|------|------|------|
| Test 1 环境检查 | **PASS**（12/12，`RAG STATUS: READY`） | `scripts/check.py` 输出 |
| Test 2 基础检索（五类） | **PASS**（5/5，均返回且带 path+chunk_id） | `scripts/test_retrieval.py` 输出 |
| Test 3 GT-50 | **PASS**：一致率 **50/50**；DirectHit@5 **0.34**、@10 **0.40**、MRR@10 **0.2509**、legacy Hit@5/@10 **0.90/0.90** —— 与冻结基线**逐项一致** | `manifests/eval_gt50_result.json` |
| Test 4 路径测试 | **PASS**（30/30 可定位到本机文件） | `scripts/test_paths.py` 输出 |
| Test 5 独立目录 | **PASS**（复制到 `C:\...\rag_portable_test\` 后 check 全过；且**断开 `library_roots` 后仍能检索**，`resolved_path=null / exists=false`，`relative_path` 保留） | 实跑记录 |
| 完整性校验 | **PASS**（sha256 全一致） | `scripts/verify.py` |

## 10. 当前性能（脚本实测，非手写）

| 指标 | 值 |
|------|-----|
| 索引规模 | 8,951 chunks ｜ 373 个不同 path |
| 50 题总耗时 | 2.72 s |
| 平均每问 | 0.054 s |
| 最大单问 | 2.14 s（首次含模型加载） |
| 内容级 DirectHit@5 / @10 | 0.34 / 0.40 |
| legacy Hit@5 / @10 | 0.90 / 0.90 |
| 与冻结快照一致率 | 50/50 = 1.00 |

## 11. 已知问题

见 `docs/known_issues.md`（10 条）。要点：

1. **公式恢复未完成**——公式本体可能缺失；
2. **Top-10 不保证全部直接可用**（DirectHit@10 = 0.40）；
3. 自动来源原文校验未实现；
4. 318 篇论文归属未判定、研赛辅库未建、乱码 43 chunk 未处理；
5. **低可信度材料存在**（`07_2026赛题参考`、`数学建模老哥`），不得当权威引用；
6. 原始 PDF **不随包**，换机需自行配置 `library_roots`；
7. `chunk_id` 存在跨路径重名，**引用必须带 path**。

## 12. 尚未解决的问题

| 项 | 状态 | 说明 |
|----|------|------|
| 公式恢复（MinerU / PP-StructureV3） | **未做** | 路线已定，安装路径待拍板 |
| 自动来源原文校验 | **未做** | 原项目记录为后续工程项 |
| 语料补全 | **未做** | 318 篇未判定 / 研赛辅库 / 乱码 |
| 2 字词检索 | **未做** | Q-1 只缓解 |
| 聚合展示层 | **未启用** | 结论：不增加唯一 DIRECT 赛题 |
| 身份规则 D-11 / D-1b | **仅登记** | 未实施 |
| 外部复验 | **待复核** | 第四轮诊断包、任务二分层链条——执行方不得自称通过 |

## 13. 后续建议

1. 先用本包做"**检索 + 人工筛**"（不要默认 Top-1 即答案）；
2. 若需要公式级检索，先做**定点公式恢复**（只针对高频引用页），不要全量重跑 OCR；
3. 若要把本包接入 Agent，**只需读 `AGENT_GUIDE.md`**，不要改检索参数；
4. 任何参数改动都会使 `docs/evaluation.md` 的性能表失效，需重跑 `eval_gt50.py`；
5. 要升级检索算法时**不要覆盖 v1.0.0**，升版本号另建目录。

---

## 附录 A：最终交付检查表（18 项）

| # | 检查项 | 结果 | 说明 |
|---|--------|:----:|------|
| 1 | 是否可以脱离原项目目录运行 | **PASS** | Test 5 独立目录实跑 |
| 2 | 是否删除了原电脑绝对路径依赖 | **PASS** | 代码零绝对路径；机器相关项集中在 `config.yaml`（设计如此） |
| 3 | 是否有标准 Python API | **PASS** | `from rag import retrieve` |
| 4 | 是否有 CLI | **PASS** | `python query.py "..."` |
| 5 | 是否有 JSON 输出 | **PASS** | `--json`，`json.loads` 可直接解析 |
| 6 | 是否有 Agent 调用说明 | **PASS** | `AGENT_GUIDE.md`（10 节，含引用规则与四级可信度） |
| 7 | 是否有环境检查 | **PASS** | `scripts/check.py`（12 项） |
| 8 | 是否有完整性校验 | **PASS** | `scripts/verify.py` + `manifests/sha256.json` |
| 9 | 是否有版本号 | **PASS** | `VERSION` + `manifests/version.json` |
| 10 | 是否有 Ground Truth | **PASS** | 50 题 GT + 冻结快照 + 内容标签 |
| 11 | 是否重新运行了关键测试 | **PASS** | check / test_retrieval / eval_gt50 / test_paths / 独立目录 |
| 12 | 是否验证了 path + chunk_id | **PASS** | 50/50 快照一致（含 path+chunk_id）；30/30 可定位 |
| 13 | 是否存在无法访问的原始文件 | **PARTIAL** | 本机可定位；**原始 PDF 不随包**，换机需配置 `library_roots`，未配置时 `exists=false`（如实标注，不伪装） |
| 14 | 是否明确记录所有已知问题 | **PASS** | `docs/known_issues.md`（10 条） |
| 15 | 是否明确区分已验证与未验证结论 | **PASS** | 三口径分列（`docs/evaluation.md`）；四级可信度（`AGENT_GUIDE.md`） |
| 16 | 是否能够让另一个 Agent 直接接手 | **PASS** | `AGENT_GUIDE.md` + `examples/` + `check.py` |
| 17 | 是否生成最终 ZIP | **PASS** | `E:\数学建模资源库\RAG-MathModel-v1.0.0.zip` |
| 18 | 公式级检索是否可用 | **FAIL（已知）** | 公式恢复未完成，已在 README / AGENT_GUIDE / known_issues 三处标注 |

---

## 附录 B：目录树

```text
E:\数学建模资源库\rag\
├── README.md / QUICKSTART.md / AGENT_GUIDE.md / CHANGELOG.md / DELIVERY_REPORT.md / VERSION / requirements.txt
├── query.py
├── config\        config.yaml（本机） / config.example.yaml（模板）
├── src\rag\       __init__.py config.py rewrite.py bm25.py vector_search.py fusion.py sources.py guard.py retrieve.py
├── data\
│   ├── index\          mvp.db / vectors.npy
│   ├── ground_truth\   eval_set_v2.json / baseline_v2_snapshot.json / content_labels_v2.jsonl
│   └── metadata\       source_map.json / index_meta.json
├── models\fastembed\
├── scripts\       check.py verify.py test_retrieval.py test_paths.py eval_gt50.py make_manifest.py setup.py
├── docs\          architecture.md retrieval.md evaluation.md known_issues.md research_notes.md
├── examples\      example_agent_call.py example_query.py
└── manifests\     file_manifest.json sha256.json version.json eval_gt50_result.json
```
