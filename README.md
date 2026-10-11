# RAG-MathModel v1.0.2

**数学建模知识检索底座（可移植版）** —— 把历年国赛真题、获奖论文、评阅要点、算法资料做成一套**能检索、带出处**的本地检索系统。

> 本资源包整理为可移植的数学建模检索系统；资料位置由使用者自行配置。
> 检索采用 **Baseline V2 + 空词法查询补救**。v1.0.1 修复部分口语问法漏掉术语的问题；v1.0.2 移除个人绝对路径；原始冻结快照和评测记录保留，当前结果见 `docs/evaluation.md`。

v1.0.1 同时校验 `top_k` 参数、收紧来源提示，并固定 Git 检出的换行格式，避免 Windows 换行转换影响模型缓存和文件校验。详细变更见 `CHANGELOG.md`。

---

## 一、这是什么

- 一个**离线**检索系统：不联网、不调用大模型，只做检索与出处标注；
- 索引内含 **8,951 个知识块**（来自 373 篇材料的切块）；
- 支持按题意检索"方法 / 算法 / 公式相关材料 / 相似赛题 / 综合问题"；
- 每条结果都带 **`path` + `chunk_id`** 双键，可追溯到原文；
- 自带 **50 题 Ground Truth**，可自测召回质量。

## 二、怎么安装

```bash
python scripts/setup.py            # 检查 Python 与依赖（可加 --install 自动 pip 安装）
pip install -r requirements.txt    # 依赖：numpy / fastembed / onnxruntime / PyYAML
```

模型已随包携带（`models/fastembed`，bge-small-zh-v1.5，ONNX），**无需联网下载**。

## 三、怎么启动 / 怎么查询

最快的自检：

```bash
python scripts/check.py
```

命令行查询：

```bash
python query.py "遗传算法适合什么类型的数学建模问题" --top-k 10
python query.py "2018A 高温服装 边界条件" --top-k 5 --json      # Agent 首选：合法 JSON
```

`--top-k` 必须为正整数，且不超过配置中的 `retrieval.pool`（默认 50）；Python 接口用 `top_k=None` 采用配置默认值。

补丁回归检查和当前评测：

```bash
python -B scripts/test_targeted_fixes.py
python -B scripts/eval_gt50.py --allow-baseline-diff --output manifests/eval_v1_0_2_result.json
```

第二条命令会重写当前版本评测文件。原始 `eval_gt50_result.json` 是 v1.0.0 历史记录；省略 `--allow-baseline-diff` 时，评测仍要求结果与原始快照逐条一致。

Python 调用：

```python
import sys; sys.path.insert(0, "src")
from rag import retrieve

out = retrieve("什么是隐式差分格式的稳定性条件？", top_k=5)
for r in out["results"]:
    print(r["rank"], r["title"], r["chunk_id"], r["source"]["resolved_path"])
```

## 四、换一台机器怎么用

1. 把整个 `rag\` 放到任意目录（例如 `D:/rag`）；
2. 将 `config/config.example.yaml` 复制为 `config/config.local.yaml`，再编辑其中 的 `paths.library_roots`，把 6 个 `ROOT*` 指向**你本机的语料目录**；
   - 不配置也能检索，只是 `source.resolved_path` 为 `null`、`exists=false`（打不开原文）；
3. 跑 `python scripts/check.py`，看到 `RAG STATUS: READY` 即可。

## 五、目录导航

| 目录 | 内容 |
|------|------|
| `src/rag/` | 检索实现（config / rewrite / bm25 / vector_search / fusion / guard / sources / retrieve） |
| `data/index/` | 索引 `mvp.db` 与向量 `vectors.npy`（必须成对） |
| `data/ground_truth/` | 50 题 GT、冻结快照、内容标签 |
| `data/metadata/` | `source_map.json`（路径映射规则）、`index_meta.json` |
| `models/fastembed/` | 离线 embedding 模型 |
| `scripts/` | check / verify / test_retrieval / eval_gt50 / make_manifest / setup |
| `docs/` | 架构、检索、评测、已知问题、研究笔记 |
| `examples/` | 最小调用示例 |
| `manifests/` | 文件清单、sha256、版本、GT-50 实测结果 |

## 六、给 AI Agent

**请直接读 [`AGENT_GUIDE.md`](AGENT_GUIDE.md)** —— 里面有调用方式、返回字段含义、引用规则、可信度分级与"检索不到怎么办"。

## 七、已知问题（详见 `docs/known_issues.md`）

- **公式恢复未完成**：论文公式多为图片式排版，检索到的是周边文字，公式本体可能缺失；
- **Top-10 不保证全部是直接答案**（当前内容级 DirectHit 见 `manifests/eval_v1_0_2_result.json`，未标注结果需补核）；
- **低可信度材料存在**：`07_2026赛题参考（低可信度）` 等材料未经验证，不得当权威引用；
- **原文本包不携带**：本包只含索引；能否打开原文取决于 `library_roots` 是否指向你本机的语料；
- 部分验收仍待外部复验（见 `DELIVERY_REPORT.md`）。

路径示例统一使用 D:/rag，使用者自行替换。config/config.local.yaml 是个人配置，不进入 Git 或文件校验清单。公开索引和引用使用 ROOT1～ROOT6 的逻辑来源编号，不保存作者电脑的绝对路径。
