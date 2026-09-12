import argparse
import asyncio
import json
from pathlib import Path
from time import perf_counter

import httpx

from app.evaluation.dataset import load_dataset
from app.evaluation.metrics import evaluate_case, summarize


async def run_case(client: httpx.AsyncClient, base_url: str, case) -> dict:
    started = perf_counter()
    sql = None
    rows = None
    error = None
    trace = None
    try:
        async with client.stream(
            "POST", f"{base_url.rstrip('/')}/api/query", json={"query": case.question}
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue
                event = json.loads(line.removeprefix("data:").strip())
                if event.get("type") == "result":
                    sql = event.get("sql")
                    rows = event.get("data")
                elif event.get("type") == "error":
                    error = event.get("message") or event.get("code")
                elif event.get("type") == "trace":
                    trace = event
    except Exception as exc:
        error = str(exc)

    result = evaluate_case(
        case=case,
        sql=sql,
        rows=rows,
        error=error,
        latency_seconds=perf_counter() - started,
    )
    result["trace"] = trace
    return result


async def main(args):
    cases = load_dataset(Path(args.dataset))
    if args.limit:
        cases = cases[: args.limit]
    async with httpx.AsyncClient(timeout=args.timeout) as client:
        results = []
        for index, case in enumerate(cases, start=1):
            print(f"[{index}/{len(cases)}] {case.id}: {case.question}")
            result = await run_case(client, args.base_url, case)
            results.append(result)
            print(
                f"  success={result['success']} table_recall={result['table_recall']:.2f} "
                f"column_recall={result['column_recall']:.2f} latency={result['latency_seconds']}s"
            )

    report = {"summary": summarize(results), "results": results}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"报告已写入: {output.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行 Text-to-SQL 端到端评测")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--dataset", default="evals/text2sql.yaml")
    parser.add_argument("--output", default="evals/report.json")
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--limit", type=int)
    asyncio.run(main(parser.parse_args()))
