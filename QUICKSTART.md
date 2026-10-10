# QUICKSTART（5 分钟跑通）

## 0. 前置

- Windows + Python 3.9 以上（实测 3.11.9）
- 依赖：`numpy`、`fastembed`、`onnxruntime`、`PyYAML`（`pip install -r requirements.txt`）

## 1. 自检（约 30 秒，首次会加载模型）

```bash
cd E:\数学建模资源库\rag
python scripts/check.py
```

期望结尾：

```text
RAG STATUS: READY
```

若出现 `[FAIL]`，按其 `Fix:` 提示处理；常见两种：

- **模型缺失** → 确认 `models/fastembed/` 存在（约 91 MB / 9 个文件），或改 `config/config.yaml` 的 `model.cache_dir`；
- **原文打不开**（仅提示、不阻塞）→ 在 `config.yaml` 的 `paths.library_roots` 填本机语料目录。

## 2. 查一条

```bash
python query.py "遗传算法适合什么类型的数学建模问题" --top-k 5
```

输出里每条都带 `出处: <文件名>#<chunk>` 与 `原文: <本机路径或"未配置">`。

## 3. 给 Agent 用（JSON）

```bash
python query.py "隐式差分格式的稳定性" --top-k 10 --json
```

或 Python：

```python
import sys; sys.path.insert(0, "src")
from rag import retrieve
out = retrieve("隐式差分格式的稳定性", top_k=10)
print(out["results"][0]["chunk_id"], out["results"][0]["source"]["resolved_path"])
```

## 4. 跑验收（约 1–2 分钟）

```bash
python scripts/test_retrieval.py     # 五类冒烟
python scripts/eval_gt50.py          # 50 题 GT，与冻结快照逐条比对
python scripts/verify.py             # 文件完整性（对照 manifests/sha256.json）
```

## 5. 出问题先看这里

| 现象 | 原因 | 处理 |
|------|------|------|
| `ModuleNotFoundError: rag` | 没把 `src` 加进 `sys.path` | 用 `query.py`，或 `sys.path.insert(0, "<包根>/src")` |
| 模型下载/联网卡住 | `local_files_only: false` | 改回 `true`（模型已在包内） |
| `原文: （未配置 library_roots…）` | 未配置语料根 | 编辑 `config/config.yaml` |
| 结果里 `section`/`year` 为空 | 该 chunk 元数据缺失 | 属已知问题，不影响出处追溯 |
