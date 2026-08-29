"use client";

import { useEffect, useState } from "react";
import { getEvalRuns } from "@/lib/api";

type EvalRun = {
  dataset: string;
  pass_rate: number;
  hallucination_rate: number;
  avg_latency_ms: number;
  results: { question: string; passed: boolean; latency_ms: number }[];
};

export default function EvalDashboard() {
  const [runs, setRuns] = useState<EvalRun[]>([]);

  useEffect(() => {
    getEvalRuns().then(setRuns);
  }, []);

  return (
    <main className="mx-auto max-w-5xl p-6">
      <h1 className="mb-4 text-2xl font-bold">Evaluation Dashboard</h1>
      {runs.length === 0 && <p className="text-zinc-500">No eval runs yet.</p>}
      {runs.map((run, i) => (
        <section key={i} className="mb-6 rounded-lg border border-zinc-800 p-4">
          <div className="mb-2 flex gap-6 text-sm">
            <span>Pass rate: <b>{(run.pass_rate * 100).toFixed(0)}%</b></span>
            <span>Hallucination: <b>{(run.hallucination_rate * 100).toFixed(0)}%</b></span>
            <span>Avg latency: <b>{run.avg_latency_ms.toFixed(0)}ms</b></span>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-zinc-400">
                <th className="py-1">Question</th>
                <th>Pass</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {run.results.map((r, j) => (
                <tr key={j} className="border-t border-zinc-800">
                  <td className="py-1">{r.question}</td>
                  <td>{r.passed ? "yes" : "no"}</td>
                  <td>{r.latency_ms.toFixed(0)}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ))}
    </main>
  );
}