"""HTML rendering tests for Jupyter output."""

from marple.arraymodel import APLArray, S
from marple.jupyter.html_render import aplarray_to_html


class TestScalar:
    def test_numeric(self) -> None:
        html = aplarray_to_html(S(42))
        assert '42' in html
        assert 'apl-scalar' in html

    def test_char(self) -> None:
        html = aplarray_to_html(APLArray([], ['A']))
        assert 'A' in html


class TestVector:
    def test_numeric(self) -> None:
        html = aplarray_to_html(APLArray([3], [1, 2, 3]))
        assert '<table' in html
        assert '<td>' in html
        assert html.count('<td>') == 3

    def test_char(self) -> None:
        html = aplarray_to_html(APLArray([5], list('hello')))
        assert 'hello' in html
        assert 'apl-scalar' in html

    def test_empty(self) -> None:
        html = aplarray_to_html(APLArray([0], []))
        assert '<table' in html


class TestMatrix:
    def test_numeric(self) -> None:
        html = aplarray_to_html(APLArray([2, 3], [1, 2, 3, 4, 5, 6]))
        assert '<table' in html
        assert html.count('<tr>') == 2
        assert html.count('<td>') == 6

    def test_char(self) -> None:
        html = aplarray_to_html(APLArray([2, 3], list('ABCDEF')))
        assert '<table' in html
        assert 'char-cell' in html


class TestRank3:
    def test_slices(self) -> None:
        html = aplarray_to_html(APLArray([2, 2, 3], list(range(12))))
        assert 'apl-slice' in html
        assert html.count('apl-slice-label') == 2
