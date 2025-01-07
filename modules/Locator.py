class Locator:
    def __init__(self, tag: str, attr: str, *attr_val):
        self.tag = tag
        self.attr = attr
        self.attr_val = attr_val