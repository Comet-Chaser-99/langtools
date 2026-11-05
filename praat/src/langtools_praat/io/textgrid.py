"""Independent full/short TextGrid text codec based on the public format manual.

https://praat.org/manual/TextGrid_file_formats.html
Labels/decorative indices are comments. Payload is ordered string/number/flag tokens.
"""

import math
import re
from dataclasses import dataclass
from pathlib import Path

from ..errors import InvalidInput
from ..model.textgrid import Interval, IntervalTier, Point, PointTier, TextGrid
from .atomic import save_bytes

NUMBER = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\Z")


@dataclass(frozen=True)
class Limits:
    max_bytes: int = 32 * 1024 * 1024
    max_tiers: int = 10_000
    max_entities: int = 1_000_000
    max_string: int = 1_000_000


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    offset: int


DEFAULT_LIMITS = Limits()


def fail(message: str, text: str, offset: int) -> InvalidInput:
    prefix = text[:offset].replace("\r\n", "\n").replace("\r", "\n")
    line = prefix.count("\n") + 1
    column = len(prefix) - prefix.rfind("\n")
    return InvalidInput(f"TextGrid line {line}, column {column}: {message}")


def scan(text: str, limits: Limits):
    i, size = 0, len(text)
    while i < size:
        char = text[i]
        if char.isspace():
            i += 1
            continue
        if char == "!":
            while i < size and text[i] not in "\r\n":
                i += 1
            continue
        start = i
        if char == '"':
            i += 1
            content = []
            length = 0
            while i < size:
                if text[i] == '"':
                    i += 1
                    if i < size and text[i] == '"':
                        content.append('"')
                        length += 1
                        i += 1
                    else:
                        break
                else:
                    content.append(text[i])
                    length += 1
                    i += 1
                if length > limits.max_string:
                    raise fail("String exceeds configured limit.", text, start)
            else:
                raise fail("Unterminated quoted string.", text, start)
            if i < size and not text[i].isspace():
                raise fail("Quoted value must be followed by whitespace.", text, i)
            yield Token("string", "".join(content), start)
        else:
            while i < size and not text[i].isspace():
                i += 1
            word = text[start:i]
            if NUMBER.fullmatch(word):
                yield Token("number", word, start)
            elif word in ("<exists>", "<absent>"):
                yield Token("flag", word, start)
            elif word.lower() in ("nan", "inf", "+inf", "-inf", "infinity"):
                raise fail("Nonfinite numeric value.", text, start)
            # Everything else is a descriptive label or index, not payload.


def loads(
    data: bytes | str, *, name: str = "untitled", limits: Limits = DEFAULT_LIMITS
) -> TextGrid:
    if isinstance(data, bytes):
        if len(data) > limits.max_bytes:
            raise InvalidInput("TextGrid exceeds configured byte limit.")
        if data.startswith(b"ooBinaryFile"):
            raise InvalidInput("Binary TextGrid is unsupported; export a text TextGrid first.")
        encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
        try:
            text = data.decode(encoding)
        except UnicodeError as error:
            raise InvalidInput("Expected UTF-8 or BOM-marked UTF-16 TextGrid.") from error
    else:
        if len(data.encode("utf-8")) > limits.max_bytes:
            raise InvalidInput("TextGrid exceeds configured byte limit.")
        text = data
    tokens = iter(scan(text, limits))

    def take(kind: str) -> Token:
        token = next(tokens, None)
        if token is None:
            raise fail(f"Unexpected end; expected {kind}.", text, len(text))
        if token.kind != kind:
            raise fail(f"Expected {kind}, got {token.kind}.", text, token.offset)
        return token

    def string() -> str:
        return take("string").value

    def number() -> float:
        token = take("number")
        value = float(token.value)
        if not math.isfinite(value):
            raise fail("Number must be finite.", text, token.offset)
        return value

    def count(limit: int) -> int:
        value = number()
        if value < 0 or not value.is_integer() or value > limit:
            raise InvalidInput(f"TextGrid count must be an integer between 0 and {limit}.")
        return int(value)

    if string() not in ("ooTextFile", "ooTextFile short"):
        raise InvalidInput("Unsupported TextGrid text header.")
    if string() != "TextGrid":
        raise InvalidInput("Expected TextGrid object class.")
    xmin, xmax = number(), number()
    flag = take("flag").value
    tier_count = count(limits.max_tiers) if flag == "<exists>" else 0
    tiers = []
    remaining = limits.max_entities
    for _ in range(tier_count):
        kind, tier_name = string(), string()
        lower, upper = number(), number()
        if kind not in ("IntervalTier", "TextTier"):
            raise InvalidInput(f"Unsupported tier class: {kind}")
        entity_count = count(remaining)
        remaining -= entity_count
        if kind == "IntervalTier":
            intervals = tuple(Interval(number(), number(), string()) for _ in range(entity_count))
            tiers.append(IntervalTier(tier_name, lower, upper, intervals))
        else:
            points = tuple(Point(number(), string()) for _ in range(entity_count))
            tiers.append(PointTier(tier_name, lower, upper, points))
    extra = next(tokens, None)
    if extra is not None:
        raise fail("Unexpected payload after the declared tiers.", text, extra.offset)
    return TextGrid(name, xmin, xmax, tuple(tiers))


def dumps(grid: TextGrid, *, short: bool = False) -> str:
    def quote(value: str) -> str:
        return '"' + value.replace('"', '""') + '"'

    def real(value: float) -> str:
        return repr(float(value))

    lines = ['File type = "ooTextFile"', 'Object class = "TextGrid"', ""]

    def emit(label: str, value: str, indent: str = "") -> None:
        lines.append(value if short else f"{indent}{label} = {value}")

    emit("xmin", real(grid.xmin))
    emit("xmax", real(grid.xmax))
    lines.append("<exists>" if short else "tiers? <exists>")
    emit("size", str(len(grid.tiers)))
    if not short:
        lines.append("item []:")
    for index, tier in enumerate(grid.tiers, 1):
        if not short:
            lines.append(f"    item [{index}]:")
        emit(
            "class",
            quote("IntervalTier" if isinstance(tier, IntervalTier) else "TextTier"),
            "        ",
        )
        emit("name", quote(tier.name), "        ")
        emit("xmin", real(tier.xmin), "        ")
        emit("xmax", real(tier.xmax), "        ")
        entities = tier.intervals if isinstance(tier, IntervalTier) else tier.points
        noun = "intervals" if isinstance(tier, IntervalTier) else "points"
        emit(f"{noun}: size", str(len(entities)), "        ")
        for item_index, item in enumerate(entities, 1):
            if not short:
                lines.append(f"        {noun} [{item_index}]:")
            if isinstance(item, Interval):
                emit("xmin", real(item.xmin), "            ")
                emit("xmax", real(item.xmax), "            ")
                emit("text", quote(item.label), "            ")
            else:
                emit("number", real(item.time), "            ")
                emit("mark", quote(item.label), "            ")
    return "\n".join(lines) + "\n"


def read(path: Path, *, limits: Limits = DEFAULT_LIMITS) -> TextGrid:
    path = Path(path)
    with path.open("rb") as stream:
        data = stream.read(limits.max_bytes + 1)
    return loads(data, name=path.stem, limits=limits)


def write(path: Path, grid: TextGrid, *, short: bool = False, overwrite: bool = False) -> None:
    save_bytes(Path(path), dumps(grid, short=short).encode("utf-8"), overwrite=overwrite)
