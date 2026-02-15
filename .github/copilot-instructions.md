# HP Prime MicroPython — AI Coding Instructions

This project targets the **HP Prime graphing calculator** running MicroPython. The display is **320×240 pixels** with a resistive touchscreen. Code runs in a constrained embedded environment with limited memory and no networking.

---

## Platform Constraints

- **MicroPython subset** — not all standard MicroPython features exist. No `os.listdir`, no `time.sleep`, no `json`, no `re` (use `ure` instead).
- **No pip/packages** — only the built-in modules listed below are available.
- **Limited memory** — avoid large data structures, long strings, and deep recursion. Prefer generators and chunked processing.
- **No threading** — single-threaded execution only.
- **No networking** — no WiFi, no sockets, no HTTP.
- **File I/O** — use `open()` for reading/writing files. Use `hpprime.eval('AFiles()')` to list files in the app directory.
- **Screen** — 320×240 pixels. Graphics buffer G0 is the visible display. Buffers G1–G9 are off-screen.
- **Strings** — PPL eval strings require escaping: backslashes doubled (`\\\\`), double quotes escaped (`\\"`).

---

## Project Structure (HP Prime App)

An HP Prime Python app lives in a `.hpappdir` folder containing:
- `main.py` — entry point (imported by the app's PPL wrapper)
- `*.py` — additional Python modules
- `*.md`, `*.txt` — data files accessible via `open()`
- `MarkdownViewer.hpapp` — app metadata
- `MarkdownViewer.hpappprgm` — PPL wrapper that calls `PYTHON(main)`
- `MarkdownViewer.hpappnote` — app notes

Deploy by copying the `.hpappdir` folder to the calculator's Applications Library via the HP Connectivity Kit.

---

## Available Python Libraries

### `hpprime` — Low-level hardware access (PRIMARY module)

This is the most important module. It provides direct access to PPL commands and graphics primitives.

#### Core

| Function | Description |
|---|---|
| `eval(ppl_string)` | Execute any PPL command and return its result. **This is the escape hatch** — any PPL function not exposed directly can be called via `eval('COMMAND(args)')`. |
| `keyboard()` | Get raw keyboard state. |
| `mouse()` | Get touch data: returns `[[x,y,xOrig,yOrig,type],[]]` for finger 1 and 2. Returns `[[],[]]` when no touch since last check. `eval('mouse(1)')` returns just the x coordinate (useful for clearing pending events). |

#### Graphics Primitives

All graphics functions operate on numbered GROB (graphics object) buffers: G0 (visible screen) through G9 (off-screen).

| Function | Signature | Description |
|---|---|---|
| `dimgrob` | `dimgrob(gr, w, h, color)` | Create/resize an off-screen GROB with given dimensions and fill color. |
| `fillrect` | `fillrect(gr, x, y, w, h, border_color, fill_color)` | Draw a filled rectangle. **Note: takes width/height, not x2/y2.** |
| `rect` | `rect(gr, x, y, w, h, color)` | Draw a rectangle outline. |
| `line` | `line(gr, x1, y1, x2, y2, color)` | Draw a line. |
| `pixon` | `pixon(gr, x, y, color)` | Set a single pixel. |
| `getpix` | `getpix(gr, x, y)` | Get the color of a pixel. Returns integer. |
| `textout` | `textout(gr, x, y, text, font, color, width)` | Draw text. Font: 0=default, 1=10px, 2=12px, 3=14px, 4=16px, 5=18px, 6=20px, 7=22px. |
| `arc` | `arc(gr, x, y, r, a1, a2, color)` | Draw an arc. |
| `circle` | `circle(gr, x, y, r, color)` | Draw a circle. |
| `blit` | `blit(gr, dx, dy, dw, dh, src_gr, sx, sy, sw, sh)` | Copy a region between GROBs. |
| `strblit` | `strblit(destG, dX, dY, dW, dH, srcG, sX, sY, sW, sH)` | Buffer-to-buffer pixel copy. Same as blit but operates on raw pixel data. When src and dest sizes match, no scaling occurs. |
| `grobw` | `grobw(gr)` | Get GROB width. |
| `grobh` | `grobh(gr)` | Get GROB height. |
| `grob` | `grob(gr, data)` | Create GROB from data. |

**`_c` variants** — Functions ending in `_c` (e.g., `fillrect_c`, `line_c`, `textout_c`) use Cartesian coordinates instead of pixel coordinates. Use `set_cartesian(gr, x_min, x_max, y_min, y_max)` and `get_cartesian(gr)` to configure.

#### Commonly Used via `eval()`

```python
import hpprime as h

# Text rendering with background color
h.eval('TEXTOUT_P("Hello", G0, 10, 10, 2, RGB(0,0,0), 320, RGB(255,255,255))')

# Get text dimensions → returns [width, height]
h.eval('TEXTSIZE("Hello", 2)')

# BLIT with transparency
h.eval('BLIT_P(G0, dx, dy, dx2, dy2, G5, sx, sy, sx2, sy2, 0xA8A8A7, 128)')

# GROB dimensions
h.eval('GROBW_P(G0)')  # → width
h.eval('GROBH_P(G0)')  # → height

# Keyboard
h.eval('GETKEY()')  # Returns keycode or -1

# Timing
h.eval('ticks()')   # Millisecond tick count
h.eval('wait(0.1)') # Sleep for 0.1 seconds

# File listing
h.eval('AFiles()')  # Returns list of files in app directory

# Dialogs (PPL UI)
h.eval('MSGBOX("Hello")')                        # Modal message box
h.eval('X:=0;CHOOSE(X, "Title", "A", "B", "C")')  # Returns 1-based index
# CHOOSE variable MUST be initialized first (X:=0) and be a capital letter.

# INPUT — multi-field user input dialog
# Args: variable list, title, labels list, help text list
# Use TYPE() integers for field types: [0]=reals only, [2]=string, [3]=list
# The manual claims [-1] accepts all types but it's buggy — use explicit types.
h.eval('INPUT({D,F}, "Params", {"Dist:", "Freq:"}, {"in meters", "in Hz"})')
d_val = h.eval('D')  # Retrieve value from PPL environment
f_val = h.eval('F')
# INPUT returns 0 if user cancelled, non-zero if OK.

h.eval('DRAWMENU("F1","F2","F3","F4","F5","F6")')

# App variable sharing (between Python and PPL/CAS/HOME)
h.eval('AVars("MyVar"):=42')
n = h.eval('AVars("MyVar")')  # Note: int becomes float when retrieved

# Program-level variable sharing (non-app PPL programs)
# From Python: h.eval('myProg.myVar:=42')
# From HOME/CAS: type myProg.myVar to retrieve

# Print to terminal
h.eval('print')  # Clear screen
```

### `graphic` — High-level drawing (simpler API)

| Function | Signature | Description |
|---|---|---|
| `clear_screen()` | `clear_screen()` | Clear the display. |
| `draw_line(x1,y1,x2,y2,c)` | Draws a line with color `c` (from predefined constants). |
| `draw_pixel(x,y,c)` | Set a pixel. |
| `get_pixel(x,y)` | Get pixel color. |
| `set_pixel(x,y,c)` | Set a pixel. |
| `draw_rectangle(x1,y1,x2,y2,c)` | Draw rectangle outline. |
| `draw_filled_polygon(pts,c)` | Draw filled polygon. |
| `draw_circle(x,y,r,c)` | Draw circle outline. |
| `draw_filled_circle(x,y,r,c)` | Draw filled circle. |
| `draw_arc(x,y,r,a1,a2,c)` | Draw arc. |
| `draw_filled_arc(x,y,r,a1,a2,c)` | Draw filled arc. |
| `draw_string(x,y,text,c,bg)` | Draw text string. |
| `draw_polygon(pts,c)` | Draw polygon outline. |
| `show()` | Refresh display. |
| `show_screen()` | Show screen. |

**Predefined colors:** `graphic.black`, `graphic.white`, `graphic.red`, `graphic.green`, `graphic.blue`, `graphic.cyan`, `graphic.magenta`, `graphic.yellow`.

> **Note:** The `graphic` module is higher-level but less flexible than `hpprime`. For performance-sensitive code, use `hpprime` directly.

### `cas` — Computer Algebra System

```python
import cas
cas.caseval('factor(x^2-1)')  # Returns string result
cas.eval_expr('solve(x^2=4,x)')
cas.get_key()  # Alternative keyboard input
cas.xcas('command')
```

### `arith` — Number theory

| Function | Description |
|---|---|
| `asc(c)` | ASCII code of character. |
| `char(n)` | Character from ASCII code. |
| `euler(n)` | Euler's totient. |
| `gcd(a,b)` | Greatest common divisor. |
| `iegcd(a,b)` | Extended GCD. |
| `ifactor(n)` | Integer factorization. |
| `isprime(n)` | Primality test. |
| `lcm(a,b)` | Least common multiple. |
| `nextprime(n)` | Next prime after n. |
| `nprimes(n)` | Count of primes up to n. |
| `prevprime(n)` | Previous prime before n. |

### `linalg` — Linear algebra (numpy-like)

Numpy is **not available**. Use `linalg` instead for matrix/vector operations.

| Function | Description |
|---|---|
| `matrix(data)` | Create matrix from nested lists. |
| `eye(n)` / `identity(n)` / `idn(n)` | Identity matrix. |
| `zeros(shape)` / `ones(shape)` | Zero/one matrices. |
| `inv(m)` | Matrix inverse. |
| `det(m)` | Determinant. |
| `transpose(m)` | Transpose. |
| `dot(a,b)` | Dot product. |
| `cross(a,b)` | Cross product. |
| `solve(a,b)` | Solve linear system. |
| `eig(m)` / `eigenvects(m)` | Eigenvalues/vectors. |
| `rref(m)` | Row-reduced echelon form. |
| `fft(v)` / `ifft(v)` | FFT/inverse FFT. |
| `linspace(a,b,n)` | Linear spacing. |
| `arange(start,stop,step)` | Range as matrix. |
| `rand()` / `ranm(r,c)` / `ranv(n)` | Random values. |
| `add`, `sub`, `mul` | Element-wise operations. |
| `abs`, `real`, `imag`, `conj` | Component access. |
| `shape(m)`, `size(m)` | Dimensions. |
| `apply(m, func)` | Apply function to each element. |
| `horner(coeffs, x)` / `pcoeff` / `peval` / `proot` | Polynomial operations. |

### `math` — Standard math functions

`acos`, `acosh`, `asin`, `asinh`, `atan`, `atan2`, `atanh`, `ceil`, `copysign`, `cos`, `cosh`, `degrees`, `e`, `erf`, `erfc`, `exp`, `expm1`, `fabs`, `floor`, `fmod`, `frexp`, `gamma`, `isfinite`, `isinf`, `isnan`, `ldexp`, `lgamma`, `log`, `log10`, `log2`, `modf`, `pi`, `pow`, `radians`, `sin`, `sinh`, `sqrt`, `tan`, `tanh`, `trunc`

### `cmath` — Complex math

`cos`, `e`, `exp`, `log`, `log10`, `phase`, `pi`, `polar`, `rect`, `sin`, `sqrt`

### `micropython` — Runtime utilities

| Function | Description |
|---|---|
| `const(value)` | Compile-time constant optimization. Use for constants that don't change. |
| `mem_info()` | Print memory usage info. |
| `opt_level(n)` | Set optimization level. |
| `heap_lock()` / `heap_unlock()` | Lock/unlock heap for GC. |
| `stack_use()` | Current stack usage. |
| `pystack_use()` | Current Python stack usage. |
| `kbd_intr(n)` | Set the keyboard interrupt character. |
| `qstr_info()` | Interned string info. |

### `maplotl` — Plotting (matplotlib-like)

`arrow`, `axis`, `bar`, `barplot`, `boxplot`, `boxwhisker`, `clf`, `grid`, `hist`, `histogram`, `linear_regression_plot`, `plot`, `scatter`, `scatterplot`, `show`, `text`, `vector`

### Other Modules

| Module | Key Functions |
|---|---|
| `gc` | `collect()`, `mem_alloc()`, `mem_free()`, `enable()`, `disable()`, `isenabled()`, `threshold()` |
| `sys` | `argv`, `byteorder`, `exc_info()`, `exit()`, `implementation`, `maxsize`, `modules`, `path`, `platform`, `print_exception()`, `stderr`, `stdin`, `stdout`, `version`, `version_info` |
| `array` | `array(typecode, data)` with `.append()`, `.extend()` |
| `ucollections` | `deque`, `namedtuple`, `OrderedDict` |
| `ure` | `compile(pattern)`, `match(pattern, string)`, `search(pattern, string)` |
| `ustruct` | `pack(fmt, ...)`, `pack_into(fmt, buf, offset, ...)`, `unpack(fmt, data)`, `unpack_from(fmt, data, offset)`, `calcsize(fmt)` |
| `urandom` | `random()`, `randint(a,b)`, `randrange(...)`, `choice(seq)`, `getrandbits(n)`, `seed(n)`, `uniform(a,b)` |
| `uhashlib` | `sha256()` with `.update()`, `.digest()` |
| `uio` | `open()`, `BytesIO`, `StringIO`, `FileIO`, `TextIOWrapper` |
| `uerrno` | Error constants: `ENOENT`, `EIO`, `EEXIST`, etc. |
| `utimeq` | Timer queue: `utimeq()` with `.push()`, `.pop()`, `.peektime()` |

---

## Display & UI Patterns

### Screen Layout

```
┌──────────────────────────────────────┐ y=0
│  Title / Header area                 │
│                                      │ y=5
│  Content area (scrollable)           │
│  x=5 to x=315, width=310            │
│                                      │
│                                      │
│                                      │
│                                      │ y≈220
├──────────────────────────────────────┤ y=220
│ F1 │ F2 │ F3 │ F4 │ F5 │ F6 │       │ Menu bar (6 slots × 53px, h=20)
└──────────────────────────────────────┘ y=240
```

### Soft Menu Bar

The bottom 20px (y=220–240) is the soft menu area. Six buttons, each ~53px wide.

```python
# Detect which soft menu button was tapped
def soft_pick(x, y):
    return -1 if y < 220 else min(x // 53, 5)
```

### Font Sizes

| Constant | Font Size | Line Height (approx) |
|---|---|---|
| 0 | Default (Home Settings) | varies |
| 1 | 10px | ~12px |
| 2 | 12px | ~14px |
| 3 | 14px | ~16px |
| 4 | 16px | ~18px |
| 5 | 18px | ~20px |
| 6 | 20px | ~22px |
| 7 | 22px | ~24px |

### GROB Buffers

| Buffer | Typical Use |
|---|---|
| G0 (`GR_AFF`) | Visible screen — draw here to show on display |
| G1–G4 | General off-screen buffers |
| G5 (`GR_TMP`) | Temporary buffer for image composition |
| G6–G9 | Additional off-screen buffers |

### Color Format

Colors are **24-bit integers** in `0xRRGGBB` format:
- `0x000000` = black
- `0xFFFFFF` = white
- `0xF80000` = red
- `0x000080` = dark blue
- `0xA8A8A7` = conventional transparency key color

### Touch / Mouse Input

```python
import hpprime as h

# Method 1: via eval
f1, f2 = h.eval('mouse')  # [[x,y,xOrig,yOrig,type],[]] or [[],[]]

# Method 2: via mouse()
m = h.mouse()  # Returns nested list

# Finger data format: [x, y, xOriginal, yOriginal, eventType]
# type: 0=move, 1=press, 2=release, 3=click, 4=long press, 5=drag

# Clear pending mouse events (debounce / drain queue)
def mouse_clear():
    while h.eval('mouse(1)') >= 0:
        pass

# Wait for a screen touch (blocking)
def mouse_wait():
    while True:
        h.eval('wait(0.1)')  # Throttle I/O loop
        f1, f2 = h.eval('mouse')
        if len(f1) > 0 and f1[0] >= 0:
            return f1, f2
```

### Keyboard Input

```python
import hpprime as h
key = h.eval('GETKEY()')  # Returns keycode or -1

# Common keycodes:
# F1=0, F2=5, F3=10, F4=1, F5=6, F6=11
# Up=2, Down=12, Left=7, Right=8
# ESC=4, Enter=30, Backspace=19
# Plus=50, Minus=45
# Letters: a=14, b=15, c=16, d=17, e=18, f=20, g=21, ...
```

### Event Loop Pattern

```python
import hpprime as h

def main():
    while True:
        h.eval('wait(0.05)')  # Throttle — 0.05s = 20 fps, 0.2s = 5 fps
        # Higher wait = less CPU but slower response.
        # WAIT(0.2) is typical for menu-driven apps.
        # WAIT(0.05) is better for scrolling / drag-heavy UIs.

        key = h.eval('GETKEY()')  # -1 if none since last call
        if key == 4:  # ESC
            break

        f1, f2 = h.eval('mouse')  # [[],[]] if no touch since last call
        if len(f1) > 0 and f1[0] >= 0:
            x, y = f1[0], f1[1]
            evt_type = f1[4]  # 0=move 1=press 2=release 3=click 4=long 5=drag
            # Handle touch at (x, y)
```

### Double Buffering with strblit

```python
from hpprime import dimgrob, strblit, fillrect

# Save a region of the screen
dimgrob(7, 320, 20, 0)  # Create off-screen buffer
strblit(7, 0, 0, 320, 20, 0, 0, 220, 320, 20)  # Save G0 area to G7

# ... draw overlay on G0 ...

# Restore the saved region
strblit(0, 0, 220, 320, 20, 7, 0, 0, 320, 20)  # Copy G7 back to G0
```

---

## PPL Interop via `hpprime.eval()`

Any PPL command can be called from Python using `hpprime.eval('...')`. This is essential for:

- **UI dialogs**: `MSGBOX`, `CHOOSE`, `INPUT`, `DRAWMENU`
- **Text rendering**: `TEXTOUT_P` (with background color support, which `textout` lacks)
- **Text measurement**: `TEXTSIZE`
- **Advanced blit**: `BLIT_P` (with transparency parameters)
- **GROB queries**: `GROBW_P`, `GROBH_P`
- **Timing**: `ticks()`, `wait(seconds)`
- **File operations**: `AFiles()`
- **Variable sharing**: `AVars("name")`
- **Screen control**: `print` (clears the text terminal)

### String Escaping for eval()

When building PPL command strings, **escape carefully**:

```python
def escape_for_ppl(text):
    text = str(text)
    text = text.replace('\\', '\\\\')
    text = text.replace('"', '\\"')
    return text

cmd = 'TEXTOUT_P("' + escape_for_ppl(user_text) + '", G0, 10, 10, 2)'
hpprime.eval(cmd)
```

---

## Common Pitfalls

1. **`fillrect` takes width/height** — `fillrect(gr, x, y, w, h, ...)` not `(gr, x1, y1, x2, y2, ...)`.
2. **`BLIT_P` takes coordinates** — `BLIT_P(G0, x1, y1, x2, y2, G5, ...)` uses corner pairs, unlike `fillrect`.
3. **`GETKEY()` returns -1** when no key is pressed, not 0.
4. **`CHOOSE()` returns 1-based index**, not 0-based. The variable must be initialized first: `h.eval('X:=0;CHOOSE(X,"Title","A","B")')`.
5. **`mouse()` returns nested lists** — returns `[[],[]]` when no touch. Always check `len()` and value before indexing. Use `mouse(1)` to peek at pending x coordinate.
6. **No `time.sleep()`** — use `hpprime.eval('wait(seconds)')` instead.
7. **No `os` module** — use `hpprime.eval('AFiles()')` for file listing.
8. **`micropython.const()`** — use for compile-time constants to save memory.
9. **Integer overflow** — MicroPython handles big integers but they're slow. Prefer bounded values.
10. **String concatenation** — avoid `+` in tight loops; build lists and `''.join()` instead.
11. **PPL variable names are capitalized** — when using `eval('INPUT(D,...)')`, the variable `D` must be a valid PPL capital-letter variable.
12. **AVars bug** — numbers with `e+` notation (like `2e+1`) cause parsing errors in HOME. Use `cas.caseval()` to work around this:
    ```python
    import cas
    def num_to_avars(name, val):
        cas.caseval('AVars("%s"):=%s' % (name, str(val)))
    ```
13. **AVars type coercion** — integers stored via `AVars()` are retrieved as floats.
14. **INPUT field types** — the manual says `[-1]` accepts all data types but it causes errors. Use explicit TYPE() integers: `[0]` = reals, `[2]` = strings, `[3]` = lists.
15. **Button debouncing** — touch events can bounce. Clear stale events before waiting for input with `while h.eval('mouse(1)') >= 0: pass`.
16. **App 'Clear' quirk** — after starting a Python-based app, you may need to hit the 'Clear' soft button once before the app works properly.
17. **numpy not available** — rewrite numpy code to use `linalg.matrix`. Vectors and matrices must use `linalg` equivalents.

---

## Memory Management Tips

- Use `gc.collect()` periodically in long-running programs.
- Use `gc.mem_free()` to check available memory.
- Prefer `micropython.const()` for immutable values.
- Avoid creating large temporary objects; process data in chunks.
- Use `bytearray` instead of `bytes` for mutable binary data.
- Read files line-by-line rather than loading entire files into memory.
- Minimize string concatenation — use lists and `join()`.

---

## PPL Wrapper Programs (Non-App)

Python code that is **not** in an app needs a PPL wrapper:

```ppl
#PYTHON MyPythonCode
  print('Hello from Python!')
#END

EXPORT myFunc()
BEGIN
  PYTHON(MyPythonCode);
END;
```

The `#PYTHON` block name is internal — the exported function name (e.g. `myFunc`) is what appears in the program list. If multiple functions exist, you'll be prompted to choose which to run.

### Sharing Variables Between PPL and Python

```python
import hpprime as h
# Read a PPL LOCAL variable from the wrapping program:
val = h.eval('myProg.myVar')
# Write back:
h.eval('myProg.myVar:=42')
# From HOME or CAS, access via: myProg.myVar
```

For apps, use `AVars()` instead (see above).

---

## App Packaging

1. Create app on calculator: Apps → highlight Python → Save → Rename.
2. In Connectivity Kit, right-click app → Add File for each `.py` and data file.
3. The main program file should simply `import main` (or your entry module) and call the entry function.
4. Use `.hpappdir` folder structure for development, then copy to calculator.
5. App icon is 38×38 pixels.
6. After starting a Python app, you may need to press 'Clear' once.
7. Python apps lose tight PPL integration — PPL `START()`, `RESET()`, `Symb()`, `Plot()`, `Num()` and their Setup counterparts cannot be overridden from Python.

---

## Reference

Based on firmware 2.1.14730 (2023-04-13). Full library listing: [HP Prime Python Libraries](https://copland.udel.edu/~mm/hp/primePython/upython.html). Lessons learned and patterns: [HP Prime Programming](https://copland.udel.edu/~mm/hp/primePython/).
