import argparse
import asyncio
import json
from time import perf_counter

import httpx


async def run_query(client: httpx.AsyncClient, base_url: str, question: str) -> dict:
    started = perf_counter()
    trace = None
    row_count = None
    error = None
    async with client.stream(
        "POST", f"{base_url.rstrip('/')}/api/query", json={"query": question}
    ) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if not line.startswith("data:"):
                continue
            event = json.loads(line.removeprefix("data:").strip())
            if event.get("type") == "trace":
                trace = event
            elif event.get("type") == "result":
                row_count = event.get("row_count")
            elif event.get("type") == "error":
                error = event.get("message") or event.get("code")
    return {
        "latency_seconds": round(perf_counter() - started, 3),
        "row_count": row_count,
        "error": error,
        "trace": trace,
    }


async def main(args) -> None:
    async with httpx.AsyncClient(timeout=args.timeout) as client:
        results = []
        for index in range(args.rounds):
            result = await run_query(client, args.base_url, args.question)
            results.append(result)
            cache = (result.get("trace") or {}).get("cache", {})
            print(
                f"round={index + 1} latency={result['latency_seconds']}s "
                f"cache={cache} error={result['error']}"
            )

    if len(results) > 1 and results[-1]["latency_seconds"]:
        speedup = results[0]["latency_seconds"] / results[-1]["latency_seconds"]
        print(f"cold_to_warm_speedup={speedup:.2f}x")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="对比冷启动与缓存命中的链路延迟")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--question", default="查询2025年1月各省份销售额")
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=300.0)
    asyncio.run(main(parser.parse_args()))
