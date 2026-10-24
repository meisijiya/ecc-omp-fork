#!/usr/bin/env python
"""Minimal frontmatter reader for the fork's markdown assets.

The fork ships plain markdown files whose YAML frontmatter omp reads:
skills carry `name` / `description`, agents carry `name` / `description` /
`tools`, rules carry `description`, commands carry `description`. A full YAML
parser is not part of the standard library and is not needed -- the
frontmatter in this repo only uses scalars, block scalars and simple lists.

What this module guarantees
  * Only the *first* `---` block is read. A `---` in the body (a markdown
    horizontal rule, a table separator, a setext underline) never turns into
    frontmatter, and a file without a closing `---` has no frontmatter at
    all.
  * Block scalars are folded the way YAML folds them: `>` / `>-` join the
    continuation lines with a space, `|` keeps the line breaks.
  * A key whose value is a nested mapping is ignored: the fork does not use
    them, and guessing their shape would be worse than skipping them.
  * Nothing raises on malformed input. A frontmatter that cannot be read
    yields the keys that could be read and nothing else.

Values are plain strings, or lists of strings for list values. Booleans are
*not* converted: `alwaysApply: true` is read as the string "true", so the
caller compares it case-insensitively if it cares about the type.
"""

from __future__ import annotations

import re

__all__ = [
    "split_frontmatter",
    "frontmatter_lines",
    "frontmatter_text",
    "key_lines",
    "parse_frontmatter",
    "read_meta_file",
]

# A frontmatter key: `name`, `argument-hint`, `metadata.origin`-style names.
RE_KEY = re.compile(r"^(?P<key>[A-Za-z0-9_][A-Za-z0-9_.-]*)\s*:(?P<rest>.*)$")
# A block scalar header: `>`, `>-`, `>+`, `|`, `|-`, `|+`, `>2`.
RE_BLOCK_SCALAR = re.compile(r"^[>|][+-]?\d*$")
# A YAML comment: a `#` that follows a space starts a comment.
RE_COMMENT = re.compile(r"\s+#.*$")


def _strip_bom(text):
    return text[1:] if text.startswith("\ufeff") else text


def split_frontmatter(text):
    """Split `text` into its frontmatter block and its body.

    Returns `(block, body)` where `block` is a list of `(lineno, line)`
    tuples (1-based line numbers into the original text) and `body` is the
    text behind the frontmatter. `block` is empty and `body` is the whole
    text when the file has no frontmatter.
    """
    if not text:
        return [], text or ""
    text = _strip_bom(text)
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != "---":
        return [], text

    end = None
    for idx in range(1, len(lines)):
        stripped = lines[idx].rstrip()
        if stripped == "---" or stripped == "...":
            end = idx
            break
    if end is None:
        # An unterminated block is not frontmatter -- treat the file as body.
        return [], text

    block = [(idx + 1, lines[idx].rstrip("\r")) for idx in range(1, end)]
    body = "\n".join(lines[end + 1:])
    return block, body


def frontmatter_lines(text):
    """The `(lineno, line)` tuples of the first frontmatter block."""
    return split_frontmatter(text)[0]


def frontmatter_text(text):
    """The raw text of the first frontmatter block ("" when there is none)."""
    block = split_frontmatter(text)[0]
    return "\n".join(line for _, line in block)


def key_lines(text):
    """Map every frontmatter key to the line numbers it appears on."""
    out = {}
    for lineno, line in frontmatter_lines(text):
        match = RE_KEY.match(line)
        if not match:
            continue
        out.setdefault(match.group("key"), []).append(lineno)
    return out


def _unquote(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def _strip_comment(value):
    """Drop a trailing YAML comment (` # ...`), keep a `#` inside a word."""
    return RE_COMMENT.sub("", value).strip()


def _split_inline_list(value):
    """`[a, b]` -> ["a", "b"]; an empty list -> []."""
    inner = value[1:-1].strip()
    if not inner:
        return []
    parts = [p.strip() for p in inner.split(",")]
    return [_unquote(p) for p in parts if p != ""]


def _fold_block(lines, style):
    """Fold the continuation lines of a block scalar."""
    items = [line.strip() for line in lines]
    while items and items[-1] == "":
        items.pop()
    if style.startswith("|"):
        return "\n".join(items)
    return " ".join(item for item in items if item)


def _parse_block(block):
    """Turn the frontmatter lines into a dict of values."""
    meta = {}
    idx = 0
    total = len(block)
    while idx < total:
        _, line = block[idx]
        idx += 1
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = RE_KEY.match(line)
        if not match:
            # Not a `key: value` line -- an orphan continuation or a
            # directive. Ignore it rather than guess.
            continue
        key = match.group("key")
        rest = match.group("rest").strip()

        if RE_BLOCK_SCALAR.match(rest):
            # A block scalar: every following line that is indented belongs
            # to it.
            body = []
            while idx < total:
                nxt = block[idx][1]
                if nxt.strip() == "":
                    body.append("")
                    idx += 1
                    continue
                if not nxt[:1].isspace():
                    break
                body.append(nxt.strip())
                idx += 1
            meta[key] = _fold_block(body, rest)
            continue

        if rest == "":
            # Either a nested mapping, a list, or an empty value. Look at
            # the indented lines below to tell them apart.
            children = []
            while idx < total:
                nxt = block[idx][1]
                if nxt.strip() == "":
                    idx += 1
                    continue
                if not nxt[:1].isspace():
                    break
                children.append(nxt)
                idx += 1
            if not children:
                meta[key] = ""
                continue
            items = []
            is_list = True
            for child in children:
                item = child.strip()
                if item == "-":
                    items.append("")
                elif item.startswith("- "):
                    items.append(_unquote(item[2:].strip()))
                else:
                    is_list = False
                    break
            if is_list:
                meta[key] = items
            # A nested mapping is not supported: the key is ignored.
            continue

        if rest.startswith("[") and rest.endswith("]"):
            meta[key] = _split_inline_list(rest)
            continue

        meta[key] = _unquote(_strip_comment(rest))

    return meta


def parse_frontmatter(text):
    """Parse the first frontmatter block of `text`.

    Returns `(meta, body)`: `meta` maps the frontmatter keys to their
    values (strings, or lists of strings), `body` is the text behind the
    frontmatter. A file without frontmatter yields `({}, text)`.
    """
    block, body = split_frontmatter(text)
    if not block:
        return {}, body
    return _parse_block(block), body


def read_meta_file(path):
    """Read a file and parse its frontmatter -> `(meta, body)`."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        return parse_frontmatter(handle.read())
