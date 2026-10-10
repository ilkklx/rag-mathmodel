#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""回归检查：自然问法、top_k 边界和来源提示；不加载模型、不修改索引。"""
import importlib
import os
import sys
import subprocess
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from rag import bm25, rewrite, sources

retrieval = importlib.import_module("rag.retrieve")


class TargetedFixTests(unittest.TestCase):
    def test_natural_wording_preserves_terms(self):
        for query, term in (
            ("时间序列预测", "时间序列"),
            ("怎么用时间序列预测", "时间序列"),
            ("怎么用遗传算法", "遗传算法"),
            ("用AHP做综合评价", "AHP"),
        ):
            with self.subTest(query=query):
                rewritten = rewrite.rewrite(query, "B")
                self.assertIn(term, rewritten["terms"])
                self.assertIn('"%s"' % term, bm25.build_match(rewritten["bm25_query"])[0])

    def test_short_unknown_terms_still_skip_trigram(self):
        self.assertEqual(bm25.build_match("回归")[0], "")

    def test_invalid_top_k_rejected_before_initialization(self):
        for value in (0, -1, True, "3", 1.5):
            with self.subTest(value=value), patch.object(retrieval, "_init") as init:
                with self.assertRaises(ValueError):
                    retrieval.retrieve("AHP", top_k=value)
                init.assert_not_called()

    def test_top_k_cannot_exceed_candidate_pool(self):
        cfg = {"retrieval": {"topk": 10, "pool": 50}}
        with patch.object(retrieval, "_init", return_value=cfg):
            with self.assertRaisesRegex(ValueError, "retrieval.pool"):
                retrieval.retrieve("AHP", top_k=51)

    def test_cli_reports_parameter_error_without_traceback(self):
        for value in ("0", "-1", "51"):
            with self.subTest(value=value):
                result = subprocess.run(
                    [sys.executable, "-B", "query.py", "AHP", "--top-k", value],
                    cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                )
                self.assertEqual(result.returncode, 2)
                self.assertIn("error:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_filename_does_not_certify_official_source(self):
        for path in ("竞赛闲聊.pdf", "评阅要点.pdf", "format2026.doc"):
            with self.subTest(path=path):
                self.assertNotIn("官方", sources.trust_of(path, "ROOT1"))
        self.assertIn("低可信度", sources.trust_of("07_2026赛题参考/test.pdf", "ROOT5"))


if __name__ == "__main__":
    unittest.main()
