from __future__ import annotations

import re

import jieba.analyse

from app.semantic.registry import semantic_registry


COMMON_SYNONYMS = {
    "销售额": ["成交金额", "销售金额", "销售收入", "GMV"],
    "成交额": ["成交金额", "销售额", "GMV"],
    "销量": ["销售数量", "购买件数", "商品销量"],
    "订单": ["订单数", "订单数量", "下单数"],
    "客单价": ["平均客单价", "平均订单金额", "AOV"],
    "省份": ["省", "地区", "区域"],
    "地区": ["区域", "大区", "省份"],
    "月份": ["月", "month"],
    "季度": ["季", "quarter"],
}


def expand_keywords_locally(
    query: str, keywords: list[str] | None = None, domain: str = "general"
) -> list[str]:
    """Deterministic domain expansion used on the latency-sensitive path."""
    expanded = list(dict.fromkeys([query, *(keywords or [])]))
    normalized = query.lower()

    for trigger, synonyms in COMMON_SYNONYMS.items():
        if trigger in normalized:
            expanded.extend(synonyms)

    for metric in semantic_registry.all_metrics():
        terms = [metric.name, metric.display_name, *metric.aliases]
        if any(term.lower() in normalized for term in terms):
            expanded.extend(terms)
            if domain == "column":
                expanded.extend(metric.required_columns)

    expanded.extend(re.findall(r"\d{4}年(?:\d{1,2}月)?|第?[一二三四1-4]季度|Q[1-4]", query))
    expanded.extend(jieba.analyse.extract_tags(query, topK=8))
    return list(dict.fromkeys(item.strip() for item in expanded if item and item.strip()))
