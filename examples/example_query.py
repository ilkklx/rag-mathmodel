#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最小 CLI 调用示例：等价于 `python query.py "..." --top-k 5 --json`。"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
cmd = [sys.executable, os.path.join(ROOT, "query.py"),
       "2018A 高温作业专用服装设计用了什么模型", "--top-k", "5", "--json"]
print("$ " + " ".join('"%s"' % c if " " in c else c for c in cmd))
p = subprocess.run(cmd, capture_output=True)
data = json.loads(p.stdout.decode("utf-8", errors="replace"))
print("返回 %d 条；第 1 条：%s#%s"
      % (len(data["results"]), data["results"][0]["title"], data["results"][0]["chunk_id"]))
