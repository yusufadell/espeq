# -*- coding: utf-8 -*-

from json import JSONDecoder, JSONEncoder, dumps, loads


def serialize(*args, **kwargs):
    kwargs["cls"] = JSONEncoder
    return dumps(*args, **kwargs)


def deserialize(*args, **kwargs):
    kwargs["cls"] = JSONDecoder
    return loads(*args, **kwargs)
