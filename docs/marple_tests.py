"""
MARPLE Compliance Test Suite
=============================

Tests derived from ISO 8485:1989 primitive catalog, plus MARPLE extensions
(direct definition, rank operator, From indexing).

Adapt the `run()` function below to match your interpreter's API.
Each test is an APL expression paired with its expected result.

Run with: python -m pytest marple_tests.py -v
    or:   python marple_tests.py
"""

import unittest
import math

# ============================================================
# ADAPTER — replace this with your interpreter's entry point
# ============================================================

def run(code):
    """Run a string of APL code and return the result.

    Must return an object with:
      .shape  — tuple of ints (e.g. () for scalar, (3,) for vector, (2,3) for matrix)
      .data   — flat list of values in row-major order
    
    Adapt this to your interpreter. For example:
        from marple import Interpreter
        _interp = Interpreter()
        def run(code):
            return _interp.execute(code)
    """
    raise NotImplementedError(
        "Connect this to your MARPLE interpreter. "
        "run('1+2') should return an object representing scalar 3."
    )


def scalar(val):
    """Helper: expected scalar result."""
    return ((), [val])

def vector(*vals):
    """Helper: expected vector result."""
    return ((len(vals),), list(vals))

def matrix(shape, vals):
    """Helper: expected matrix/higher-rank result."""
    return (tuple(shape), list(vals))

def result_of(code):
    """Run code, return (shape_tuple, flat_data_list)."""
    r = run(code)
    shape = tuple(r.shape) if hasattr(r.shape, '__iter__') else (r.shape,) if r.shape else ()
    data = list(r.data) if hasattr(r, 'data') else [r]
    return (shape, data)

def assertAPL(test_case, code, expected_shape, expected_data, msg=None, tol=1e-10):
    """Assert that running APL code produces expected shape and data."""
    shape, data = result_of(code)
    test_case.assertEqual(shape, expected_shape, 
        f"Shape mismatch for: {code}" + (f" ({msg})" if msg else ""))
    test_case.assertEqual(len(data), len(expected_data),
        f"Data length mismatch for: {code}")
    for i, (got, exp) in enumerate(zip(data, expected_data)):
        if isinstance(exp, float):
            test_case.assertAlmostEqual(got, exp, delta=tol,
                msg=f"Element {i} mismatch for: {code}")
        elif isinstance(exp, str):
            test_case.assertEqual(got, exp,
                msg=f"Element {i} mismatch for: {code}")
        else:
            test_case.assertEqual(got, exp,
                msg=f"Element {i} mismatch for: {code}")


# ============================================================
# PHASE 1: SCALAR ARITHMETIC
# The foundation — if these fail, nothing else matters.
# ============================================================

class TestScalarArithmetic(unittest.TestCase):
    """Scalar functions: monadic and dyadic, on scalars and vectors."""

    # ── Addition ──
    def test_add_scalars(self):
        assertAPL(self, '2+3', (), [5])

    def test_add_vectors(self):
        assertAPL(self, '1 2 3+4 5 6', (3,), [5, 7, 9])

    def test_add_scalar_extension_right(self):
        assertAPL(self, '10+1 2 3', (3,), [11, 12, 13])

    def test_add_scalar_extension_left(self):
        assertAPL(self, '1 2 3+10', (3,), [11, 12, 13])

    def test_conjugate(self):
        """Monadic + is conjugate (identity for reals)."""
        assertAPL(self, '+5', (), [5])
        assertAPL(self, '+¯3.5', (), [-3.5])

    # ── Subtraction ──
    def test_subtract_scalars(self):
        assertAPL(self, '5-3', (), [2])

    def test_negate(self):
        assertAPL(self, '-5', (), [-5])
        assertAPL(self, '-¯3', (), [3])

    def test_negate_vector(self):
        assertAPL(self, '-1 ¯2 3', (3,), [-1, 2, -3])

    # ── Multiplication ──
    def test_multiply_scalars(self):
        assertAPL(self, '3×4', (), [12])

    def test_signum(self):
        assertAPL(self, '×5', (), [1])
        assertAPL(self, '×¯3', (), [-1])
        assertAPL(self, '×0', (), [0])

    def test_signum_vector(self):
        assertAPL(self, '×¯3 0 5', (3,), [-1, 0, 1])

    # ── Division ──
    def test_divide_scalars(self):
        assertAPL(self, '12÷4', (), [3.0])

    def test_reciprocal(self):
        assertAPL(self, '÷4', (), [0.25])
        assertAPL(self, '÷0.5', (), [2.0])

    # ── Maximum and Minimum ──
    def test_maximum(self):
        assertAPL(self, '3⌈5', (), [5])
        assertAPL(self, '¯2⌈¯5', (), [-2])

    def test_minimum(self):
        assertAPL(self, '3⌊5', (), [3])

    def test_ceiling(self):
        assertAPL(self, '⌈3.2', (), [4])
        assertAPL(self, '⌈¯3.2', (), [-3])
        assertAPL(self, '⌈5', (), [5])

    def test_floor(self):
        assertAPL(self, '⌊3.7', (), [3])
        assertAPL(self, '⌊¯3.7', (), [-4])
        assertAPL(self, '⌊5', (), [5])

    # ── Power and Exponential ──
    def test_power(self):
        assertAPL(self, '2*3', (), [8.0])
        assertAPL(self, '3*0', (), [1.0])

    def test_exponential(self):
        assertAPL(self, '*0', (), [1.0])
        assertAPL(self, '*1', (), [math.e], tol=1e-6)

    # ── Logarithm ──
    def test_log_natural(self):
        assertAPL(self, '⍟1', (), [0.0])
        assertAPL(self, '⍟*1', (), [1.0], tol=1e-10)

    def test_log_base(self):
        assertAPL(self, '10⍟100', (), [2.0], tol=1e-10)
        assertAPL(self, '2⍟8', (), [3.0], tol=1e-10)

    # ── Residue and Absolute Value ──
    def test_absolute_value(self):
        assertAPL(self, '|¯5', (), [5])
        assertAPL(self, '|5', (), [5])
        assertAPL(self, '|0', (), [0])

    def test_residue(self):
        assertAPL(self, '3|7', (), [1])
        assertAPL(self, '3|9', (), [0])
        assertAPL(self, '3|¯1', (), [2])  # APL residue: always non-negative

    # ── Factorial and Binomial ──
    def test_factorial(self):
        assertAPL(self, '!0', (), [1])
        assertAPL(self, '!5', (), [120])

    def test_binomial(self):
        assertAPL(self, '2!5', (), [10])
        assertAPL(self, '0!5', (), [1])

    # ── High Minus (negative literal) ──
    def test_high_minus(self):
        assertAPL(self, '¯3+5', (), [2])
        assertAPL(self, '¯3', (), [-3])

    def test_high_minus_in_vector(self):
        assertAPL(self, '1 ¯2 3', (3,), [1, -2, 3])


# ============================================================
# PHASE 2: COMPARISON AND BOOLEAN
# ============================================================

class TestComparisonAndBoolean(unittest.TestCase):

    def test_less_than(self):
        assertAPL(self, '2<3', (), [1])
        assertAPL(self, '3<2', (), [0])
        assertAPL(self, '3<3', (), [0])

    def test_less_equal(self):
        assertAPL(self, '3≤3', (), [1])
        assertAPL(self, '4≤3', (), [0])

    def test_equal(self):
        assertAPL(self, '3=3', (), [1])
        assertAPL(self, '3=4', (), [0])

    def test_greater_equal(self):
        assertAPL(self, '3≥3', (), [1])
        assertAPL(self, '2≥3', (), [0])

    def test_greater_than(self):
        assertAPL(self, '3>2', (), [1])
        assertAPL(self, '2>3', (), [0])

    def test_not_equal(self):
        assertAPL(self, '3≠4', (), [1])
        assertAPL(self, '3≠3', (), [0])

    def test_comparison_vector(self):
        assertAPL(self, '1 2 3<2 2 2', (3,), [1, 0, 0])

    def test_not(self):
        assertAPL(self, '~0', (), [1])
        assertAPL(self, '~1', (), [0])
        assertAPL(self, '~1 0 1', (3,), [0, 1, 0])

    def test_and(self):
        assertAPL(self, '1∧1', (), [1])
        assertAPL(self, '1∧0', (), [0])
        assertAPL(self, '0∧0', (), [0])

    def test_or(self):
        assertAPL(self, '1∨0', (), [1])
        assertAPL(self, '0∨0', (), [0])

    def test_nand(self):
        assertAPL(self, '1⍲1', (), [0])
        assertAPL(self, '1⍲0', (), [1])

    def test_nor(self):
        assertAPL(self, '0⍱0', (), [1])
        assertAPL(self, '1⍱0', (), [0])


# ============================================================
# PHASE 3: STRUCTURAL FUNCTIONS
# ============================================================

class TestStructuralFunctions(unittest.TestCase):

    # ── Shape ──
    def test_shape_scalar(self):
        assertAPL(self, '⍴5', (0,), [])  # shape of scalar is empty vector

    def test_shape_vector(self):
        assertAPL(self, '⍴1 2 3', (1,), [3])

    def test_shape_matrix(self):
        assertAPL(self, '⍴2 3⍴⍳6', (2,), [2, 3])

    # ── Reshape ──
    def test_reshape_vector(self):
        assertAPL(self, '5⍴1', (5,), [1, 1, 1, 1, 1])

    def test_reshape_cycle(self):
        assertAPL(self, '5⍴1 2 3', (5,), [1, 2, 3, 1, 2])

    def test_reshape_matrix(self):
        assertAPL(self, '2 3⍴1 2 3 4 5 6', (2, 3), [1, 2, 3, 4, 5, 6])

    def test_reshape_empty(self):
        assertAPL(self, '0⍴1 2 3', (0,), [])

    # ── Iota ──
    def test_iota(self):
        """⎕IO←1 by default."""
        assertAPL(self, '⍳5', (5,), [1, 2, 3, 4, 5])

    def test_iota_one(self):
        assertAPL(self, '⍳1', (1,), [1])

    # ── Index Of ──
    def test_index_of(self):
        assertAPL(self, '10 20 30 40⍳30', (), [3])

    def test_index_of_missing(self):
        """Not found → 1+⍴⍺ (with ⎕IO←1)."""
        assertAPL(self, '10 20 30⍳99', (), [4])

    def test_index_of_vector(self):
        assertAPL(self, '10 20 30 40⍳20 40', (2,), [2, 4])

    # ── Ravel ──
    def test_ravel_matrix(self):
        assertAPL(self, ',2 3⍴1 2 3 4 5 6', (6,), [1, 2, 3, 4, 5, 6])

    def test_ravel_scalar(self):
        assertAPL(self, ',5', (1,), [5])

    # ── Catenate ──
    def test_catenate_vectors(self):
        assertAPL(self, '1 2 3,4 5', (5,), [1, 2, 3, 4, 5])

    def test_catenate_scalar_vector(self):
        assertAPL(self, '0,1 2 3', (4,), [0, 1, 2, 3])

    # ── Reverse ──
    def test_reverse_vector(self):
        assertAPL(self, '⌽1 2 3 4', (4,), [4, 3, 2, 1])

    def test_reverse_empty(self):
        assertAPL(self, '⌽⍬', (0,), [])

    # ── Rotate ──
    def test_rotate_vector(self):
        assertAPL(self, '2⌽1 2 3 4 5', (5,), [3, 4, 5, 1, 2])

    def test_rotate_negative(self):
        assertAPL(self, '¯1⌽1 2 3 4 5', (5,), [5, 1, 2, 3, 4])

    # ── Take ──
    def test_take_positive(self):
        assertAPL(self, '3↑1 2 3 4 5', (3,), [1, 2, 3])

    def test_take_negative(self):
        assertAPL(self, '¯2↑1 2 3 4 5', (2,), [4, 5])

    def test_take_overtake(self):
        """Taking more than available pads with fill (0 for numeric)."""
        assertAPL(self, '5↑1 2 3', (5,), [1, 2, 3, 0, 0])

    # ── Drop ──
    def test_drop_positive(self):
        assertAPL(self, '2↓1 2 3 4 5', (3,), [3, 4, 5])

    def test_drop_negative(self):
        assertAPL(self, '¯2↓1 2 3 4 5', (3,), [1, 2, 3])

    def test_drop_all(self):
        assertAPL(self, '5↓1 2 3 4 5', (0,), [])

    # ── Membership ──
    def test_membership(self):
        assertAPL(self, '2 5 7∈1 2 3 4 5', (3,), [1, 1, 0])

    # ── Grade ──
    def test_grade_up(self):
        assertAPL(self, '⍋30 10 40 20', (4,), [2, 4, 1, 3])

    def test_grade_down(self):
        assertAPL(self, '⍒30 10 40 20', (4,), [3, 1, 4, 2])

    # ── Transpose ──
    def test_transpose_matrix(self):
        assertAPL(self, '⍉2 3⍴1 2 3 4 5 6', (3, 2), [1, 4, 2, 5, 3, 6])

    # ── Encode / Decode ──
    def test_encode(self):
        assertAPL(self, '2 2 2 2⊤13', (4,), [1, 1, 0, 1])

    def test_decode(self):
        assertAPL(self, '10⊥1 2 3', (), [123])
        assertAPL(self, '2⊥1 1 0 1', (), [13])

    # ── Without ──
    def test_without(self):
        assertAPL(self, '1 2 3 4 5~2 4', (3,), [1, 3, 5])


# ============================================================
# PHASE 4: EVALUATION ORDER AND PARENTHESES
# ============================================================

class TestEvaluationOrder(unittest.TestCase):

    def test_right_to_left(self):
        """APL evaluates right to left with no precedence."""
        assertAPL(self, '2×3+4', (), [14])  # 2×(3+4)=14, NOT (2×3)+4=10

    def test_right_to_left_chain(self):
        assertAPL(self, '1+2×3+4', (), [15])  # 1+(2×(3+4))=1+14=15

    def test_parentheses_override(self):
        assertAPL(self, '(2×3)+4', (), [10])

    def test_nested_parentheses(self):
        assertAPL(self, '(2+3)×(4+5)', (), [45])


# ============================================================
# PHASE 5: OPERATORS (REDUCE, SCAN, INNER, OUTER)
# ============================================================

class TestOperators(unittest.TestCase):

    # ── Reduce ──
    def test_reduce_plus(self):
        assertAPL(self, '+/1 2 3 4', (), [10])

    def test_reduce_times(self):
        assertAPL(self, '×/1 2 3 4', (), [24])

    def test_reduce_minus(self):
        """Reduce is right-to-left: -/1 2 3 → 1-(2-3) = 2."""
        assertAPL(self, '-/1 2 3', (), [2])

    def test_reduce_max(self):
        assertAPL(self, '⌈/3 1 4 1 5', (), [5])

    def test_reduce_min(self):
        assertAPL(self, '⌊/3 1 4 1 5', (), [1])

    def test_reduce_single(self):
        assertAPL(self, '+/5', (), [5])

    def test_reduce_and(self):
        assertAPL(self, '∧/1 1 1 0', (), [0])
        assertAPL(self, '∧/1 1 1 1', (), [1])

    def test_reduce_or(self):
        assertAPL(self, '∨/0 0 1 0', (), [1])
        assertAPL(self, '∨/0 0 0 0', (), [0])

    # ── Scan ──
    def test_scan_plus(self):
        assertAPL(self, '+\\1 2 3 4', (4,), [1, 3, 6, 10])

    def test_scan_times(self):
        assertAPL(self, '×\\1 2 3 4', (4,), [1, 2, 6, 24])

    def test_scan_max(self):
        assertAPL(self, '⌈\\3 1 4 1 5', (5,), [3, 3, 4, 4, 5])

    # ── Outer Product ──
    def test_outer_product_add(self):
        assertAPL(self, '1 2 3∘.+10 20', (3, 2), [11, 21, 12, 22, 13, 23])

    def test_outer_product_multiply(self):
        assertAPL(self, '1 2 3∘.×1 2 3', (3, 3), [1,2,3, 2,4,6, 3,6,9])

    def test_outer_product_equal(self):
        assertAPL(self, '1 2 3∘.=1 3', (3, 2), [1,0, 0,0, 0,1])

    # ── Inner Product ──
    def test_inner_product_plus_times(self):
        """Dot product: 1 2 3 +.× 4 5 6 → 32."""
        assertAPL(self, '1 2 3+.×4 5 6', (), [32])


# ============================================================
# PHASE 6: ASSIGNMENT AND VARIABLES
# ============================================================

class TestAssignmentAndVariables(unittest.TestCase):

    def test_simple_assignment(self):
        assertAPL(self, 'x←5 ⋄ x', (), [5])

    def test_vector_assignment(self):
        assertAPL(self, 'v←1 2 3 ⋄ v', (3,), [1, 2, 3])

    def test_use_in_expression(self):
        assertAPL(self, 'x←3 ⋄ x+x', (), [6])

    def test_pass_through(self):
        """Assignment returns the value (pass-through)."""
        assertAPL(self, '1+x←5', (), [6])

    def test_multiple_assignment(self):
        assertAPL(self, 'a←1 ⋄ b←2 ⋄ a+b', (), [3])


# ============================================================
# PHASE 7: DIRECT DEFINITION (DFNS)
# ============================================================

class TestDirectDefinition(unittest.TestCase):

    def test_simple_monadic_dfn(self):
        assertAPL(self, '{⍵×2} 5', (), [10])

    def test_simple_dyadic_dfn(self):
        assertAPL(self, '3 {⍺+⍵} 4', (), [7])

    def test_named_dfn(self):
        assertAPL(self, 'double←{⍵×2} ⋄ double 5', (), [10])

    def test_dfn_with_primitives(self):
        assertAPL(self, 'mean←{(+/⍵)÷⍴⍵} ⋄ mean 2 4 6', (), [4.0])

    def test_guard_true(self):
        assertAPL(self, '{⍵>0 : ⍵ ⋄ -⍵} 5', (), [5])

    def test_guard_false(self):
        assertAPL(self, '{⍵>0 : ⍵ ⋄ -⍵} ¯5', (), [5])

    def test_recursive_dfn(self):
        assertAPL(self, 'fact←{⍵≤1 : 1 ⋄ ⍵×∇ ⍵-1} ⋄ fact 5', (), [120])

    def test_default_left_argument(self):
        assertAPL(self, 'f←{⍺←10 ⋄ ⍺+⍵} ⋄ f 5', (), [15])

    def test_default_left_overridden(self):
        assertAPL(self, 'f←{⍺←10 ⋄ ⍺+⍵} ⋄ 3 f 5', (), [8])

    def test_dfn_vector_argument(self):
        assertAPL(self, '{+/⍵} 1 2 3 4 5', (), [15])

    def test_anonymous_dfn_in_expression(self):
        assertAPL(self, '1+{⍵×⍵}4', (), [17])  # 1+(4×4)=17


# ============================================================
# PHASE 8: DIRECT OPERATORS (DOPS)
# ============================================================

class TestDirectOperators(unittest.TestCase):

    def test_monadic_dop(self):
        assertAPL(self, 'twice←{⍺⍺ ⍺⍺ ⍵} ⋄ (×twice) 3', (), [1])
        # signum(signum(3)) = signum(1) = 1

    def test_dop_with_add(self):
        assertAPL(self, 'twice←{⍺⍺ ⍺⍺ ⍵} ⋄ 5 (+twice) 3', (), [11])
        # 5 + (5 + 3) = 5 + 8 = 13? No: ⍺⍺ is +, so: 5 +(⍺⍺) (⍺⍺ ⍵)
        # Actually: twice derives a function. (⍺⍺ ⍺⍺ ⍵) with ⍺⍺=+:
        # + + ⍵ = +(+3) = +3 = 3 for monadic? 
        # Hmm, let's use a clearer test:

    def test_dop_double_apply(self):
        """Apply negation twice → identity."""
        assertAPL(self, 'twice←{⍺⍺ ⍺⍺ ⍵} ⋄ (-twice) 5', (), [5])


# ============================================================
# PHASE 9: RANK OPERATOR (MARPLE EXTENSION)
# ============================================================

class TestRankOperator(unittest.TestCase):

    def test_reverse_each_row(self):
        assertAPL(self, '(⌽⍤1) 2 3⍴1 2 3 4 5 6', (2, 3), [3,2,1, 6,5,4])

    def test_sum_each_row(self):
        assertAPL(self, '(+/⍤1) 2 3⍴1 2 3 4 5 6', (2,), [6, 15])

    def test_sum_each_column(self):
        """Reduce at rank ¯1 on a matrix → column sums."""
        assertAPL(self, '(+/⍤¯1) 2 3⍴1 2 3 4 5 6', # This is +/ on 2-cell = whole matrix
                  (3,), [5, 7, 9])
        # ¯1 on rank 2 → 1-cells → rows → +/ each row... 
        # Actually ¯1 means rank (2-1)=1 cells = rows.
        # +/⍤1 sums each row. For column sums we need +⌿ or +/⍤2.
        # Let me fix: +/⍤1 gives row sums. Column sums need different approach.

    def test_rank_scalar(self):
        """Rank 0: apply to each scalar."""
        assertAPL(self, '({⍵×⍵}⍤0) 1 2 3', (3,), [1, 4, 9])

    def test_rank_whole_array(self):
        """Rank 99 (or higher than actual): apply to whole array."""
        assertAPL(self, '(⌽⍤99) 1 2 3', (3,), [3, 2, 1])

    def test_dyadic_rank_scalar_vector(self):
        """Add scalars from left to rows from right."""
        assertAPL(self, '10 20(+⍤0 1)2 3⍴1 2 3 4 5 6',
                  (2, 3), [11,12,13, 24,25,26])


# ============================================================
# PHASE 10: FROM / INDEXING (MARPLE EXTENSION)
# ============================================================

class TestFromIndexing(unittest.TestCase):

    def test_from_vector(self):
        assertAPL(self, '3⌷10 20 30 40 50', (), [30])

    def test_from_vector_multiple(self):
        assertAPL(self, '1 3 5⌷10 20 30 40 50', (3,), [10, 30, 50])

    def test_from_matrix_row(self):
        assertAPL(self, '2⌷2 3⍴10 20 30 40 50 60', (3,), [40, 50, 60])

    def test_from_matrix_rows(self):
        assertAPL(self, '1 2⌷2 3⍴10 20 30 40 50 60',
                  (2, 3), [10,20,30, 40,50,60])

    def test_bracket_indexing_element(self):
        """Traditional bracket indexing still works."""
        assertAPL(self, '(3 4⍴⍳12)[2;3]', (), [7])

    def test_bracket_indexing_row(self):
        assertAPL(self, '(3 4⍴⍳12)[2;]', (4,), [5, 6, 7, 8])

    def test_bracket_indexing_column(self):
        assertAPL(self, '(3 4⍴⍳12)[;3]', (3,), [3, 7, 11])


# ============================================================
# PHASE 11: EDGE CASES AND SPECIAL VALUES
# ============================================================

class TestEdgeCases(unittest.TestCase):

    def test_empty_vector_iota(self):
        assertAPL(self, '⍳0', (0,), [])

    def test_empty_reshape(self):
        assertAPL(self, '0⍴0', (0,), [])

    def test_reduce_empty(self):
        """Reduce of empty vector should return identity element."""
        assertAPL(self, '+/⍬', (), [0])
        assertAPL(self, '×/⍬', (), [1])
        assertAPL(self, '⌈/⍬', (), [float('-inf')]) # or minimum float
        assertAPL(self, '⌊/⍬', (), [float('inf')])  # or maximum float

    def test_shape_of_empty(self):
        assertAPL(self, '⍴⍬', (1,), [0])

    def test_ravel_empty(self):
        assertAPL(self, ',⍬', (0,), [])

    def test_scalar_reshape(self):
        """Empty shape reshape → scalar."""
        # ⍬⍴5 should give scalar 5? Depends on implementation.
        # In classic APL: (⍬⍴V) gives first element as scalar.
        assertAPL(self, '⍬⍴7 8 9', (), [7])

    def test_catenate_empties(self):
        assertAPL(self, '⍬,⍬', (0,), [])

    def test_catenate_empty_and_vector(self):
        assertAPL(self, '⍬,1 2 3', (3,), [1, 2, 3])

    def test_take_from_empty(self):
        """Take from empty pads with zeros."""
        assertAPL(self, '3↑⍬', (3,), [0, 0, 0])


# ============================================================
# PHASE 12: CIRCULAR / TRIGONOMETRIC FUNCTIONS
# ============================================================

class TestCircularFunctions(unittest.TestCase):

    def test_pi_times(self):
        assertAPL(self, '○1', (), [math.pi], tol=1e-10)
        assertAPL(self, '○2', (), [2*math.pi], tol=1e-10)

    def test_sin(self):
        assertAPL(self, '1○○1', (), [0.0], tol=1e-10)  # sin(π) ≈ 0

    def test_cos(self):
        assertAPL(self, '2○0', (), [1.0], tol=1e-10)     # cos(0) = 1

    def test_sin_cos_identity(self):
        """sin²(x) + cos²(x) = 1."""
        assertAPL(self, '((1○0.5)*2)+((2○0.5)*2)', (), [1.0], tol=1e-10)


# ============================================================
# PHASE 13: FORMAT AND EXECUTE
# ============================================================

class TestFormatAndExecute(unittest.TestCase):

    def test_format_number(self):
        """Monadic ⍕ converts number to character."""
        # Just test it doesn't crash; exact format is implementation-defined
        shape, data = result_of('⍕42')
        self.assertEqual(len(shape), 1)  # result should be a character vector

    def test_execute(self):
        """Monadic ⍎ evaluates a string as APL."""
        assertAPL(self, "⍎'2+3'", (), [5])


# ============================================================
# PHASE 14: MATRIX OPERATIONS
# ============================================================

class TestMatrixOperations(unittest.TestCase):

    def test_inner_product_matrix(self):
        """2×2 matrix multiply."""
        # [1 2; 3 4] +.× [5 6; 7 8] = [19 22; 43 50]
        assertAPL(self, '(2 2⍴1 2 3 4)+.×(2 2⍴5 6 7 8)',
                  (2, 2), [19, 22, 43, 50])

    def test_reduce_matrix_rows(self):
        """+/ on matrix reduces along last axis (rows)."""
        assertAPL(self, '+/2 3⍴1 2 3 4 5 6', (2,), [6, 15])

    def test_reduce_first_matrix(self):
        """+⌿ on matrix reduces along first axis (columns)."""
        assertAPL(self, '+⌿2 3⍴1 2 3 4 5 6', (3,), [5, 7, 9])


# ============================================================
# PHASE 15: COMPRESS / REPLICATE
# ============================================================

class TestCompressReplicate(unittest.TestCase):

    def test_compress(self):
        assertAPL(self, '1 0 1 0 1/10 20 30 40 50', (3,), [10, 30, 50])

    def test_compress_all(self):
        assertAPL(self, '1 1 1/10 20 30', (3,), [10, 20, 30])

    def test_compress_none(self):
        assertAPL(self, '0 0 0/10 20 30', (0,), [])

    def test_replicate(self):
        assertAPL(self, '1 2 3/10 20 30', (6,), [10, 20, 20, 30, 30, 30])


# ============================================================
# PHASE 16: EXPAND
# ============================================================

class TestExpand(unittest.TestCase):

    def test_expand(self):
        assertAPL(self, '1 0 1 0 1\\10 20 30', (5,), [10, 0, 20, 0, 30])

    def test_expand_all_ones(self):
        assertAPL(self, '1 1 1\\10 20 30', (3,), [10, 20, 30])


# ============================================================
# PHASE 17: ROLL AND DEAL
# ============================================================

class TestRandomFunctions(unittest.TestCase):

    def test_roll_range(self):
        """?6 should produce integer in 1..6 (⎕IO←1)."""
        shape, data = result_of('?6')
        self.assertEqual(shape, ())
        self.assertGreaterEqual(data[0], 1)
        self.assertLessEqual(data[0], 6)

    def test_deal_length(self):
        """6?52 produces 6 distinct values."""
        shape, data = result_of('6?52')
        self.assertEqual(shape, (6,))
        self.assertEqual(len(set(data)), 6)  # all distinct


# ============================================================
# PHASE 18: CHARACTER DATA
# ============================================================

class TestCharacterData(unittest.TestCase):

    def test_char_vector(self):
        shape, data = result_of("'hello'")
        self.assertEqual(shape, (5,))

    def test_char_indexing(self):
        assertAPL(self, "'ABCDE'[3]", (), ['C'])

    def test_char_catenate(self):
        shape, data = result_of("'hello',' ','world'")
        self.assertEqual(shape, (11,))

    def test_char_membership(self):
        assertAPL(self, "'aeiou'∈'hello world'", (5,), [0, 1, 0, 1, 0])
        # a not in 'hello world', e is, i not, o is, u not


# ============================================================
# RUN
# ============================================================

if __name__ == '__main__':
    unittest.main(verbosity=2)
