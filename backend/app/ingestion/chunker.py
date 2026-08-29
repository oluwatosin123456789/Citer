from dataclasses import dataclass, field

from app.ingestion.parser import SourceFile

TREE_SITTER_LANGUAGES = {
    "py": "python",
    "js": "javascript",
    "jsx": "jsx",
    "ts": "typescript",
    "tsx": "tsx",
    "go": "go",
    "rs": "rust",
    "java": "java",
    "rb": "ruby",
    "php": "php",
    "c": "c",
    "h": "c",
    "cpp": "cpp",
    "hpp": "cpp",
    "cs": "c_sharp",
    "swift": "swift",
    "kt": "kotlin",
    "css": "css",
    "scss": "scss",
    "html": "html",
    "yml": "yaml",
    "yaml": "yaml",
    "json": "json",
    "toml": "toml",
    "sql": None,
}

DEFINITION_NODE_TYPES = {
    "python": {"function_definition", "class_definition", "decorated_definition"},
    "javascript": {
        "function_declaration",
        "generator_function_declaration",
        "class_declaration",
        "method_definition",
        "arrow_function",
    },
    "jsx": {
        "function_declaration",
        "class_declaration",
        "method_definition",
        "arrow_function",
    },
    "typescript": {
        "function_declaration",
        "generator_function_declaration",
        "class_declaration",
        "method_definition",
        "arrow_function",
        "interface_declaration",
        "type_alias_declaration",
        "enum_declaration",
        "function_signature",
    },
    "tsx": {
        "function_declaration",
        "class_declaration",
        "method_definition",
        "arrow_function",
        "interface_declaration",
        "type_alias_declaration",
        "enum_declaration",
    },
    "go": {"function_declaration", "method_declaration", "type_declaration", "type_spec"},
    "rust": {"function_item", "struct_item", "enum_item", "impl_item", "trait_item", "mod_item"},
    "java": {"method_declaration", "constructor_declaration", "class_declaration", "interface_declaration", "enum_declaration"},
    "ruby": {"method", "singleton_method", "class", "module"},
    "php": {"function_definition", "class_declaration", "method_declaration", "interface_declaration"},
    "c": {"function_definition", "struct_specifier", "enum_specifier", "union_specifier"},
    "cpp": {"function_definition", "class_specifier", "struct_specifier", "enum_specifier", "union_specifier"},
    "c_sharp": {"method_declaration", "class_declaration", "constructor_declaration", "interface_declaration", "enum_declaration", "struct_declaration"},
    "swift": {"function_declaration", "class_declaration", "struct_declaration", "enum_declaration", "protocol_declaration"},
    "kotlin": {"function_declaration", "class_declaration", "object_declaration", "interface_declaration"},
}

CLASS_NODE_TYPES = {
    "python": {"class_definition", "decorated_definition"},
    "javascript": {"class_declaration"},
    "typescript": {"class_declaration"},
    "java": {"class_declaration", "interface_declaration", "enum_declaration"},
    "c": {"struct_specifier", "enum_specifier", "union_specifier"},
    "cpp": {"class_specifier", "struct_specifier", "enum_specifier", "union_specifier"},
    "c_sharp": {"class_declaration", "interface_declaration", "enum_declaration", "struct_declaration"},
    "go": {"type_declaration", "type_spec"},
    "rust": {"struct_item", "enum_item", "impl_item", "trait_item"},
    "ruby": {"class", "module"},
    "swift": {"class_declaration", "struct_declaration", "enum_declaration", "protocol_declaration"},
    "kotlin": {"class_declaration", "object_declaration", "interface_declaration"},
}

FUNCTION_MEMBER_NODE_TYPES = {
    "python": {"function_definition"},
    "javascript": {"method_definition", "function_declaration", "arrow_function"},
    "typescript": {"method_definition", "function_declaration", "arrow_function"},
    "java": {"method_declaration", "constructor_declaration"},
    "c": {"function_definition"},
    "cpp": {"function_definition"},
    "c_sharp": {"method_declaration", "constructor_declaration"},
    "go": {"function_declaration", "method_declaration"},
    "rust": {"function_item"},
    "ruby": {"method", "singleton_method"},
    "swift": {"function_declaration"},
    "kotlin": {"function_declaration"},
}

MAX_CHUNK_LINES = 400
MAX_CHUNK_CHARS = 8000
MAX_CHUNKS_PER_FILE = 500


@dataclass
class Chunk:
    file_path: str
    language: str
    content: str
    symbol_name: str | None = None
    symbol_type: str | None = None
    start_line: int = 1
    end_line: int = 1
    metadata: dict = field(default_factory=dict)

    def enriched_content(self) -> str:
        header = f"File: {self.file_path}"
        if self.symbol_name:
            header += f"\nSymbol: {self.symbol_name} ({self.symbol_type or 'def'})"
        return f"{header}\nLines: {self.start_line}-{self.end_line}\n```{self.language}\n{self.content}\n```"


def chunk_file(source: SourceFile) -> list[Chunk]:
    chunks = _chunk_with_tree_sitter(source)
    if chunks:
        return chunks
    return [_whole_file_chunk(source)]


def _chunk_with_tree_sitter(source: SourceFile) -> list[Chunk]:
    parser = _get_parser(source.language)
    if parser is None:
        return []

    tree = parser.parse(source.content.encode("utf-8"))
    root = tree.root_node

    chunks: list[Chunk] = []
    definition_ranges: list[tuple[int, int]] = []
    language = TREE_SITTER_LANGUAGES.get(source.language)

    for child in root.children:
        node = _unwrap_export(child)
        if node.type in _definition_types(language):
            definition_ranges.append((child.start_byte, child.end_byte))
            chunks.extend(_extract_definition_chunks(source, node, language))

    _append_top_level_chunk(source, chunks, definition_ranges)

    capped = chunks[:MAX_CHUNKS_PER_FILE]
    return [c for c in capped if c.content.strip()]


def _unwrap_export(node):
    """Descend through declaration wrappers (e.g. TypeScript `export_statement`)."""
    while node.type in {"export_statement", "module_declaration", "declaration"}:
        inner = None
        for child in node.children:
            if child.type in _all_definition_types():
                inner = child
                break
        if inner is None:
            break
        node = inner
    return node


def _all_definition_types() -> set[str]:
    return set().union(*DEFINITION_NODE_TYPES.values())


def _extract_definition_chunks(
    source: SourceFile,
    node,
    language: str | None,
) -> list[Chunk]:
    if node.type in _class_types(language):
        return _chunk_class(source, node, language)

    text = _node_text(source, node)
    return [_make_chunk(source, node, text, _symbol_name(node), _symbol_type(node, language))]


def _chunk_class(source: SourceFile, class_node, language: str | None) -> list[Chunk]:
    class_text = _node_text(source, class_node)
    if not _oversized(class_text):
        return [_make_chunk(source, class_node, class_text, _symbol_name(class_node), "class")]

    class_name = _symbol_name(class_node) or "class"
    chunks = [_make_chunk(source, class_node, _class_header(source, class_node), class_name, "class")]

    for child in class_node.children:
        if child.type in _function_member_types(language):
            member_text = _node_text(source, child)
            if not _oversized(member_text):
                chunks.append(
                    _make_chunk(source, child, member_text, _symbol_name(child), "method")
                )

    return [c for c in chunks if c.content.strip()]


def _class_header(source: SourceFile, class_node) -> str:
    lines = _node_text(source, class_node).splitlines()
    header = []
    for line in lines:
        header.append(line)
        stripped = line.strip()
        if stripped.endswith(":"):
            break
        if stripped.endswith("{") or stripped.endswith("(") and not stripped.endswith("}"):
            break
    return "\n".join(header)


def _append_top_level_chunk(
    source: SourceFile,
    chunks: list[Chunk],
    definition_ranges: list[tuple[int, int]],
) -> None:
    content = source.content
    total = len(content)

    line_starts: list[int] = []
    offset = 0
    for line in content.splitlines(keepends=True):
        line_starts.append(offset)
        offset += len(line)

    def line_of(byte: int) -> int:
        lo, hi = 0, len(line_starts)
        while lo < hi:
            mid = (lo + hi) // 2
            if line_starts[mid] <= byte:
                lo = mid + 1
            else:
                hi = mid
        return lo

    start = 0
    top_level_parts: list[tuple[int, int, str]] = []

    for def_start, def_end in sorted(definition_ranges):
        if def_start > start:
            part = content[start:def_start]
            if part.strip():
                top_level_parts.append((line_of(start), line_of(def_start - 1), part.rstrip("\n")))
        start = max(start, def_end)

    if start < total:
        part = content[start:]
        if part.strip():
            top_level_parts.append((line_of(start), line_of(total - 1), part.rstrip("\n")))

    if not top_level_parts:
        return

    joined = "\n\n".join(p[2] for p in top_level_parts)
    chunks.append(
        Chunk(
            file_path=source.relative_path,
            language=source.language,
            content=joined,
            symbol_type="module",
            start_line=top_level_parts[0][0],
            end_line=top_level_parts[-1][1],
            metadata={"module_top_level": True},
        )
    )


def _make_chunk(
    source: SourceFile,
    node,
    text: str,
    symbol_name: str | None,
    symbol_type: str | None,
) -> Chunk:
    return Chunk(
        file_path=source.relative_path,
        language=source.language,
        content=text,
        symbol_name=symbol_name,
        symbol_type=symbol_type,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
    )


def _whole_file_chunk(source: SourceFile) -> Chunk:
    lines = source.content.splitlines()
    return Chunk(
        file_path=source.relative_path,
        language=source.language,
        content=source.content,
        symbol_type="module",
        start_line=1,
        end_line=len(lines),
    )


def _symbol_name(node) -> str | None:
    if node.type == "decorated_definition":
        node = node.child_by_field_name("definition") or node
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return _node_text_raw(node, name_node)
    for child in node.children:
        if child.type in {"identifier", "type_identifier", "property_identifier", "constant"}:
            return _node_text_raw(node, child)
        if child.type in {"declarator", "variable_declarator"}:
            name_node = child.child_by_field_name("name")
            if name_node is not None:
                return _node_text_raw(node, name_node)
    return None


def _symbol_type(node, language: str | None) -> str:
    if node.type in _class_types(language):
        return "class"
    if node.type in {"method_definition", "method_declaration", "method", "singleton_method", "constructor_declaration", "function_signature"}:
        return "method"
    if node.type in {"interface_declaration", "type_alias_declaration", "enum_declaration", "type_spec", "struct_item", "enum_item", "trait_item", "impl_item"}:
        return "type"
    return "function"


def _definition_types(language: str | None) -> set[str]:
    return DEFINITION_NODE_TYPES.get(language, set())


def _class_types(language: str | None) -> set[str]:
    return CLASS_NODE_TYPES.get(language, set())


def _function_member_types(language: str | None) -> set[str]:
    return FUNCTION_MEMBER_NODE_TYPES.get(language, set())


def _oversized(text: str) -> bool:
    return text.count("\n") > MAX_CHUNK_LINES or len(text) > MAX_CHUNK_CHARS


def _node_text(source: SourceFile, node) -> str:
    return source.content.encode("utf-8")[node.start_byte:node.end_byte].decode("utf-8")


def _node_text_raw(_, node) -> str:
    return node.text.decode("utf-8")


def _get_parser(extension: str):
    language = TREE_SITTER_LANGUAGES.get(extension)
    if not language:
        return None
    try:
        from tree_sitter_language_pack import get_parser

        return get_parser(language)
    except Exception:
        pass
    try:
        from tree_sitter_languages import get_parser

        return get_parser(language)
    except Exception:
        pass
    try:
        module = __import__(f"tree_sitter_{language.replace('-', '_')}")
        grammar = getattr(module, "language")()
        from tree_sitter import Parser

        parser = Parser()
        parser.language = grammar
        return parser
    except Exception:
        return None