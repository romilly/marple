"""End-to-end tests for MARPLE running on a Raspberry Pi Pico 2.

These tests send APL expressions over USB serial and verify the results.
They require a Pico connected with MARPLE deployed.

Run with: pytest tests/pico/ -m pico --pico-port /dev/ttyACM0
Skip with: pytest -m 'not pico'
"""

import pytest

pytestmark = pytest.mark.pico


class TestPicoArithmetic:
    def test_addition(self, pico):
        assert pico.eval("2+3") == "5"

    def test_subtraction(self, pico):
        assert pico.eval("10-4") == "6"

    def test_multiplication(self, pico):
        assert pico.eval("3×7") == "21"

    def test_division(self, pico):
        assert pico.eval("15÷5") == "3"

    def test_high_minus(self, pico):
        assert pico.eval("¯3+5") == "2"

    def test_right_to_left(self, pico):
        assert pico.eval("1+2×3") == "7"


class TestPicoVectors:
    def test_iota(self, pico):
        assert pico.eval("⍳5") == "1 2 3 4 5"

    def test_vector_add(self, pico):
        assert pico.eval("1 2 3+10 20 30") == "11 22 33"

    def test_scalar_extension(self, pico):
        assert pico.eval("10×⍳5") == "10 20 30 40 50"

    def test_shape(self, pico):
        assert pico.eval("⍴ 1 2 3 4 5") == "5"

    def test_reverse(self, pico):
        assert pico.eval("⌽ 1 2 3 4 5") == "5 4 3 2 1"


class TestPicoReduce:
    def test_sum(self, pico):
        assert pico.eval("+/⍳100") == "5050"

    def test_product(self, pico):
        assert pico.eval("×/⍳6") == "720"

    def test_scan(self, pico):
        assert pico.eval("+\\1 2 3 4 5") == "1 3 6 10 15"


class TestPicoMatrices:
    def test_reshape(self, pico):
        result = pico.eval("2 3⍴⍳6")
        assert result == "1 2 3\n4 5 6"

    def test_matrix_reduce(self, pico):
        pico.eval_silent("M←2 3⍴⍳6")
        assert pico.eval("+/M") == "6 15"

    def test_transpose(self, pico):
        pico.eval_silent("M←2 3⍴⍳6")
        result = pico.eval("⍉M")
        assert result == "1 4\n2 5\n3 6"


class TestPicoDfns:
    def test_simple_dfn(self, pico):
        assert pico.eval("{⍵+⍵} 21") == "42"

    def test_named_dfn(self, pico):
        pico.eval_silent("double←{⍵+⍵}")
        assert pico.eval("double 7") == "14"

    def test_guard(self, pico):
        pico.eval_silent("sign←{⍵>0:1 ⋄ ⍵<0:¯1 ⋄ 0}")
        assert pico.eval("sign 42") == "1"
        assert pico.eval("sign ¯7") == "¯1"
        assert pico.eval("sign 0") == "0"

    @pytest.mark.skip(reason="Pico stack too small for non-TCO recursion")
    def test_recursion(self, pico):
        pico.eval_silent("fact←{⍵≤1:1 ⋄ ⍵×∇ ⍵-1}")
        assert pico.eval("fact 10") == "3628800"


class TestPicoRank:
    def test_reverse_rows(self, pico):
        pico.eval_silent("M←3 4⍴⍳12")
        result = pico.eval("(⌽⍤1) M")
        rows = [line.split() for line in result.strip().split("\n")]
        assert rows == [["4","3","2","1"],["8","7","6","5"],["12","11","10","9"]]

    def test_sum_rows(self, pico):
        pico.eval_silent("M←3 4⍴⍳12")
        assert pico.eval("(+/⍤1) M") == "10 26 42"


class TestPicoNamespaces:
    def test_str_upper(self, pico):
        assert pico.eval("$::str::upper 'hello'") == "HELLO"

    def test_str_lower(self, pico):
        assert pico.eval("$::str::lower 'MARPLE'") == "marple"

    def test_str_trim(self, pico):
        assert pico.eval("$::str::trim '  hi  '") == "hi"

    def test_import(self, pico):
        pico.eval_silent("#import $::str::upper")
        assert pico.eval("upper 'test'") == "TEST"

    def test_import_alias(self, pico):
        pico.eval_silent("#import $::str::lower as lc")
        assert pico.eval("lc 'LOUD'") == "loud"


class TestPicoFileIO:
    def test_write_and_read(self, pico):
        pico.eval_silent("'hello pico' ⎕NWRITE '/test_e2e.txt'")
        assert pico.eval("⎕NREAD '/test_e2e.txt'") == "hello pico"

    def test_write_read_round_trip(self, pico):
        pico.eval_silent("'one two three' ⎕NWRITE '/words_e2e.txt'")
        assert pico.eval("⎕NREAD '/words_e2e.txt'") == "one two three"

    def test_nexists(self, pico):
        pico.eval_silent("'test' ⎕NWRITE '/exists_e2e.txt'")
        assert pico.eval("⎕NEXISTS '/exists_e2e.txt'") == "1"
        pico.eval_silent("⎕NDELETE '/exists_e2e.txt'")
        assert pico.eval("⎕NEXISTS '/exists_e2e.txt'") == "0"


class TestPicoErrorHandling:
    def test_domain_error(self, pico):
        result = pico.eval("1÷0")
        assert "DOMAIN ERROR" in result

    def test_length_error(self, pico):
        result = pico.eval("1 2+1 2 3")
        assert "LENGTH ERROR" in result

    def test_ea(self, pico):
        assert pico.eval("'0' ⎕EA '1÷0'") == "0"


class TestPicoSystemVars:
    def test_ver(self, pico):
        result = pico.eval("⎕VER")
        assert "MARPLE" in result
        assert "rp2" in result

    def test_io(self, pico):
        assert pico.eval("⎕IO") == "1"

    def test_a(self, pico):
        assert pico.eval("⎕A") == "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def test_d(self, pico):
        assert pico.eval("⎕D") == "0123456789"

    def test_ts(self, pico):
        result = pico.eval("⍴⎕TS")
        assert result == "7"

    def test_ts_year(self, pico):
        result = pico.eval("1⌷⎕TS")
        year = int(result)
        assert 2020 <= year <= 2030


class TestPicoOuterProduct:
    def test_multiplication_table(self, pico):
        result = pico.eval("(⍳3)∘.×⍳3")
        assert result == "1 2 3\n2 4 6\n3 6 9"


class TestPicoIndexingShape:
    def test_vector_index(self, pico):
        pico.eval_silent("v←10 20 30 40 50")
        assert pico.eval("⍴v[2 4]") == "2"

    def test_matrix_index(self, pico):
        pico.eval_silent("v←10 20 30 40 50")
        assert pico.eval("⍴v[2 3⍴1 2 3 4 5 1]") == "2 3"

    # Pimoroni build limits ulab to 2 dimensions; standard ulab supports 4
    # def test_rank3_index(self, pico):
    #     pico.eval_silent("v←10 20 30 40")
    #     assert pico.eval("⍴v[2 2 2⍴1 2 3 4 1 2 3 4]") == "2 2 2"

    def test_outer_product_index(self, pico):
        pico.eval_silent("r←1 2 3")
        pico.eval_silent("s←1 2 3")
        assert pico.eval("⍴' *'[1+r∘.=s]") == "3 3"


class TestPicoReplicateExpand:
    """Replicate / and expand \\ on vectors and matrices.

    The desktop (CPython/numpy) implementation uses np.repeat, np.full,
    and fancy indexing (`result[..., one_positions] = source`). These
    are not used anywhere else in marple so they're untested under ulab.
    If these tests fail on the Pico, we'll need to fall back to a
    loop-based implementation (option B3 from the 2026-04-07 audit).
    """

    def test_replicate_vector(self, pico):
        assert pico.eval("1 0 1/1 2 3") == "1 3"

    def test_replicate_vector_multiplied(self, pico):
        assert pico.eval("2 3/1 2") == "1 1 2 2 2"

    def test_replicate_scalar_left(self, pico):
        assert pico.eval("3/1 2 3") == "1 1 1 2 2 2 3 3 3"

    def test_replicate_char_vector(self, pico):
        assert pico.eval("1 0 1/'ABC'") == "AC"

    def test_replicate_char_matrix(self, pico):
        # 2×3 char matrix, replicate cols with mask 1 0 1 → 2×2 matrix
        assert pico.eval("1 0 1/2 3⍴'ABCDEF'") == "AC\nDF"

    def test_replicate_first_char_matrix(self, pico):
        # 3×2 char matrix, replicate rows with mask 1 0 1 → 2×2 matrix
        assert pico.eval("1 0 1⌿3 2⍴'ABCDEF'") == "AB\nEF"

    def test_expand_vector(self, pico):
        assert pico.eval("1 0 1\\1 2") == "1 0 2"

    def test_expand_char_vector(self, pico):
        assert pico.eval("1 0 1\\'AC'") == "A C"

    def test_expand_char_matrix(self, pico):
        # 2×2 char matrix, expand cols with mask 1 0 1 → 2×3 matrix
        assert pico.eval("1 0 1\\2 2⍴'ABCD'") == "A B\nC D"


class TestPicoSystemCommands:
    def test_save_load_drop_and_lib(self, pico):
        pico.eval(")clear")
        pico.eval_silent("x←42")
        pico.eval(")wsid e2e_test")
        result = pico.eval(")save")
        assert "SAVED" in result
        # Clear and reload
        pico.eval(")clear")
        result = pico.eval(")lib")
        assert "e2e_test" in result
        result = pico.eval(")load e2e_test")
        assert "e2e_test" in result
        assert pico.eval("x") == "42"
        # Drop and verify it's gone
        result = pico.eval(")drop e2e_test")
        assert "DROPPED" in result
        result = pico.eval(")lib")
        assert "e2e_test" not in result
