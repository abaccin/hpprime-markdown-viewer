# Demo Document

This file demonstrates **internal linking**.

## Links

Tap the link below to open the help file:

- [Open Help](help.md)

## More Info

You can link to any `.md` file in the app folder.
Press **ESC** to go back to the previous file.

Try it: [Back to Help](help.md)

## Code Highlighting

Python syntax highlighting:

```python
import hpprime as h

def greet(name="World"):
    """Say hello."""
    # Print greeting
    msg = "Hello, " + name + "!"
    h.eval('MSGBOX("' + msg + '")')
    return 42

for i in range(10):
    if i % 2 == 0:
        print(i)
```

PPL code:

```ppl
EXPORT Main()
BEGIN
  LOCAL x, y;
  x := GETKEY();
  IF x > 0 THEN
    TEXTOUT_P("Key: " + x, G0, 10, 10, 2);
    WAIT(0.5);
  END;
END;
```

## Math Formulas

Formulas render as pretty-print CAS expressions.

```math
integrate(sin(x)^2,x)
```

```math
sum(1/n^2,n,1,infinity)
```

```math
(x^2+1)/(sqrt(x)+3)
```

```math
limit(sin(x)/x,x,0)
```

```math
diff(x^3+2*x,x)
```
