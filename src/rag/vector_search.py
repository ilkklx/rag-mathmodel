# -*- coding: utf-8 -*-
"""向量检索：fastembed(BAAI/bge-small-zh-v1.5, ONNX) + 预建 vectors.npy（已 L2 归一化）。"""
import numpy as np

_MODELS = {}
_MATS = {}


def get_model(cfg):
    lfo = bool(cfg["model"].get("local_files_only", True))
    key = (cfg["model"]["name"], cfg["model"]["cache_dir"], lfo)
    if key not in _MODELS:
        from fastembed import TextEmbedding
        kwargs = {"model_name": cfg["model"]["name"], "cache_dir": cfg["model"]["cache_dir"]}
        try:
            _MODELS[key] = TextEmbedding(local_files_only=lfo, **kwargs)
        except TypeError:
            _MODELS[key] = TextEmbedding(**kwargs)
    return _MODELS[key]


def get_mat(cfg):
    p = cfg["_vectors_path"]
    if p not in _MATS:
        m = np.load(p)
        n = np.linalg.norm(m, axis=1, keepdims=True)
        n[n == 0] = 1.0
        _MATS[p] = m / n
    return _MATS[p]


def embed_one(cfg, text):
    q = list(get_model(cfg).query_embed([text]))[0].astype("float32")
    return q / (np.linalg.norm(q) or 1.0)


def search(cfg, query, topn, filt):
    qv = embed_one(cfg, query)
    sims = get_mat(cfg) @ qv
    order = np.argsort(-sims)
    ids = []
    for i in order:
        rid = int(i) + 1
        if filt(rid):
            ids.append(rid)
        if len(ids) >= topn:
            break
    return ids, sims
