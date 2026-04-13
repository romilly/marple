"""Convert APLArray to HTML for Jupyter rich display."""

import html as _html

from marple.numpy_array import APLArray
from marple.formatting import format_num
from marple.backend_functions import NDArray, chars_to_str, is_char_array

ARRAY_CSS = """<style>
.apl-array {
    border-collapse: collapse;
    font-family: 'APL385 Unicode', 'DejaVu Sans Mono', monospace;
    margin: 4px 0;
}
.apl-array td {
    border: 1px solid #ddd;
    padding: 2px 8px;
    text-align: right;
    white-space: nowrap;
}
.apl-array .char-cell { text-align: left; }
.apl-array tr:nth-child(even) { background: #f7f7f7; }
.apl-slice {
    margin: 6px 0;
    padding-left: 10px;
    border-left: 3px solid #4a86c8;
}
.apl-slice-label {
    color: #888;
    font-size: 0.85em;
    font-family: 'APL385 Unicode', 'DejaVu Sans Mono', monospace;
}
</style>"""


def _is_char_data(data: NDArray) -> bool:
    return is_char_array(data)


def _cell_html(value: object, is_char: bool) -> str:
    if isinstance(value, str):
        return f'<td class="char-cell">{_html.escape(value)}</td>'
    return f'<td>{_html.escape(format_num(value))}</td>'


def aplarray_to_html(arr: APLArray) -> str:
    """Convert an APLArray to an HTML representation."""
    is_char = _is_char_data(arr.data)

    # Scalar
    if arr.shape == []:
        val = arr.data.item()
        text = _html.escape(str(val) if isinstance(val, str) else format_num(val))
        return f'<span class="apl-scalar">{text}</span>'

    # Vector
    if len(arr.shape) == 1:
        if is_char:
            return f'<span class="apl-scalar">{_html.escape(chars_to_str(arr.data))}</span>'
        if len(arr.data) == 0:
            return '<table class="apl-array"><tr></tr></table>'
        cells = ''.join(_cell_html(v, is_char) for v in arr.data)
        return f'<table class="apl-array"><tr>{cells}</tr></table>'

    # Matrix
    if len(arr.shape) == 2:
        return _matrix_html(arr, is_char)

    # Rank 3+
    return _high_rank_html(arr, is_char)


def _matrix_html(arr: APLArray, is_char: bool) -> str:
    rows, cols = arr.shape
    flat = arr.data.flatten()
    html_rows = []
    for r in range(rows):
        cells = ''.join(
            _cell_html(flat[r * cols + c], is_char) for c in range(cols))
        html_rows.append(f'<tr>{cells}</tr>')
    return f'<table class="apl-array">{"".join(html_rows)}</table>'


def _high_rank_html(arr: APLArray, is_char: bool) -> str:
    outer = arr.shape[0]
    inner_shape = arr.shape[1:]
    slices = []
    for i in range(outer):
        sub_data = arr.data[i]
        sub = APLArray(list(inner_shape), sub_data)
        inner_html = aplarray_to_html(sub)
        slices.append(
            f'<div class="apl-slice">'
            f'<span class="apl-slice-label">[{i + 1}]</span>'
            f'{inner_html}</div>')
    return ''.join(slices)
