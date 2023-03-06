from typing import Final
from type_enum import TypeEnum

class BgColor(TypeEnum):
    transparent = ()
    # a: Final = 32
    name = (str,)
    # b = (3, 4)
    rgb = {"red": int, "green": int, "blue": int}  # named args
    hsv = {"hue": int, "saturation": int, "value": int}
reveal_type(BgColor.rgb)
background_color = BgColor.rgb(red=39, green=127, blue=168)
reveal_type(background_color.red)
assert isinstance(background_color, BgColor)

x: str = "foo"
match background_color:
    case BgColor.transparent():
        print("no color")
    case BgColor.name(color_name):
        print(f"color name: {color_name}")
    case BgColor.rgb(red=r, green=g, blue=b):
        x = r
        print(f"RGB: {r}, {g}, {b}")
    case BgColor.hsv(hue=h, saturation=s, value=v):
        print(f"HSV: {h}, {s}, {v}")
