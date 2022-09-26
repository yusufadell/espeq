from importlib import import_module


def import_app(app):
    module_path, class_name = app.rsplit(
        sep=".", maxsplit=1
    )  # math.sin => ['math', 'sin']
    module = import_module(module_path)  # eq to import math
    espeq = getattr(module, class_name)
    return espeq  # callable from module, it could be a function like sin()
