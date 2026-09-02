import queue

from app.agent.format import parse_citations
from app.agent.llm import format_history, messages_from_text

SYNTHESIZER_SYSTEM = (
    "You are a senior codebase analyst. Answer the user's question using ONLY the "
    "provided context. Rules:\n"
    "1. Cite the exact source for every claim using [n] markers, e.g. 'login() validates "
    "credentials [1]'.\n"
    "2. Never invent file paths, line numbers, or code.\n"
    "3. If the context does not answer the question, say so explicitly.\n"
    "4. Use conversation history to resolve pronouns like 'it' or 'that file'."
)

NO_CONTEXT = "No relevant code was retrieved for this question."


def make_synthesize_node(model):
    def synthesize_node(state, config=None) -> dict:
        question = state["question"]
        history = state.get("messages", [])
        context = "\n\n".join(state.get("context", []))
        if not context.strip():
            context = NO_CONTEXT

        human = (
            f"Conversation history:\n{format_history(history)}\n\n"
            f"Question: {question}\n\nContext:\n{context}"
        )

        token_queue = None
        if config:
            token_queue = (config.get("configurable") or {}).get("token_queue")

        messages = messages_from_text(SYNTHESIZER_SYSTEM, human)
        tokens: list[str] = []
        for chunk in model.stream(messages):
            piece = chunk.content or ""
            tokens.append(piece)
            if token_queue is not None:
                token_queue.put(("token", piece))
        answer = "".join(tokens).strip()

        citations = parse_citations(answer, state.get("retrieved_chunks", []))

        tool_calls = list(state.get("tool_calls", []))
        tool_calls.append({"node": "synthesize", "tokens": len(answer.split())})

        return {"answer": answer, "citations": citations, "tool_calls": tool_calls}

    return synthesize_node