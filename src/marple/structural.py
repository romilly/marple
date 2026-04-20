from typing import Any

from marple.ports.array import APLArray, S
from marple.numpy_aplarray import NumpyAPLArray
from marple.backend_functions import (
    char_fill, get_char_dtype, np_repeat, np_reshape,
)
from marple.errors import DomainError, IndexError_, LengthError, RankError
from marple.get_numpy import np


def encode(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊤: represent ω in the number system given by α.

    Per ISO/Dyalog "Representation": both operands must be simple
    numeric arrays. Result shape is (⍴α),⍴ω — α dimensions FIRST,
    then ω dimensions.

    For higher-rank α, the radix vectors are the vectors along α's
    FIRST axis (so for an (n,k) matrix α, the k columns are k
    independent radix systems each of length n).

    A radix of 0 means "fully represent the remaining carry": the
    digit at that position is the entire carry, and the carry
    becomes 0 for any earlier positions.

    If ω exceeds the system's range, the result is the residue
    (×/X)|Y per the spec. This falls out naturally from the modular
    arithmetic.
    """
    if alpha.is_char() or omega.is_char():
        raise DomainError("⊤ is not defined on character data")

    a = alpha.data
    o = omega.data

    # Treat 0-d α as length-1 along an implicit single radix axis,
    # but track the original shape for the result.
    a_atleast = np.atleast_1d(a)
    n = a_atleast.shape[0]                    # the radix axis
    other_a_dims = a_atleast.shape[1:]        # axes after the radix axis

    # Result shape per spec: (⍴α),⍴ω
    result_shape = list(a.shape) + list(o.shape)

    # Choose an output dtype that accommodates both operands. For
    # int+int the result stays int; for any float input it becomes
    # float (so float ω is preserved).
    out_dtype = np.result_type(a_atleast.dtype, o.dtype)

    # Empty radix axis → empty result.
    if n == 0:
        return NumpyAPLArray(result_shape,
                        np.zeros(tuple(result_shape), dtype=out_dtype))

    # Carry shape: one carry per (radix-system, ω-value) pair.
    # That is: prepend the "other α dims" to the ω shape.
    carry_shape = other_a_dims + o.shape
    carry = np.broadcast_to(o, carry_shape).astype(out_dtype)

    # Output buffer: (n,) + carry_shape, in the same dtype.
    out = np.empty((n,) + carry_shape, dtype=out_dtype)

    # Walk the radix axis from last (least significant) to first.
    # At each position, peel off one digit and update the carry.
    # `view_shape` reshapes a single radix slice so it broadcasts
    # naturally against the carry across the ω axes.
    view_shape = other_a_dims + (1,) * len(o.shape)
    for i in range(n - 1, -1, -1):
        radix_i = a_atleast[i].reshape(view_shape)
        zero_mask = (radix_i == 0)
        # Avoid div-by-zero in the unused branch via a safe replacement.
        safe_radix = np.where(zero_mask, 1, radix_i)
        digit = np.where(zero_mask, carry, carry % safe_radix)
        carry = np.where(zero_mask, np.zeros_like(carry), carry // safe_radix)
        out[i] = digit

    return NumpyAPLArray(result_shape, out)


def decode(alpha: APLArray, omega: APLArray) -> APLArray:
    """Dyadic ⊥: evaluate ω as a polynomial with bases from α.

    Per ISO/Dyalog "Base Value": the last axis of α and the first
    axis of ω are the digit axis. They must agree in length, OR one
    of them must be a length-1 axis that extends to match the other,
    OR one or both operands may be scalars.

    Result shape is `(¯1↓⍴α),(1↓⍴ω)` — the digit axis is consumed.

    The "first element of α has no effect on the result" rule from
    the spec falls out naturally because the weights vector is built
    from `α[1:]` followed by 1, never using `α[0]`.
    """
    if alpha.is_char() or omega.is_char():
        raise DomainError("⊥ is not defined on character data")

    a = alpha.data
    o = omega.data

    # Treat 0-d operands as length-1 along an implicit single axis.
    a_atleast = np.atleast_1d(a)
    o_atleast = np.atleast_1d(o)

    a_n = a_atleast.shape[-1]   # length of α's last axis (digit axis)
    o_n = o_atleast.shape[0]    # length of ω's first axis (digit axis)

    # Result shape (the digit axis is consumed on each side).
    a_outer = list(a.shape[:-1]) if len(a.shape) >= 1 else []
    o_outer = list(o.shape[1:]) if len(o.shape) >= 1 else []
    result_shape = a_outer + o_outer

    # Empty digit axis on either side → empty polynomial → 0.
    if a_n == 0 or o_n == 0:
        return NumpyAPLArray(result_shape,
                        np.zeros(tuple(result_shape) or (), dtype=a.dtype))

    # Conformability: equal lengths, or one is length 1 (extends).
    if a_n != o_n and a_n != 1 and o_n != 1:
        raise LengthError(f"⊥ length mismatch: {a_n} vs {o_n}")
    n = max(a_n, o_n)

    # Broadcast both digit axes to common length n. The non-digit
    # axes of α (everything before the last) and ω (everything after
    # the first) are preserved unchanged.
    a_view = np.broadcast_to(a_atleast, a_atleast.shape[:-1] + (n,))
    o_view = np.broadcast_to(o_atleast, (n,) + o_atleast.shape[1:])

    # Weights along the digit axis: drop the first element of α,
    # append a trailing 1, then cumulative product from the right.
    # For α = [b1, b2, ..., bn], weights = [b2·b3·...·bn, ..., bn, 1].
    ones_tail = np.ones(a_view.shape[:-1] + (1,), dtype=a_view.dtype)
    shifted = np.concatenate([a_view[..., 1:], ones_tail], axis=-1)
    weights = np.flip(np.cumprod(np.flip(shifted, axis=-1), axis=-1), axis=-1)

    # Matrix product: contracts α's last axis with ω's first axis.
    result = weights @ o_view

    return NumpyAPLArray(result_shape, result)


