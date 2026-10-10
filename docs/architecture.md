# 架构

## 一、总体

```text
调用方(Agent / 人 / CLI)
        │  retrieve(query, top_k)
        ▼
┌───────────────────────────────────────────────┐
│ src/rag/retrieve.py   统一入口与编排           │
│   ├─ rewrite.py        Scheme-B 查询改写       │
│   ├─ vector_search.py  向量召回（ONNX）        │
│   ├─ bm25.py           FTS5 trigram 召回       │
│   ├─ fusion.py         RRF 融合 (k=60)         │
│   ├─ sources.py        路径映射 / 可信度提示   │
│   ├─ guard.py          防呆自检                │
│   └─ config.py         配置与相对路径解析      │
└───────────────────────────────────────────────┘
        │ 数据
        ├─ data/index/mvp.db      chunks(8951) + chunks_fts(FTS5 trigram)
        ├─ data/index/vectors.npy 向量矩阵（与 chunks 行序一一对应）
        ├─ models/fastembed/      bge-small-zh-v1.5（ONNX，离线）
        └─ data/{metadata,ground_truth}/
```

## 二、模块职责

| 模块 | 职责 | 与原始项目的关系 |
|------|------|------------------|
| `config.py` | 读 `config/config.yaml`，把相对路径解析到资源包根目录 | 新写的（原来硬编码绝对路径） |
| `rewrite.py` | Scheme-B 分词；原词法为空时补救术语边界 | 基于 `14_BaselineV2/p5_rewrite.py`，v1.0.1 增加受限补救 |
| `bm25.py` | Q-1 修复的词法构造 + FTS5 查询 | **等价移植** `p52_lexical.py` |
| `vector_search.py` | fastembed 编码查询 + 与 `vectors.npy` 点积 | **等价移植** `ask_mvp.vec_search` |
| `fusion.py` | RRF（k=60） | **等价移植** `ask_mvp.rrf` |
| `sources.py` | 原始路径 → `source_id` + `relative_path`，可选落到本机语料根；来源提示仅作类别参考 | 新写的；v1.0.1 收紧官方身份提示 |
| `guard.py` | 断言词法表达式为 `"网格无关"`、不含伪词 | **等价移植** `baseline_v2.guard()` |
| `retrieve.py` | 编排 + 统一返回结构 | **等价移植** `baseline_v2.retrieve()` 并扩展返回字段 |

## 三、依赖方向

`retrieve` → {`rewrite`, `vector_search`, `bm25`, `fusion`, `sources`, `config`}
`guard` → `bm25`（仅做词法自检）
无循环依赖；`data/` 与 `models/` 只读，运行期不写任何文件（除 `manifests/` 由脚本生成）。

## 四、可移植性设计

1. **零绝对路径**：代码内不出现 `F:\` / `E:\`，全部经 `config.py` 的 `ROOT` 解析；
2. **配置外置**：索引位置、模型位置、语料根映射都写在 `config/config.yaml`；
3. **离线模型**：模型随包携带，`model.local_files_only: true`；
4. **路径映射**：`sources.py` 把索引里的原始路径折算成 `source_id + relative_path`，换机只需改 `library_roots`；
5. **完整性**：`manifests/sha256.json` 覆盖包内全部文件，`scripts/verify.py` 可校验。
