def timedelta_to_str(td, hhmmss=True):
    if hhmmss:
        return timedelta_to_str_hh_mm_ss(td)
    else:
        return timedelta_to_str_mm_ss(td)


def timedelta_to_str_hh_mm_ss(td):
    hours = td.seconds // 3600
    remain = td.seconds - (hours * 3600)
    minutes = remain // 60
    seconds = remain - (minutes * 60)
    return f"{int(hours)}:{int(minutes):02}:{int(seconds):02}"


def timedelta_to_str_mm_ss(td):
    minutes = td.seconds // 60
    seconds = td.seconds - (minutes * 60)
    return f"{int(minutes)}:{int(seconds):02}"


def seconds_to_time_str(sec: int | float) -> str:
    sec_i = int(sec)
    if sec_i < 0:
        raise ValueError(f"sec must be >= 0, got {sec!r}")

    hours = sec_i // 3600
    remain = sec_i - (hours * 3600)
    minutes = remain // 60
    seconds = remain - (minutes * 60)
    return f"{int(hours)}:{int(minutes):02}:{int(seconds):02}"


def str_to_seconds(src: str) -> int:
    s = src.strip()
    if s == "":
        return 0

    parts = s.split(":")
    if len(parts) == 1:
        sec = int(parts[0])
        if sec < 0:
            raise ValueError(f"Invalid time (negative): {src!r}")
        return sec

    if len(parts) == 2:
        m_str, s_str = parts
        minutes = int(m_str)
        seconds = int(s_str)
        return minutes * 60 + seconds

    if len(parts) == 3:
        h_str, m_str, s_str = parts
        hours = int(h_str)
        minutes = int(m_str)
        seconds = int(s_str)
        return hours * 3600 + minutes * 60 + seconds

    raise ValueError(f"Invalid time format: {src!r}")


def str_to_time_str(src: str) -> str:
    s = src.strip()
    if s == "":
        return ""
    return seconds_to_time_str(str_to_seconds(s))
