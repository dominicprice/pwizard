from datetime import timedelta

SEC_TO_MIN = 60
SEC_TO_HOUR = SEC_TO_MIN * 60


def format_timedelta(d: timedelta) -> str:
    prefix = ""
    res = ""
    elapsed = d.total_seconds()

    # use same logic as below but prefix with a minus sign if delta is
    # negative
    if elapsed < 0:
        prefix = "-"
        elapsed *= -1

    if elapsed > 1:
        if elapsed > SEC_TO_HOUR:
            hours, elapsed = divmod(elapsed, SEC_TO_HOUR)
            res += str(hours) + "h"
        if res or elapsed > SEC_TO_MIN:
            minutes, elapsed = divmod(elapsed, SEC_TO_MIN)
            res += str(minutes) + "m"
        res += _float_to_str(elapsed) + "s"
    else:
        if (ms := elapsed * 1e3) > 1:
            res = _float_to_str(ms) + "ms"
        elif (us := elapsed * 1e6) > 1:
            res = _float_to_str(us) + "us"
        elif (ns := elapsed * 1e9) > 1:
            res = _float_to_str(ns) + "ns"
        else:
            res = "0s"

    return prefix + res


def _float_to_str(f: float) -> str:
    return "{:.3f}".format(f).rstrip("0").rstrip(".")
