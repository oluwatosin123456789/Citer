from types import SimpleNamespace


class FakeChatModel:
    """A scriptable stand-in for a real chat model.

    - ``invoke(messages)`` returns ``invoke_responses.pop(0)`` (or a default).
    - ``stream(messages)`` yields ``stream_chunks`` one at a time.
    """

    def __init__(
        self,
        default_response: str = "",
        invoke_responses: list[str] | None = None,
        stream_chunks: list[str] | None = None,
    ):
        self.default_response = default_response
        self.invoke_responses = list(invoke_responses or [])
        self.stream_chunks = list(stream_chunks or [default_response])
        self.invocations: list[list] = []
        self.stream_calls = 0

    def invoke(self, messages):
        self.invocations.append(messages)
        if self.invoke_responses:
            return SimpleNamespace(content=self.invoke_responses.pop(0))
        return SimpleNamespace(content=self.default_response)

    def stream(self, messages):
        self.stream_calls += 1
        self.invocations.append(messages)
        for chunk in self.stream_chunks:
            yield SimpleNamespace(content=chunk)