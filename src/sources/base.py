from abc import ABC, abstractmethod
from datetime import datetime
import html
from html.parser import HTMLParser
import re

from pydantic import BaseModel

_BLOCK_TAGS = frozenset(
    {
        "article",
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "hr",
        "li",
        "ol",
        "p",
        "section",
        "tr",
        "ul",
    }
)
_SKIP_TAGS = frozenset({"script", "style"})


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_lower = tag.lower()
        if tag_lower in _SKIP_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        if tag_lower == "li":
            self._chunks.append("\n- ")
        elif tag_lower in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag_lower = tag.lower()
        if tag_lower in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if self._skip_depth > 0:
            return
        if tag_lower in _BLOCK_TAGS:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def get_text(self) -> str:
        return "".join(self._chunks)


def clean_html(raw_html: str) -> str:
    if not raw_html or not raw_html.strip():
        return ""

    prepared = raw_html
    if "<" not in prepared and "&lt;" in prepared:
        prepared = html.unescape(prepared)

    parser = _HTMLTextExtractor()
    parser.feed(prepared)
    parser.close()

    text = html.unescape(parser.get_text())
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    lines = [line.strip() for line in text.split("\n")]
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


class RawJob(BaseModel):
    source: str
    external_id: str | None = None
    title: str
    company: str
    url: str
    location_raw: str = ""
    description_text: str = ""
    salary_raw: str | None = None
    published_at: datetime | None = None


class BaseSource(ABC):
    name: str

    @abstractmethod
    def fetch(self) -> list[RawJob]:
        raise NotImplementedError
