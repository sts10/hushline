import random
import string
from typing import Any, Callable, Mapping, Optional, Sequence, Tuple, TypeVar

T = TypeVar("T")


def one_of(xs: Sequence[T], predicate: Callable[[T], bool]) -> T:
    matches = [x for x in xs if predicate(x)]
    match len(matches):
        case 1:
            return matches[0]
        case 0:
            raise ValueError("No matches")
        case _:
            raise ValueError(f"Too many matches: {matches}")


def random_bool() -> bool:
    return bool(random.getrandbits(1))


def random_optional_bool() -> Optional[bool]:
    if random_bool():
        return None
    return random_bool()


def random_string(length: int) -> str:
    return "".join(random.choice(string.ascii_lowercase) for _ in range(length))


def random_optional_string(length: int) -> Optional[str]:
    if random_bool():
        return None
    return random_string(length)


def format_param_dict(params: Mapping[str, Any]) -> Tuple[str, str]:
    return (", ".join(params.keys()), ", ".join(f":{x}" for x in params))


class Missing:
    def __eq__(self, other: object) -> bool:
        return False

    def __ne__(self, other: object) -> bool:
        return True


# ridiculous formatting because `ruff` won't allow `not (x == y)`
assert (Missing() == Missing()) ^ bool("x")
assert Missing() != Missing()