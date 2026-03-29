"""Partition function tests — Bob Smith's techniques."""

from marple.arraymodel import APLArray, S
from marple.engine import Interpreter


def _load_partfns(i: Interpreter) -> None:
    """Load the partition workspace into the interpreter."""
    from marple.workspace import load_workspace
    load_workspace(i.env, "workspaces/partfns", evaluate=i.run)


def _iv(data: list[int]) -> APLArray:
    return APLArray([len(data)], data)


class TestNDelta:
    def test_ne_first_in_runs(self) -> None:
        i = Interpreter(io=1)
        _load_partfns(i)
        i.run("B←0 0 1 1 1 0 0 1 1 1 0 0 0 1 0 1")
        result = i.run("(≠ N∆) B")
        assert result == _iv([0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1])

    def test_minus_first_differences(self) -> None:
        i = Interpreter(io=1)
        _load_partfns(i)
        result = i.run("(- N∆) 1 3 6 10 15")
        assert result == _iv([1, 2, 3, 4, 5])

    def test_eq_first_in_zero_runs(self) -> None:
        i = Interpreter(io=1)
        _load_partfns(i)
        i.run("B←0 0 1 1 1 0 0 1 1 1 0 0 0 1 0 1")
        result = i.run("(= N∆) B")
        assert result == _iv([0, 1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0, 0])


class TestPDelta:
    def test_ne_last_in_runs(self) -> None:
        i = Interpreter(io=1)
        _load_partfns(i)
        i.run("B←0 0 1 1 1 0 0 1 1 1 0 0 0 1 0 1")
        result = i.run("(≠ P∆) B")
        assert result == _iv([0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 1])


class TestIdentities:
    def test_ne_ndelta_scan_inverse(self) -> None:
        """(≠ N∆) and ≠\\ are inverses."""
        i = Interpreter(io=1)
        _load_partfns(i)
        i.run("B←1 0 1 1 0 1 0 0 1 1")
        assert i.run("≠\\(≠ N∆) B") == i.run("B")

    def test_minus_ndelta_plus_scan_inverse(self) -> None:
        """(- N∆) and +\\ are inverses."""
        i = Interpreter(io=1)
        _load_partfns(i)
        i.run("V←1 3 6 10 15")
        assert i.run("+\\(- N∆) V") == i.run("V")


class TestPartitionFunctions:
    """Test partition functions with standard test data from the document."""

    def _setup(self) -> Interpreter:
        i = Interpreter(io=1)
        _load_partfns(i)
        i.run("P←1 0 0 1 1 0 0 0 1 0")
        i.run("V←1 2 3 4 5 6 7 8 9 10")
        i.run("B←1 0 1 0 1 0 1 0 1 0")
        return i

    def test_pplred(self) -> None:
        i = self._setup()
        result = i.run("P pplred V")
        assert result == _iv([6, 4, 26, 19])

    def test_pplscan(self) -> None:
        i = self._setup()
        result = i.run("P pplscan V")
        assert result == _iv([1, 3, 6, 4, 5, 11, 18, 26, 9, 19])

    def test_pnescan(self) -> None:
        i = self._setup()
        result = i.run("P pnescan B")
        assert result == _iv([1, 1, 0, 0, 1, 1, 0, 0, 1, 1])

    def test_porscan(self) -> None:
        i = self._setup()
        result = i.run("P porscan B")
        assert result == _iv([1, 1, 1, 0, 1, 1, 1, 1, 1, 1])

    def test_pandscan(self) -> None:
        i = self._setup()
        result = i.run("P pandscan B")
        assert result == _iv([1, 0, 0, 0, 1, 0, 0, 0, 1, 0])

    def test_preverse(self) -> None:
        i = self._setup()
        result = i.run("P preverse V")
        assert result == _iv([3, 2, 1, 4, 8, 7, 6, 5, 10, 9])
