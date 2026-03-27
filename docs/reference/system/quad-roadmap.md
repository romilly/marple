# System Functions & Variables Roadmap

Planned quad-names for MARPLE, based on Dyalog APL's system functions and variables.

## Already Implemented

### Settable Variables
| Name | Description |
|------|-------------|
| `⎕IO` | Index Origin — 0 or 1 |
| `⎕CT` | Comparison Tolerance — default `1E¯14` |
| `⎕PP` | Print Precision — significant digits for display |
| `⎕RL` | Random Link — seed for `?` |
| `⎕WSID` | Workspace ID |
| `⎕FR` | Floating-point Representation — 645 (float64) or 1287 (decimal) |

### Read-only Variables
| Name | Description |
|------|-------------|
| `⎕A` | Alphabet — `'ABCDEFGHIJKLMNOPQRSTUVWXYZ'` |
| `⎕D` | Digits — `'0123456789'` |
| `⎕TS` | Timestamp — 7-element vector (year month day hour min sec ms) |
| `⎕VER` | Version — e.g. `'MARPLE v0.4.6 on linux'` |
| `⎕EN` | Error Number — last caught error code |
| `⎕DM` | Diagnostic Message — last caught error text |

### System Functions
| Name | Description |
|------|-------------|
| `⎕EA` | Execute Alternate — `'fallback' ⎕EA 'expr'` |
| `⎕UCS` | Unicode — convert between chars and code points |
| `⎕NC` | Name Class — 0=undef, 2=array, 3=function, 4=operator |
| `⎕EX` | Expunge — remove name from workspace |
| `⎕SIGNAL` | Signal — raise an error by code |
| `⎕DR` | Data Representation — query/convert internal types |
| `⎕NREAD` | Read text file |
| `⎕NWRITE` | Write text file (dyadic: `data ⎕NWRITE path`) |
| `⎕NEXISTS` | Check file existence — returns 1 or 0 |
| `⎕NDELETE` | Delete file |
| `⎕FMT` | Format — dyadic with I/F/E/A/G codes, text insertion, G pattern |
| `⎕CR` | Canonical Representation — function source as character matrix |
| `⎕FX` | Fix — define function from text source |

---

## High Priority — Commonly Used

| Name | Type | Description | Notes |
|------|------|-------------|-------|
| `⎕VFI` | Function | Verify and Fix Input — parse numbers from text | Returns (validity vector)(value vector) |
| `⎕DL` | Function | Delay — pause execution for N seconds | Simple: `⎕DL 2.5` sleeps 2.5s |
| `⎕NL` | Function | Name List — list names of a given class | Programmable version of `)fns`/`)vars` |
| `⎕JSON` | Function | JSON — convert between APL arrays and JSON | Monadic (parse) and dyadic (generate) |
| `⎕CSV` | Function | CSV — import/export tabular data | Useful for data processing |
| `⎕DCT` | Variable | Decimal Comparison Tolerance | For `⎕FR←1287` mode, default `1E¯28` |
| `⎕NULL` | Constant | Null value | For JSON interop, empty results |
| `⎕SH`/`⎕CMD` | Function | Execute shell command | Returns output as char matrix |
| `⎕MKDIR` | Function | Create directory (and parents) | For file I/O workflows |
| `⎕NINFO` | Function | File/directory information | Size, type, dates |
| `⎕NPARTS` | Function | Split file path into dir/name/ext | Path manipulation |

## Medium Priority — Useful

| Name | Type | Description | Notes |
|------|------|-------------|-------|
| `⎕FX` | Function | Fix — define function from text | `⎕FX 'fn←{⍵+1}'` |
| `⎕CR` | Function | Canonical Representation — function text as matrix | Introspection |
| `⎕VR` | Function | Visual Representation — function text with newlines | Introspection |
| `⎕NR` | Function | Nested Representation — function as vector of lines | Introspection |
| `⎕WA` | Variable | Workspace Available — free memory in bytes | Diagnostics |
| `⎕AI` | Variable | Account Information — timing data | User ID, CPU time, connect time |
| `⎕NGET` | Function | Read text file with encoding | Like ⎕NREAD but handles BOM/encoding |
| `⎕NPUT` | Function | Write text file with encoding | Like ⎕NWRITE but handles encoding |
| `⎕C` | Function | Case conversion | Upper/lower/title case |
| `⎕PW` | Variable | Print Width — max line width | Controls matrix display wrapping |
| `⎕LX` | Variable | Latent Expression — auto-run on `)load` | Workspace startup hook |
| `⎕S` | Function | Regex Search — PCRE pattern matching | Returns match info |
| `⎕R` | Function | Regex Replace — PCRE search-and-replace | |

## Low Priority — Dyalog-Specific or Niche

### Workspace Introspection
| Name | Description |
|------|-------------|
| `⎕SIZE` | Size of named objects in bytes |
| `⎕SI` | State Indicator — execution stack |
| `⎕XSI` | Extended State Indicator — with namespace paths |
| `⎕AT` | Attributes — function syntax, result type, timestamp |
| `⎕NS` | Create namespace |
| `⎕THIS` | Reference to current namespace |
| `⎕OR` | Object Representation — binary snapshot |
| `⎕LOCK` | Lock function (hide source) |

### Component Files (Dyalog-specific persistence)
| Name | Description |
|------|-------------|
| `⎕FCREATE` | Create component file |
| `⎕FAPPEND` | Append component |
| `⎕FREAD` | Read component |
| `⎕FREPLACE` | Replace component |
| `⎕FERASE` | Delete component file |
| `⎕FTIE`/`⎕FUNTIE` | Open/close component file |
| `⎕FNAMES`/`⎕FNUMS` | List tied files |

### GUI (Windows-specific)
| Name | Description |
|------|-------------|
| `⎕WC` | Window Create |
| `⎕WG` | Window Get property |
| `⎕WS` | Window Set property |
| `⎕DQ` | Dequeue — GUI event loop |
| `⎕NQ` | Generate GUI event |

### Threading
| Name | Description |
|------|-------------|
| `⎕TID` | Thread ID |
| `⎕TNUMS` | Active thread numbers |
| `⎕TSYNC` | Wait for threads |
| `⎕TKILL` | Kill thread |
| `⎕TGET`/`⎕TPUT` | Token pool synchronisation |

### .NET / External Integration
| Name | Description |
|------|-------------|
| `⎕USING` | .NET namespace search path |
| `⎕NEW` | Create .NET instance |
| `⎕NA` | Native API — declare DLL function |
| `⎕EXPORT` | Export functions for .NET assembly |

### Legacy / Deprecated
| Name | Description |
|------|-------------|
| `⎕AV` | Atomic Vector (classic character set) |
| `⎕ARBIN`/`⎕ARBOUT` | Raw byte I/O |
| `⎕STACK` | Execution stack (use `⎕SI` instead) |
| `⎕SHADOW` | Localise names (use lexical scope instead) |
| `⎕ML` | Migration Level (compatibility shim) |
| `⎕DIV` | Division method (0÷0 behaviour) |

---

## MARPLE-Specific Additions (not in Dyalog)

| Name | Description |
|------|-------------|
| `⎕VER` | Version string (MARPLE-specific, not a Dyalog quad) |

## Notes

- MARPLE uses `⎕NREAD`/`⎕NWRITE` as simple text file functions, not Dyalog's
  tie-number-based native file API.
- MARPLE's `⎕DR` type codes follow Dyalog's scheme (11=bool, 323=int32, 645=float64, etc.)
- `⎕FR←1287` uses Python `decimal.Decimal`, not IEEE 754 decimal128.
- Component files (`⎕F*`) are unlikely to be implemented — SD card + text files
  serve the same purpose on Pico hardware.
- GUI functions (`⎕W*`, `⎕DQ`) are not applicable — PRIDE serves this role.
- Threading is not applicable on MicroPython (single-threaded).
