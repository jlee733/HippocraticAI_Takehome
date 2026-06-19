import re

META_PREFIX_PATTERNS = [
    r"^(?:sure!?\s*)",
    r"^(?:of course!?\s*)",
    r"^(?:okay!?\s*)",
    r"^(?:here(?:'s| is)\s+(?:a\s+)?(?:bedtime\s+)?story(?: for you)?[:.\-]?\s*)",
    r"^(?:i(?:'d| would)\s+be happy to[^.]*\.\s*)",
]

META_SUFFIX_PATTERNS = [
    r"\n+(?:i hope you (?:enjoy|like)[^.]*\.?|let me know if[^.]*\.?|would you like[^?]*\??)\s*$",
    r"\n+(?:what (?:kind|type|name|sort)[^?]*\?|would you like[^?]*\?|do you want[^?]*\?|could you tell me[^?]*\?)\s*$",
]


LINE_LABEL_PATTERN = re.compile(r"\bline\s*\d+\s*:\s*", re.IGNORECASE)


def _strip_line_labels(text: str) -> str:
    text = LINE_LABEL_PATTERN.sub("", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def story_only(response: str) -> str:
    """Strip common LLM commentary and return just the story text."""
    text = response.strip()

    for pattern in META_PREFIX_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).lstrip()

    for pattern in META_SUFFIX_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE).rstrip()

    return _strip_line_labels(text)


def parse_story(response: str) -> tuple[str, str]:
    """Split a story response into title and body."""
    text = story_only(response)
    if not text:
        return "", ""

    lines = text.splitlines()
    title = _clean_title(lines[0])
    body = "\n".join(lines[1:]).strip()
    return title, body


def _clean_title(line: str) -> str:
    title = LINE_LABEL_PATTERN.sub("", line.strip())
    title = re.sub(r"^#+\s*", "", title)
    title = re.sub(r"^\*\*(.+)\*\*$", r"\1", title)
    title = re.sub(r"^title:\s*", "", title, flags=re.IGNORECASE)
    return title.strip()

