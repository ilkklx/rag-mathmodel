# -*- coding: utf-8 -*-
"""Phase 5 查询改写模块（通用规则，不读取任何 GT / expected source / 题目 ID）。

两个方案：
  Scheme-A: 规范化 + 术语切分 + 缩写/同义词扩展
  Scheme-B: 规范化 + 术语切分（不做同义词扩展，用于消融对照）
"""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---- 通用数学建模术语词典（用于最长匹配切分；与任何具体题目无关） ----
LEXICON = [
    "元胞自动机", "遗传算法", "粒子群优化", "粒子群算法", "模拟退火", "蚁群算法", "差分进化",
    "层次分析法", "一致性检验", "判断矩阵", "熵权法", "熵值法", "灰色关联", "灰色预测",
    "多目标优化", "动态规划", "线性规划", "整数规划", "非线性规划", "二次规划", "目标规划",
    "最短路径", "最小生成树", "最大流", "二分图匹配", "图论模型", "网络模型",
    "蒙特卡洛", "蒙特卡罗", "排队论", "排队长度", "服务强度", "到达率", "服务率",
    "回归分析", "多元回归", "逐步回归", "岭回归", "逻辑回归",
    "主成分分析", "因子分析", "聚类分析", "判别分析", "典型相关分析", "方差分析",
    "时间序列", "指数平滑", "神经网络", "支持向量机", "随机森林", "决策树",
    "有限差分", "有限元", "有限体积", "差分格式", "隐式格式", "显式格式", "隐式", "显式",
    "偏微分方程", "常微分方程", "热传导方程", "扩散方程", "热传导", "对流换热", "对流传质",
    "边界条件", "初始条件", "定解条件", "网格无关", "收敛性", "稳定性",
    "参数辨识", "参数估计", "参数反演", "拟合优度", "最小二乘", "残差",
    "灵敏度分析", "敏感性分析", "误差分析", "不确定性分析",
    "综合评价", "模糊综合评价", "数据包络分析", "层次分析", "熵权",
    "交通流", "通行能力", "车流量", "路径规划", "覆盖率", "光学效率", "余弦效率", "阴影遮挡",
    "多波束", "测线", "数值求解", "数值解", "几何模型", "几何建模", "建模优化",
    "储能", "充放电", "光伏", "电价", "负载", "微网", "购电",
    "优化模型", "评价模型", "预测模型", "仿真模型", "微分方程模型",
    "目标函数", "约束条件", "决策变量", "可行域", "最优解",
    "数据预处理", "缺失值", "异常值", "归一化", "标准化",
]

SYNONYMS = {
    "TOPSIS": ["优劣解距离法", "理想解法", "正理想解", "贴近度"],
    "AHP": ["层次分析法", "判断矩阵", "一致性检验"],
    "PSO": ["粒子群优化", "粒子群算法", "惯性权重"],
    "GA": ["遗传算法", "交叉", "变异", "适应度"],
    "DEA": ["数据包络分析"],
    "SVM": ["支持向量机"],
    "BP": ["BP神经网络", "反向传播"],
    "LSTM": ["长短期记忆网络"],
    "Floyd": ["最短路径", "多源最短路径"],
    "Dijkstra": ["最短路径", "单源最短路径"],
    "K-means": ["聚类分析", "K均值"],
    "ARIMA": ["时间序列", "自回归"],
    "PDE": ["偏微分方程"],
    "ODE": ["常微分方程"],
}

# 仅在这些上下文出现时才展开的歧义缩写（避免误扩）
AMBIGUOUS = {"CA": (["元胞自动机"], ["交通流", "模拟", "演化", "网格"])}

QUESTION_WORDS = ["怎么", "如何", "什么情况", "什么样", "什么", "哪些", "哪些个", "多少",
                  "请问", "请", "能否", "可以", "是否", "为什么", "是什么", "怎么样",
                  "的", "了", "吗", "呢", "啊", "里", "中", "下", "上",
                  "和", "与", "及", "或", "在", "对", "把", "为", "是", "该", "求",
                  "使用", "适合", "涉及", "属于", "需要", "进行", "一般", "通常"]


def normalize(q):
    s = q.strip()
    s = s.replace("？", " ").replace("?", " ").replace("！", " ").replace("!", " ")
    s = s.replace("，", " ").replace(",", " ").replace("。", " ").replace("；", " ").replace(";", " ")
    # 全角转半角
    out = []
    for ch in s:
        code = ord(ch)
        if code == 0x3000:
            out.append(" ")
        elif 0xFF01 <= code <= 0xFF5E:
            out.append(chr(code - 0xFEE0))
        else:
            out.append(ch)
    s = "".join(out)
    # 英文缩写统一大写
    for k in SYNONYMS:
        s = re.sub(re.escape(k), k, s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip()


def strip_question_words(s):
    for w in sorted(QUESTION_WORDS, key=len, reverse=True):
        s = s.replace(w, " ")
    return re.sub(r"\s+", " ", s).strip()


def segment(s, preserve_starts=False):
    """默认沿用 V2 分词；补救模式不跨过术语或 ASCII 词的起点。"""
    lex = sorted(LEXICON, key=len, reverse=True)
    toks, i = [], 0
    while i < len(s):
        hit = None
        for term in lex:
            if s.startswith(term, i):
                hit = term
                break
        if hit:
            toks.append(hit)
            i += len(hit)
            continue
        ch = s[i]
        if ch == " ":
            i += 1
            continue
        # 连续 ASCII 字母/数字整体作为一个词元（避免 TOPSIS -> TO PS IS）
        if ch.isascii() and ch.isalnum():
            j = i
            while j < len(s) and s[j].isascii() and s[j].isalnum():
                j += 1
            toks.append(s[i:j])
            i = j
            continue
        # 保留两字窗口，但不吞掉下一位置开始的术语（如「用时间序列」）。
        if i + 1 < len(s) and s[i + 1] != " ":
            nxt = s[i + 1]
            starts_term = preserve_starts and any(s.startswith(term, i + 1) for term in lex)
            starts_ascii = preserve_starts and nxt.isascii() and nxt.isalnum()
            if not starts_term and not starts_ascii:
                toks.append(s[i:i + 2])
                i += 2
                continue
        toks.append(ch)
        i += 1
    return [t for t in toks if t.strip()]


def expand(query, toks):
    """缩写/同义词扩展；返回 (扩展词列表, 命中的规则)。"""
    ext, rules = [], []
    up = query.upper()
    for abbr, syns in SYNONYMS.items():
        if abbr.upper() in up:
            ext.extend(syns)
            rules.append("%s->%s" % (abbr, "/".join(syns)))
    for abbr, (syns, ctx) in AMBIGUOUS.items():
        if re.search(r"(?<![A-Za-z])%s(?![A-Za-z])" % abbr, query):
            if any(c in query for c in ctx):
                ext.extend(syns)
                rules.append("%s->%s(上下文充分)" % (abbr, "/".join(syns)))
            else:
                rules.append("%s 未展开(上下文不足)" % abbr)
    return ext, rules


def rewrite(query, scheme="A"):
    """返回 dict：normalized / terms / bm25_query / emb_query / rules / fallback。"""
    norm = normalize(query)
    core = strip_question_words(norm)
    toks = segment(core)
    if not toks:
        return {"normalized": norm, "terms": [], "bm25_query": query,
                "emb_query": query, "rules": ["切分失败"], "fallback": True}
    # 仅在所有词元都短于 trigram 下限时补救，保留已有有效词法查询的排序。
    if not any(len(t) >= 3 for t in toks):
        rescued = segment(core, preserve_starts=True)
        if any(len(t) >= 3 for t in rescued):
            toks = rescued
    ext, rules = ([], [])
    if scheme == "A":
        ext, rules = expand(norm, toks)
    terms = toks + ext
    # 去重且保序
    seen, uniq = set(), []
    for t in terms:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    bm25 = " ".join(uniq)
    emb = norm
    if ext:
        emb = norm + " " + " ".join(ext)
    fallback = len(core) < 2
    return {"normalized": norm, "terms": uniq, "bm25_query": bm25, "emb_query": emb,
            "rules": rules, "fallback": fallback}
