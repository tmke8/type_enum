# `type_enum`: Concise sum types in Python
Sum types (aka tagged unions) in the style of Rust's `enum`s, with pattern matching and (with the mypy plugin) exhaustiveness checking.

## Basic usage

```python
from type_enum import Field, TypeEnum

class BgColor(TypeEnum):
    transparent: Field[()]
    name: Field[str]
    rgb: Field[int, int, int]
    hsv: Field[int, int, int]

background_color: BgColor = BgColor.rgb(39, 127, 168)

assert isinstance(background_color, BgColor)
assert not isinstance(BgColor.rgb, BgColor)

match background_color:
    case BgColor.transparent():  # unfortunately needs the parentheses
        print("no color")
    case BgColor.name(color_name):
        print(f"color name: {color_name}")
    case BgColor.rgb(red, green, blue):
        print(f"RGB: {red}, {green}, {blue}")
    case BgColor.hsv(hue, saturation, value):
        print(f"HSV: {hue}, {saturation}, {value}")
# will print "RGB: 39, 127, 168"
```

## Installation

Requires Python >= 3.11 (because features from PEP 646 are required)

```
pip install type-enum
```

And for the mypy plugin (requires mypy >= 1.7):
```
pip install type-enum-plugin
```

Then register the plugin with
```toml
[tool.mypy]
plugins = "type_enum_plugin"
```

## Advanced usage
### Exhaustiveness checking
To make exhaustiveness checking work, you first need the mypy plugin, and then you also need to use the special `T` attribute that is synthesized for each `TypeEnum`:

```python
from type_enum import Field, TypeEnum

class Color(TypeEnum):
    transparent: Field[()]
    name: Field[str]

def f(color: Color.T) -> str:
    match color:
        case Color.transparent():
            return "no color"
        case Color.name(color_name):
            return color_name

assert f(Color.transparent()) == "no color"
```

The requirement to use `.T` is a limitation of the mypy plugin, and hopefully will be removed in the future.

### Generics

The `.T` attribute can also be used to specify type arguments for generic `TypeEnum`s:

```python
from typing import Generic, Tuple, Type, TypeVar

from type_enum import Field, TypeEnum

U = TypeVar("U")

class Maybe(TypeEnum, Generic[U]):
    nothing: Field[()]
    some: Field[U]

a = Maybe.some[int](3)

def f(x: Maybe.T[int]) -> int:
    match x:
        case Maybe.some(y):
            return y
        case Maybe.nothing():
            return 0

assert f(a) == 3
```
