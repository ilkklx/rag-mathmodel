#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""安装辅助：检查 Python 与依赖；加 --install 则执行 pip 安装。"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REQ = os.path.join(ROOT, "requirements.txt")


def main():
    print("Python: %s" % sys.version.replace("\n", " "))
    if sys.version_info < (3, 9):
        print("[FAIL] 需要 Python 3.9+")
        return 1
    missing = []
    for mod, pkg in (("numpy", "numpy"), ("fastembed", "fastembed"), ("yaml", "PyYAML")):
        try:
            __import__(mod)
        except Exception:
            missing.append(pkg)
    if missing:
        print("[WARN] 缺少依赖: %s" % ", ".join(missing))
        print("       安装命令：pip install -r \"%s\"" % REQ)
        if "--install" in sys.argv:
            print("       正在执行 pip 安装 …")
            return subprocess.call([sys.executable, "-m", "pip", "install", "-r", REQ])
        return 1
    print("[PASS] 依赖齐备（numpy / fastembed / PyYAML）")
    print("下一步：python scripts/check.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
