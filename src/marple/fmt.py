"""Dyadic ⎕FMT format specification parsing and application for MARPLE."""

from typing import Any

from marple.numpy_array import APLArray, S
from marple.formatting import format_num
from marple.errors import DomainError


def _ljust(s: str, width: int) -> str:
    return s + " " * max(0, width - len(s))


def _rjust(s: str, width: int) -> str:
    return " " * max(0, width - len(s)) + s


class FmtGroup:
    """A format group: one data column's format, or a text insertion."""
    def __init__(self, code: str, width: int = 0, decimals: int = 0,
                 repeat: int = 1, text: str = "") -> None:
        self.code = code
        self.width = width
        self.decimals = decimals
        self.repeat = repeat
        self.text = text


def parse_fmt_spec(spec: str) -> list[FmtGroup]:
    """Parse a format specification string like 'I5,F8.2,⊂ => ⊃,5A1'."""
    groups: list[FmtGroup] = []
    i = 0
    while i < len(spec):
        if spec[i] in " ,":
            i += 1
            continue
        if spec[i] in ("⊂", "<"):
            close = "⊃" if spec[i] == "⊂" else ">"
            i += 1
            end = spec.index(close, i)
            groups.append(FmtGroup("TEXT", text=spec[i:end]))
            i = end + 1
            continue
        rep = 0
        while i < len(spec) and spec[i].isdigit():
            rep = rep * 10 + int(spec[i])
            i += 1
        if i >= len(spec):
            break
        code = spec[i].upper()
        if code not in "IFEAG":
            raise DomainError(f"Unknown format code: {spec[i]}")
        i += 1
        if code == "G" and i < len(spec) and spec[i] in ("⊂", "<"):
            close = "⊃" if spec[i] == "⊂" else ">"
            i += 1
            end = spec.index(close, i)
            pattern = spec[i:end]
            i = end + 1
            groups.append(FmtGroup("G", text=pattern, repeat=max(rep, 1)))
            continue
        width = 0
        while i < len(spec) and spec[i].isdigit():
            width = width * 10 + int(spec[i])
            i += 1
        decimals = 0
        if i < len(spec) and spec[i] == ".":
            i += 1
            while i < len(spec) and spec[i].isdigit():
                decimals = decimals * 10 + int(spec[i])
                i += 1
        if code == "F" and width > 0 and decimals > width - 2:
            raise DomainError(f"F format: decimals ({decimals}) > width-2 ({width - 2})")
        if code == "E" and width > 0 and decimals > width - 2:
            raise DomainError(f"E format: decimals ({decimals}) > width-2 ({width - 2})")
        groups.append(FmtGroup(code, width, decimals, max(rep, 1)))
    return groups


def format_one_value(code: str, width: int, decimals: int,
                     value: int | float | str | None) -> str:
    """Format a single value with a format code."""
    if value is None:
        return " " * width if width > 0 else ""
    if code == "A":
        text = value if isinstance(value, str) else str(value)
        return _ljust(text, width) if width > 0 else text
    num = float(value) if not isinstance(value, (int, float)) else value
    if code == "I":
        text = str(int(num))
    elif code == "F":
        text = f"{num:.{decimals}f}"
    elif code == "E":
        text = f"{num:.{decimals}E}"
    elif code == "G":
        text = format_num(num)
    else:
        text = str(num)
    text = text.replace("-", "¯")
    return _rjust(text, width) if width > 0 else text


def apply_g_pattern(pattern: str, value: int | float) -> str:
    """Apply a G-format pattern. '9' placeholders are filled with digits."""
    num = abs(int(float(value) if not isinstance(value, (int, float)) else value))
    digit_count = pattern.count("9")
    digits = str(num).zfill(digit_count)
    result: list[str] = []
    di = 0
    for ch in pattern:
        if ch == "9":
            result.append(digits[di] if di < len(digits) else "0")
            di += 1
        else:
            result.append(ch)
    return "".join(result)


def apply_group(group: FmtGroup, value: APLArray | None,
                row: int) -> str:
    """Apply a format group to one row of a column's data."""
    if group.code == "TEXT":
        return group.text
    if value is None:
        return " " * (group.width * group.repeat)
    is_char = (len(value.data) > 0 and isinstance(value.data[0], str))
    if group.code == "A" and not is_char:
        raise DomainError("A format requires character data")
    if group.code != "A" and is_char:
        raise DomainError(f"{group.code} format requires numeric data, got character")
    if group.code == "A":
        total_chars = group.repeat * group.width
        if len(value.shape) >= 2:
            cols = value.shape[1]
            start = row * cols
            if start >= len(value.data):
                return " " * total_chars
            row_chars = [str(c) for c in value.data[start:start + cols]]
        elif len(value.data) > 0 and isinstance(value.data[0], str):
            row_chars = [str(c) for c in value.data] if row == 0 else []
        else:
            row_chars = []
        while len(row_chars) < total_chars:
            row_chars.append(" ")
        parts: list[str] = []
        for r in range(group.repeat):
            ch = row_chars[r * group.width:(r + 1) * group.width]
            field = "".join(ch)
            parts.append(_ljust(field, group.width) if group.width > 0 else field)
        return "".join(parts)
    else:
        if len(value.shape) == 0:
            scalar = value.data[0] if row == 0 else None
        elif row < value.shape[0]:
            scalar = value.data[row]
        else:
            scalar = None
        if group.code == "G" and group.text:
            if scalar is None:
                return " " * len(group.text)
            return apply_g_pattern(group.text, scalar)
        return format_one_value(group.code, group.width, group.decimals,
                                scalar)


def column_row_count(value: APLArray, is_alpha: bool) -> int:
    """How many output rows does a column argument produce?"""
    if len(value.shape) == 0:
        return 1
    if len(value.shape) >= 2:
        return value.shape[0]
    if is_alpha and len(value.data) > 0 and isinstance(value.data[0], str):
        return 1
    return value.shape[0]


def dyadic_fmt(fmt_str: str, values: list[APLArray]) -> APLArray:
    """Dyadic ⎕FMT: format values according to specification."""
    groups = parse_fmt_spec(fmt_str)
    if not groups:
        raise DomainError("Empty format specification")
    template: list[tuple[FmtGroup, int | None]] = []
    group_idx = 0
    val_idx = 0
    while val_idx < len(values):
        g = groups[group_idx % len(groups)]
        group_idx += 1
        if g.code == "TEXT":
            template.append((g, None))
            continue
        template.append((g, val_idx))
        val_idx += 1
    while True:
        g = groups[group_idx % len(groups)]
        if g.code != "TEXT":
            break
        template.append((g, None))
        group_idx += 1
    num_rows = 1
    for g, vi in template:
        if vi is not None:
            num_rows = max(num_rows, column_row_count(values[vi], g.code == "A"))
    rows: list[str] = []
    for row_idx in range(num_rows):
        parts: list[str] = []
        for g, vi in template:
            v = values[vi] if vi is not None else None
            parts.append(apply_group(g, v, row_idx))
        rows.append("".join(parts))
    max_width = max(len(r) for r in rows) if rows else 0
    all_chars: list[object] = []
    for r in rows:
        all_chars.extend(list(_ljust(r, max_width)))
    return APLArray.array([len(rows), max_width], all_chars)
