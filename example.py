from type_enum import TypeEnum

class BgColor(TypeEnum):
    transparent = ()
    name = (str,)
    rgb = {"red": int, "green": int, "blue": int}  # named args
    hsv = {"hue": int, "saturation": int, "value": int}

background_color = BgColor.rgb(red=39, green=127, blue=168)
assert isinstance(background_color, BgColor)

match background_color:
    case BgColor.transparent():
        print("no color")
    case BgColor.name(color_name):
        print(f"color name: {color_name}")
    case BgColor.rgb(red=r, green=g, blue=b):
        print(f"RGB: {r}, {g}, {b}")
    case BgColor.hsv(hue=h, saturation=s, value=v):
        print(f"HSV: {h}, {s}, {v}")
