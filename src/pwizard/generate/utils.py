import re


def split_relist(v: str) -> list[str | re.Pattern]:
    "converts a newline separated string into a list, omitting empty elements"
    res: list[str | re.Pattern] = []
    for elem in v.splitlines():
        e = elem.strip()
        if e:
            if e[:1] == e[-1:] == "/":
                res.append(re.compile(e))
            else:
                res.append(e)
    return res
