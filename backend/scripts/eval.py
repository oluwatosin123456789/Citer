import argparse
import sys

from app.eval.reports import save_report
from app.eval.runner import run_eval


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the eval harness")
    parser.add_argument("repo_url", help="GitHub repo URL to evaluate against")
    parser.add_argument("--dataset", default="golden")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    report = run_eval(args.dataset, args.repo_url, args.base_url)
    path = save_report(report)
    print(f"pass_rate={report['pass_rate']:.0%} hallucination={report['hallucination_rate']:.0%} avg_latency={report['avg_latency_ms']:.0f}ms")
    print(f"report: {path}")


if __name__ == "__main__":
    sys.exit(main())