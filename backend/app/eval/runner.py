import asyncio
import time

import httpx

from app.eval.dataset import DATASETS
from app.eval.metrics import evaluate_answer


async def run_dataset(name: str, repo_url: str, base_url: str = "http://localhost:8000") -> dict:
    results = []
    async with httpx.AsyncClient(base_url=base_url) as client:
        for item in DATASETS[name]:
            start = time.perf_counter()
            resp = await client.post(
                "/api/ask",
                json={"question": item["question"], "repo_url": repo_url},
            )
            latency_ms = (time.perf_counter() - start) * 1000
            body = resp.json()
            metrics = evaluate_answer(
                answer=body.get("answer", ""),
                citations=body.get("citations", []),
                expected_files=item["expected_files"],
            )
            results.append({"question": item["question"], "latency_ms": latency_ms, **metrics})

    return {
        "dataset": name,
        "pass_rate": sum(r["passed"] for r in results) / len(results),
        "hallucination_rate": sum(r["hallucinated"] for r in results) / len(results),
        "avg_latency_ms": sum(r["latency_ms"] for r in results) / len(results),
        "results": results,
    }


def run_eval(name: str, repo_url: str) -> dict:
    return asyncio.run(run_dataset(name, repo_url))