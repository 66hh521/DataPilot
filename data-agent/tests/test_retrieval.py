from app.retrieval.bm25 import BM25Index
from app.retrieval.fusion import reciprocal_rank_fusion


def test_bm25_matches_chinese_alias():
    index = BM25Index({
        "fact_order.order_amount": "订单金额 销售额 收入",
        "fact_order.order_quantity": "购买数量 销量 件数",
    })
    results = index.search("统计各地区销售额")
    assert results[0].item_id == "fact_order.order_amount"


def test_rrf_rewards_items_found_by_both_retrievers():
    results = reciprocal_rank_fusion({
        "dense": ["a", "b", "c"],
        "lexical": ["b", "d", "a"],
    })
    assert results[0].item_id == "b"
    assert set(results[0].sources) == {"dense", "lexical"}
