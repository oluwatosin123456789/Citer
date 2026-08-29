def evaluate_answer(answer: str, citations: list[dict], expected_files: list[str]) -> dict:
    cited_files = [c.get("file_path", "") for c in citations]
    passed = any(exp in f for exp in expected_files for f in cited_files) if citations else False
    hallucinated = any(exp not in " ".join(cited_files) for exp in expected_files) and not citations
    return {"passed": passed, "hallucinated": hallucinated, "cited_files": cited_files}