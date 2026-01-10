from typing import Tuple

def get_pagination(limit: int | None, offset: int | None) -> Tuple[int, int]:
    l = 50 if limit is None else max(1, min(limit, 200))
    o = 0 if offset is None else max(0, offset)
    return l, o
