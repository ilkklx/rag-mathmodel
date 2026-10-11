# -*- coding: utf-8 -*-
"""配置加载：所有路径均以「资源包根目录」为基准，不含任何原电脑绝对路径。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

DEFAULTS = {
    "package": {"name": "RAG-MathModel", "version": "1.0.1"},
    "index": {"db": "data/index/mvp.db", "vectors": "data/index/vectors.npy"},
    "model": {"name": "BAAI/bge-small-zh-v1.5", "cache_dir": "models/fastembed",
              "local_files_only": True},
    "retrieval": {"rewrite_scheme": "B", "pool": 50, "topk": 10,
                  "recall_multiplier": 2, "rrf_k": 60},
    "paths": {"source_map": "data/metadata/source_map.json", "library_roots": {}},
}


def _load_yaml(p):
    try:
        import yaml
    except Exception:
        return None
    with io.open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load(path=None):
    """读 config/config.yaml（不存在则 config.example.yaml），与默认值合并。"""
    cands = [path] if path else [
        os.path.join(ROOT, "config", "config.local.yaml"),
        os.path.join(ROOT, "config", "config.yaml"),
        os.path.join(ROOT, "config", "config.example.yaml"),
    ]
    cfg = dict(DEFAULTS)
    used = None
    for c in cands:
        if c and os.path.isfile(c):
            loaded = _load_yaml(c)
            if loaded:
                cfg = _merge(cfg, loaded)
                used = c
                break
    cfg["_config_file"] = used
    cfg["_root"] = ROOT
    return cfg


def abspath(cfg, rel):
    """相对路径一律相对资源包根目录解析。"""
    if not rel:
        return None
    return rel if os.path.isabs(rel) else os.path.abspath(os.path.join(ROOT, rel))
