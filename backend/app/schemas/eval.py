from pydantic import BaseModel


class EvalRunRequest(BaseModel):
    dataset: str = "golden"


class EvalRunResult(BaseModel):
    run_id: str
    pass_rate: float
    hallucination_rate: float
    avg_latency_ms: float