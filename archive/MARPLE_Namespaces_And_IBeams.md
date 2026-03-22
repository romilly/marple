# MARPLE Language Extension: Namespaces and I-Beams

## Workspace namespaces and Python FFI for MARPLE

*This document specifies two related extensions to MARPLE: a namespace system based on workspace subdirectories, and an i-beam mechanism for calling Python code from APL. Together they allow MARPLE's standard library to grow without expanding the interpreter core.*

---

## 1. Rationale

MARPLE's workspace is a directory of APL source files. As the language acquires utility functions — file I/O, string manipulation, date handling, HTTP, GPIO on the Pico — these need organisation. Dumping everything into a flat workspace doesn't scale. Equally, implementing every system facility as a quad-name (`⎕NREAD`, `⎕NPUT`, `⎕JSON`, ...) would litter the interpreter with special cases.

Two mechanisms solve this:

**Namespaces** organise functions into hierarchical groups mapped to subdirectories. A function `nread` in the `io` subdirectory is referenced as `io::nread`. A system workspace `$` is always available, so a standard library function is `$::io::nread`.

**I-beams** (`⌶`) provide a controlled foreign-function interface to Python. An APL function can call arbitrary Python code, so long as the Python callable accepts one or two `APLArray` arguments and returns an `APLArray`. This lets the standard library be written as thin APL wrappers around Python implementations, keeping the interpreter core small.

The two mechanisms are complementary: the standard library lives in the `$` namespace and its functions use i-beams internally to access Python capabilities.

---

## 2. Namespaces

### 2.1 Structure

A namespace is a subdirectory within a workspace directory. The directory name is the namespace name. Nesting is permitted: `math/linalg/` creates namespace `math::linalg`.

```
my_workspace/
  foo.apl              ⍝ top-level function foo
  bar.apl              ⍝ top-level function bar
  utils/
    trim.apl           ⍝ utils::trim
    pad.apl            ⍝ utils::pad
  math/
    stats/
      mean.apl         ⍝ math::stats::mean
      stddev.apl       ⍝ math::stats::stddev
```

Each `.apl` file defines one function or operator, just as in the existing workspace model. The filename (without extension) is the function name within its namespace.

### 2.2 Qualified names

A qualified name uses double colon (`::`) as the separator:

```apl
utils::trim ' hello '        ⍝ call trim from the utils namespace
math::stats::mean data        ⍝ call mean from math::stats
```

**Why double colon, not single colon or dot**: the dot (`.`) is already APL's inner-product operator. Single colon (`:`) conflicts with dfn guard syntax — guards can have an identifier on both sides (`x:y` means "if x, return y"), making `identifier:identifier` ambiguous. Double colon (`::`) is lexically unambiguous: it never appears in any other APL context, so `utils::trim` can be recognised by the tokenizer without context-dependent parsing.

**Parsing rule**: the tokenizer recognises `identifier::identifier` (and longer chains like `a::b::c`) as a single **qualified-name token**. The system workspace prefix `$` may appear at the start: `$::io::nread`.

### 2.3 The system workspace `$`

MARPLE provides a built-in system workspace whose root is referenced by `$`. It is always available, regardless of the current user workspace. Its contents are the standard library.

```apl
$::io::nread '/tmp/data.csv'
$::math::gcd 12 18
$::str::trim '  hello  '
```

`$` is a reserved identifier. It cannot be assigned or shadowed.

**Location on disk**: the system workspace directory is located relative to the MARPLE installation. The interpreter finds it via a known path (e.g. `<install>/stdlib/`). On the Pico, it would be a directory on the filesystem or frozen into the firmware.

**Lazy loading**: namespace contents are loaded on first reference, not at startup. `$::io::nread` triggers loading of `<stdlib>/io/nread.apl` (and any dependencies it declares) only when first called. Subsequent calls use the cached definition. This is essential for constrained platforms where RAM is limited.

### 2.4 Name resolution order

When an unqualified name `foo` is encountered:

1. **Local scope** — if inside a dfn, check local assignments and arguments (`⍺`, `⍵`, `⍺⍺`, `⍵⍵`)
2. **Current namespace** — the namespace of the file being executed (if any)
3. **Workspace root** — top-level definitions in the current workspace
4. **Imports** — names brought in by `#import` directives (see §2.5)
5. **Primitives** — built-in functions and operators

The system workspace `$` is **not** searched implicitly. You must either qualify (`$::io::nread`) or import (`#import $::io::nread as nread`). This avoids surprising name resolution and keeps the search path short.

### 2.5 Import directives

Import directives use `#` as a line prefix, placing them outside the normal APL expression grammar. They are declarations processed by the file loader and REPL before evaluation.

```apl
#import $::io::nread                ⍝ import as nread (leaf name)
#import $::io::nread as read        ⍝ import with alias
#import $::io                       ⍝ import namespace — use as io::nread
#import $::math::stats as stats     ⍝ import namespace with alias — use as stats::mean
```

**Syntax**:

```ebnf
import_directive := '#import' qualified_name [ 'as' identifier ] ;
qualified_name   := '$' '::' name_chain | name_chain ;
name_chain       := identifier ( '::' identifier )* ;
```

**Semantics**:

| Form | Effect |
|------|--------|
| `#import a::b::c` | Binds `c` in current scope to the function/operator at `a::b::c` |
| `#import a::b::c as x` | Binds `x` in current scope to the function/operator at `a::b::c` |
| `#import a::b` | Binds `b` as a namespace prefix — `b::c` resolves to `a::b::c` |
| `#import a::b as x` | Binds `x` as a namespace prefix — `x::c` resolves to `a::b::c` |

Import directives are valid at file scope and in the REPL. They are not valid inside dfns (use qualified names there).

**Circular imports**: if file A imports from namespace B and B imports from A, the interpreter raises a DEPENDENCY ERROR at load time. No lazy resolution, no partial loading — circular dependencies are prohibited. This is simple to implement and simple to reason about.

### 2.6 Workspace commands

Existing commands are extended:

| Command | Behaviour |
|---------|-----------|
| `)fns` | Lists functions in the current namespace (workspace root by default) |
| `)fns utils` | Lists functions in the `utils` namespace |
| `)fns $` | Lists top-level namespaces in the system workspace |
| `)fns $::io` | Lists functions in `$::io` |
| `)ns` | Shows the current namespace context |
| `)save` | Saves workspace including subdirectory structure |
| `)load` | Loads workspace including subdirectory structure |

---

## 3. I-Beams (`⌶`)

### 3.1 What i-beams are

In Dyalog APL, `⌶` (I-Beam, Unicode U+2336) provides access to system services via numeric codes: `8415⌶1` enables complex numbers, `819⌶'hello'` converts case, etc. The codes are deliberately opaque — I-Beam is Dyalog's escape hatch for experimental or system-level features.

MARPLE repurposes the glyph with a different and more transparent mechanism: `⌶` is a **dyadic operator** that takes a string left operand (a Python callable path) and produces a derived function that calls that Python code.

### 3.2 Syntax

```apl
(⌶'module.function') Y          ⍝ monadic: call Python function with one APLArray arg
X (⌶'module.function') Y        ⍝ dyadic: call Python function with two APLArray args
```

`⌶` is a **monadic operator** (one operand, on the left). The operand is a character vector (string) identifying a Python callable using dotted module path notation.

In ASCII fallback, MARPLE accepts `I:` as an alternative spelling.

### 3.3 The Python callable contract

Any Python function referenced by `⌶` must satisfy this contract:

```python
from marple.arraymodel import APLArray

# Monadic: one APLArray argument, returns APLArray
def my_function(right: APLArray) -> APLArray:
    ...

# Dyadic: two APLArray arguments, returns APLArray
def my_function(left: APLArray, right: APLArray) -> APLArray:
    ...
```

The interpreter determines monadic vs. dyadic dispatch based on the valence of the call site (whether a left argument is present), not by inspecting the Python function's signature. If a monadic call is made but the Python function requires two arguments, Python raises a `TypeError`, which MARPLE catches and reports as a DOMAIN ERROR.

**Return value**: the Python function must return an `APLArray`. If it returns `None` or a non-APLArray value, MARPLE raises a DOMAIN ERROR.

**Exceptions**: any Python exception raised during execution is caught and reported as a DOMAIN ERROR with the Python exception message included in the error text.

### 3.4 Module resolution

The string operand is resolved using Python's standard `importlib` machinery:

1. Split the string on `.` to get module path and callable name
2. Import the module via `importlib.import_module()`
3. Retrieve the callable via `getattr()`
4. Cache the resolved callable for subsequent calls

```apl
⍝ Resolves to: from marple.stdlib.io import nread; nread(right)
(⌶'marple.stdlib.io.nread') '/tmp/data.csv'
```

The module must be importable from the Python environment where MARPLE is running. For the standard library, modules live under `marple.stdlib.*`. Third-party or user modules work if they're on `sys.path`.

### 3.5 Example: building `$::io::nread`

The standard library function `$::io::nread` would be defined in `<stdlib>/io/nread.apl`:

```apl
⍝ nread: read a text file, return a character vector with embedded newlines
⍝ Usage: $::io::nread '/path/to/file'
{(⌶'marple.stdlib.io_impl.nread') ⍵}
```

The Python implementation in `marple/stdlib/io_impl.py`:

```python
from marple.arraymodel import APLArray

def nread(right: APLArray) -> APLArray:
    """Read a text file. Right arg is a character vector (filepath).
    Returns a character vector with embedded newline characters."""
    path = ''.join(right.data)  # APLArray of chars → Python string
    with open(path, 'r') as f:
        text = f.read()
    chars = list(text)
    return APLArray((len(chars),), chars) if chars else APLArray((0,), [])
```

This pattern — thin APL wrapper, Python implementation — keeps the APL layer composable (the dfn can be passed to operators, used in expressions, etc.) while the heavy lifting happens in Python.

### 3.6 Composability

Because `⌶` produces an ordinary derived function, it composes with operators:

```apl
readfile ← ⌶'marple.stdlib.io_impl.nread'

readfile '/tmp/data.csv'              ⍝ direct call
(readfile⍤0) file_list                ⍝ read each file in a vector of filenames
                                      ⍝ (if filenames were boxed — future)
```

It can be assigned, passed as an operand, and used anywhere a function is expected.

### 3.7 Security

Calling arbitrary Python code is powerful and potentially dangerous. MARPLE addresses this pragmatically:

**Default: unrestricted.** On a desktop, MARPLE trusts the user. Any importable Python module can be called via `⌶`. This matches the threat model: if you can run MARPLE, you can run Python directly.

**Optional allowlist.** A configuration setting `MARPLE_IBEAM_ALLOW` can restrict which module prefixes are permitted:

```
MARPLE_IBEAM_ALLOW=marple.stdlib,myproject.utils
```

When set, only callables under the listed prefixes are resolved. Attempts to call other modules raise a SECURITY ERROR. When unset, all modules are allowed.

**On constrained platforms**: CircuitPython has no `importlib`. The Pico build will need a static registry of i-beam callables compiled into the firmware. This is a platform-specific concern handled in the backend layer, not in the language spec.

---

## 4. Grammar additions

### 4.1 Tokenizer changes

The tokenizer gains two new token types:

**Qualified name**: a sequence of identifiers separated by double colons, optionally starting with `$::`.

```ebnf
qualified_name := [ '$' '::' ] identifier ( '::' identifier )* ;
```

**Import directive**: a line beginning with `#import`.

```ebnf
import_line := '#import' ws qualified_name [ ws 'as' ws identifier ] ;
```

Import lines are consumed by the loader/REPL before the line reaches the parser.

### 4.2 Parser changes

The parser must handle qualified names wherever an identifier (function name or variable name) currently appears. A qualified name resolves through the namespace lookup chain rather than the local/global scope chain.

### 4.3 Operator addition

`⌶` is added as a monadic operator:

```ebnf
mop := '¨' | '⌶' ;    ⍝ (¨ is reserved for future Each; ⌶ is i-beam)
```

The operand must be a character vector (string). The derived function is monadic or dyadic depending on call-site valence.

---

## 5. Implementation guidance

### 5.1 Namespace implementation

The `workspace.py` module currently handles flat workspace directories. Changes needed:

1. **Recursive directory walking**: on `)load`, walk subdirectories to discover namespaces. Build a tree structure mapping qualified names to file paths. Do not load file contents — just build the directory index.

2. **Lazy loading**: when a qualified name is evaluated and the function is not yet loaded, load and evaluate the `.apl` file at that point. Cache the resulting definition in the namespace tree.

3. **Namespace object**: add a `Namespace` class (or dictionary-based equivalent) that holds name→value mappings. The workspace root is a `Namespace`. Each subdirectory is a child `Namespace`. The system workspace `$` is a separate `Namespace` tree loaded from the stdlib directory.

4. **Tokenizer update**: modify the tokenizer to detect `identifier::identifier` chains and emit them as a single `QUALIFIED_NAME` token. The `::` sequence is lexically unambiguous — it never appears in any other APL context (single `:` is the guard separator in dfns).

5. **Import processing**: add an import-processing pass in `repl.py` (for interactive lines) and the file loader (for `.apl` files). Lines beginning with `#import` are parsed and recorded before the rest of the line/file is evaluated. Imported names are injected into the current scope.

6. **`)save` update**: when saving, preserve the subdirectory structure. Functions defined in a namespace are saved into the corresponding subdirectory.

### 5.2 I-beam implementation

1. **Operator registration**: add `⌶` to the operator table in `interpreter.py` as a monadic operator. The operand must evaluate to a character vector (flat `APLArray` of characters).

2. **Callable resolution**: implement a `resolve_ibeam(path_string)` function that uses `importlib` to find the Python callable. Cache resolved callables in a dictionary keyed by the path string.

3. **Derived function**: the derived function wraps the resolved callable. On monadic invocation, it calls `python_fn(right)`. On dyadic invocation, it calls `python_fn(left, right)`. It validates return types and converts Python exceptions to APL errors.

4. **Allowlist check**: if `MARPLE_IBEAM_ALLOW` is set, check the module prefix before importing. Raise SECURITY ERROR if disallowed.

5. **Testing**: i-beam functions are easy to test — write Python functions that operate on `APLArray` and verify round-trip behaviour. Test error cases: bad module paths, wrong return types, Python exceptions, allowlist violations.

### 5.3 Standard library bootstrap

The initial system workspace (`$`) should include at least:

| Namespace | Functions | Purpose |
|-----------|-----------|---------|
| `$::io` | `nread`, `nwrite`, `nexists`, `ndelete` | Native file I/O (vectors with embedded newlines) |
| `$::str` | `trim`, `split`, `join`, `upper`, `lower`, `u`, `v2m` | String utilities |
| `$::sys` | `argv`, `exit`, `env` | System access |

**`$::io::nread`** reads a text file and returns a character vector with embedded newline characters. **`$::io::nwrite`** accepts a character vector (with embedded newlines) and writes it to a file. This keeps I/O simple — a file is a vector of characters — and leaves the choice of how to structure the data (matrix, nested, etc.) to the caller.

**`$:str:u`** (unescape) takes a character vector containing escape sequences and returns the corresponding Unicode string. Recognised escapes: `\n` (newline), `\t` (tab), `\r` (carriage return), `\\` (literal backslash), `\uNNNN` (4-digit Unicode code point), `\UNNNNNNNN` (8-digit Unicode code point). Unrecognised escapes are an error. This solves the practical problem of entering special characters when the input method doesn't support them directly.

```apl
$::str::u 'line one\nline two'
⍝ → character vector with an embedded newline between the two parts

$::str::u 'caf\u00E9'
⍝ → 'café'

$::str::u 'tab\there'
⍝ → character vector with a tab character
```

**`$:str:v2m`** (vector to matrix) takes a character vector containing delimiter characters and splits it into a character matrix, one row per segment, padded on the right with spaces. Monadic: splits on newline (`\n`). Dyadic: the left argument is a character scalar or vector of delimiter characters.

```apl
$::str::v2m 'abc\ndef\nghij'         ⍝ error: this is literal backslash-n
$::str::v2m $::str::u 'abc\ndef\nghij'  ⍝ → 3 4 matrix, padded with spaces
⍝ abc
⍝ def
⍝ ghij

⍝ Typical file-reading pipeline:
$::str::v2m $::io::nread '/tmp/data.txt'
⍝ → character matrix, one row per line

⍝ Split on comma instead:
',' $::str::v2m 'alpha,beta,gamma'
⍝ → 3 5 matrix
⍝ alpha
⍝ beta
⍝ gamma
```

### 5.4 Pico considerations

On CircuitPython:
- `importlib` is not available. I-beam resolution must use a static registry: a dictionary mapping path strings to function references, populated at build time.
- The system workspace may be frozen into the firmware rather than read from the filesystem.
- Lazy loading is especially important — the Pico has ~264KB of RAM.

---

## 6. Complete example session

```apl
⍝ ── Using the system workspace directly ──
$::io::nread '/tmp/names.txt'
⍝ Returns a character vector with embedded newlines

⍝ ── The typical file-to-matrix pipeline ──
#import $::io::nread
#import $::str::v2m
#import $::str::u

v2m nread '/tmp/names.txt'
⍝ → character matrix, one row per line, space-padded

⍝ ── Escape sequences for special characters ──
u 'hello\tworld\n'
⍝ → character vector with tab and trailing newline

u 'caf\u00E9'
⍝ → 'café'

⍝ ── Splitting on custom delimiters ──
',' v2m 'red,green,blue'
⍝ → 3 5 matrix
⍝ red
⍝ green
⍝ blue

⍝ ── Importing with aliases ──
#import $::str::trim as strip
strip '  padded  '

⍝ ── Importing a whole namespace ──
#import $::math as m
m::gcd 12 18
⍝ → 6

⍝ ── User workspace with namespaces ──
)load myproject
)fns
⍝ main  run  config
)fns utils
⍝ clean  validate  transform

utils::clean raw_data
utils::validate cleaned

⍝ ── Defining a function that uses an i-beam directly ──
timestamp ← {(⌶'marple.stdlib.sys_impl.timestamp') ⍵}
timestamp 0    ⍝ returns current time as a numeric vector

⍝ ── I-beam in a more complex dfn ──
read_matrix ← {
    raw ← (⌶'marple.stdlib.io_impl.nread') ⍵
    ⍝ split into matrix, then further APL processing ...
    $::str::v2m raw
}

⍝ ── Composing i-beam-derived functions with operators ──
char_count ← {⍴(⌶'marple.stdlib.io_impl.nread') ⍵}
char_count '/tmp/data.csv'
⍝ → 1742  (character count including newlines)

⍝ ── Namespace in a saved workspace ──
)wsid myproject
)save
⍝ Saves:
⍝   myproject/
⍝     main.apl
⍝     utils/
⍝       clean.apl
⍝       validate.apl
```

---

## 7. Design decisions and alternatives considered

**Double colon separator.** Dot (`.`) was rejected because it's APL's inner-product operator. Single colon (`:`) was considered but conflicts with dfn guard syntax — guards can have an identifier on both sides (`x:y` means "if x, return y"), making `identifier:identifier` ambiguous without context. Double colon (`::`) is lexically unambiguous: it never appears in any other APL context, so `utils::trim` can be recognised by the tokenizer without context-dependent parsing.

**I-beam as operator vs. system function.** An alternative was `⎕FFI 'module.func' args` — a quad-name that takes a string and arguments. This was rejected because it doesn't compose: you can't pass `⎕FFI 'module.func'` as an operand or assign the partially-applied form. Making `⌶` an operator means `⌶'path'` is a first-class function value.

**Implicit `$` search vs. explicit import.** An alternative was to search `$` automatically for unqualified names. Rejected: implicit search makes name resolution unpredictable, risks shadowing, and complicates error messages. Explicit `#import` or `$::`-qualified names keep things clear.

**`#` prefix for directives.** APL doesn't use `#` for anything. The `#` prefix clearly marks lines as directives rather than APL expressions. An alternative was `)import` as a system command, but system commands are REPL-only by convention — they don't belong in source files. `#` directives work in both source files and the REPL.

---

## 8. References

- Ken Iverson. *A Dictionary of APL*. APL Quote Quad 18(1), September 1987.
- Dyalog APL — I-Beam: https://docs.dyalog.com/20.0/language-reference-guide/primitive-operators/i-beam/
- Dyalog APL — Namespaces: https://docs.dyalog.com/20.0/language-reference-guide/system-functions/ns/
- J Software — Locales: https://www.jsoftware.com/help/learning/28.htm
- APL Wiki — Namespace: https://aplwiki.com/wiki/Namespace
- Python `importlib` documentation: https://docs.python.org/3/library/importlib.html
