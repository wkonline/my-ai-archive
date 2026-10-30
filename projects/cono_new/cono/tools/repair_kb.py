"""维修知识库检索。

按故障现象在历史维修记录（ServiceDetail）中检索相似案例，
归纳出高频的故障原因与维修方法，形成维修方法总结。

中文没有天然词边界，且历史数据里同一故障的写法差异较大
（如「左侧无信号」「左无信号」「左侧没有信号」），
因此采用字符级 bigram 相似度，不依赖分词库。
"""
import re
from collections import Counter

from cono import models


# 无实际诊断价值的内容，不参与检索与归纳
NOISE_VALUES = {
    '', '/', '\\', 'null', 'none', '无', '没有', 'na', 'n/a', '-', '--', '测试正常',
    '重测ok', '测试ok', '正常', '报废', '待定', '未知',
}

MIN_SIMILARITY = 0.34

SUMMARY_TOP_N = 5

SIMILAR_CASE_LIMIT = 20


def _normalize(text):
    """去掉空白、标点与全角符号，便于比较。"""
    text = str(text or '')
    text = re.sub(r'[\s\u3000]+', '', text)
    text = re.sub(r'[，。、；：！？,.;:!?()（）\[\]【】{}<>《》"\'`~@#$%^&*+=|\\/_-]+', '', text)
    return text.lower()


def is_noise(text):
    return _normalize(text) in {_normalize(v) for v in NOISE_VALUES}


def _bigrams(text):
    if len(text) < 2:
        return {text} if text else set()
    return {text[i:i + 2] for i in range(len(text) - 1)}


def similarity(left, right):
    """字符 bigram 的 Dice 系数，范围 0~1。"""
    a, b = _bigrams(left), _bigrams(right)
    if not a or not b:
        return 0.0
    return 2 * len(a & b) / (len(a) + len(b))


def search_cases(query, limit=SIMILAR_CASE_LIMIT):
    """按故障现象检索历史维修案例，按相似度倒序返回。"""
    query_norm = _normalize(query)
    if not query_norm:
        return []

    matched = []
    for row in models.ServiceDetail.objects.select_related(
        'customer', 'product', 'productcategory', 'repairman', 'service'
    ).all():
        fault = _normalize(row.fault_text)
        if not fault or is_noise(row.fault_text):
            continue
        score = similarity(query_norm, fault)
        # 现象文字包含关键词时提升权重，避免长描述因 bigram 稀释而漏检
        if query_norm in fault:
            score = max(score, 0.8)
        if score >= MIN_SIMILARITY:
            matched.append((score, row))

    matched.sort(key=lambda item: (-item[0], -item[1].id))
    return [{'score': round(score, 3), 'record': row} for score, row in matched[:limit]]


# 归纳时把写法相近的条目合并，避免「更换电源模块」与
# 「更换电源模块（±15V/500mA）」被拆成两条
CLUSTER_SIMILARITY = 0.62


def _cluster(counter, samples):
    """把高频条目按相似度归并成若干代表条目。"""
    ordered = sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
    clusters = []
    for key, count in ordered:
        placed = False
        for cluster in clusters:
            if similarity(key, cluster['key']) >= CLUSTER_SIMILARITY:
                cluster['count'] += count
                # 保留出现次数最多的写法作为代表
                if count > cluster['best_count']:
                    cluster['best_count'] = count
                    cluster['text'] = samples[key]
                placed = True
                break
        if not placed:
            clusters.append({
                'key': key,
                'text': samples[key],
                'count': count,
                'best_count': count,
            })
    clusters.sort(key=lambda c: -c['count'])
    return [{'text': c['text'], 'count': c['count']} for c in clusters[:SUMMARY_TOP_N]]


def summarize(cases):
    """把相似案例的原因与方法归纳成高频条目。"""
    reasons = Counter()
    methods = Counter()
    reason_samples = {}
    method_samples = {}

    for case in cases:
        row = case['record']
        reason = str(row.fault_reason or '').strip()
        method = str(row.repair_method or '').strip()
        if reason and not is_noise(reason):
            key = _normalize(reason)
            reasons[key] += 1
            reason_samples.setdefault(key, reason)
        if method and not is_noise(method):
            key = _normalize(method)
            methods[key] += 1
            method_samples.setdefault(key, method)

    return {
        'total': len(cases),
        'reasons': _cluster(reasons, reason_samples),
        'methods': _cluster(methods, method_samples),
    }


def build_knowledge(query):
    """检索 + 归纳，返回可直接渲染的结果。"""
    query = str(query or '').strip()
    if not query:
        return {'query': '', 'cases': [], 'summary': None}
    cases = search_cases(query)
    return {
        'query': query,
        'cases': cases,
        'summary': summarize(cases) if cases else None,
    }
