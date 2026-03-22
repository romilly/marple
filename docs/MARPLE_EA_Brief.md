# Implementation Brief: `$:error:ea` and `$:error:en` for MARPLE

## Summary

Add two features:

1. **`$:error:ea`** — a dyadic function that tries to evaluate the right argument (a character vector containing an APL expression); if it fails, evaluates the left argument instead. Execution continues either way.

2. **`$:error:en`** — a niladic function returning the error number of the most recent error in the current session, or 0 if no error has occurred.

Together these give MARPLE APL-level error handling: `ea` prevents errors from halting execution, and `en` lets code inspect what went wrong.

## Motivation

MARPLE needs a way to verify that expressions produce expected errors without halting execution. This is essential for:

- **APL-level test scripts** that assert specific error codes from specific expressions
- **Application code** that needs to attempt an operation and handle failure gracefully

Currently all MARPLE errors raise Python exceptions that propagate up and terminate evaluation. There is no APL-level mechanism to catch them.

## `$:error:ea` — Execute Alternate

`$:error:ea` is a **dyadic** function. Both arguments are character vectors containing APL expressions.

- The **right** argument expression is evaluated first
- If it succeeds, its result is returned
- If it fails, the error number is recorded (accessible via `en`) and the **left** argument expression is evaluated instead; its result is returned

`ea` is implemented as a standard library function in the `$:error` namespace, using an i-beam to call Python. It executes expressions in the current workspace scope.

```apl
#import $:error:ea as ea
#import $:error:en as en

⍝ Right expression succeeds — its result is returned
'0' ea '2+3'                ⍝ → 5

⍝ Right expression fails — left expression is evaluated instead
'0' ea '1÷0'                ⍝ → 0
en                           ⍝ → 11 (DOMAIN ERROR)

⍝ Left expression can reference en
'en' ea '1÷0'               ⍝ → 11
```

`ea` catches all MARPLE APL errors. It does not catch `KeyboardInterrupt`, `SystemExit`, or non-MARPLE Python exceptions.

## `$:error:en` — Error Number

`$:error:en` is a **niladic** function. It returns the integer error code of the most recent error, or 0 if no error has occurred in the current session. The error number is set whenever an error occurs — whether caught by `ea` or not. A successful `ea` evaluation does not reset it.

`en` is implemented in the `$:error` namespace using an i-beam, the same as `ea`.

```apl
#import $:error:en as en

en                           ⍝ → 0 (fresh session)
'0' ea '1÷0'
en                           ⍝ → 11
'0' ea '2+3'                ⍝ succeeds — en is NOT reset
en                           ⍝ → 11 (still the last error)
```

## Usage in test scripts

```apl
#import $:error:ea as ea
#import $:error:en as en

⍝ Test that an expression produces the expected error
'en' ea '1÷0'               ⍝ → 11 (DOMAIN ERROR)
'en' ea '10⌷⍳5'             ⍝ → 3  (INDEX ERROR)
'en' ea '1 2+1 2 3'         ⍝ → 5  (LENGTH ERROR)

⍝ Test that an expression succeeds
'en' ea '2+3'               ⍝ → 5  (the result of 2+3)

⍝ A test helper for error-expected tests:
expect ← {'en' ea ⍵}
11 = expect '1÷0'           ⍝ 1
 3 = expect '10⌷⍳5'         ⍝ 1
```

## File structure

```
stdlib/
  error/
    ea.apl                    ← thin APL wrapper (dfn calling i-beam)
    en.apl                    ← thin APL wrapper (dfn calling i-beam)

src/marple/stdlib/
  error_impl.py               ← Python implementation of ea and en
```

## Testing

Add pytest tests covering:

- `ea` returns the right expression's result on success
- `ea` evaluates and returns the left expression on failure
- `en` returns the correct error code after a caught error
- `en` returns 0 in a fresh session
- `en` is not reset by a successful `ea` call
- `ea` works with each error type (DOMAIN, INDEX, RANK, LENGTH, SYNTAX, VALUE)
- `'en' ea 'expr'` returns the error code directly
