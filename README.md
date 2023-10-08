# `type_enum`: Concise sum types in Python

### Installation

```
pip install type-enum
```

And for the mypy plugin:
```
pip install type-enum-plugin
```

Then register the plugin with
```toml
[tool.mypy]
plugins = "type_enum_plugin"
```

### Usage

```python
from type_enum import Field, TypeEnum

class BgColor(TypeEnum):
    transparent: Field[()]
    name: Field[str]
    rgb: Field[int, int, int]
    hsv: Field[int, int, int]

background_color: BgColor = BgColor.rgb(39, 127, 168)
assert isinstance(background_color, BgColor)
assert not isinstance(BgColor.rgb, BgColor)  # different from Enum

match background_color:
    case BgColor.transparent():
        print("no color")
    case BgColor.name(color_name):
        print(f"color name: {color_name}")
    case BgColor.rgb(red, green, blue):
        print(f"RGB: {red}, {green}, {blue}")
    case BgColor.hsv(hue, saturation, value):
        print(f"HSV: {hue}, {saturation}, {value}")
# will print "RGB: 39, 127, 168"
```
