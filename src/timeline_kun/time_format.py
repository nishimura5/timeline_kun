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


def seconds_to_time_str(src):
    if isinstance(src, str):
        s = src.strip()
        if s == "":
            return ""

        colons = s.count(":")
        if colons == 2:
            h, m, sec = s.split(":")
            total = int(h) * 3600 + int(m) * 60 + int(sec)
            return seconds_to_time_str(total)

        elif colons == 1:
            minutes, seconds = s.split(":")
            minutes_i = int(minutes)
            seconds_i = int(seconds)
            total = minutes_i * 60 + seconds_i
            return seconds_to_time_str(total)

        elif colons == 0:
            sec = int(s)
        else:
            raise ValueError(f"Invalid time format: {src!r}")

    else:
        sec = int(src)

    hours = sec // 3600
    remain = sec - (hours * 3600)
    minutes = remain // 60
    seconds = remain - (minutes * 60)
    return f"{int(hours)}:{int(minutes):02}:{int(seconds):02}"


def time_str_to_seconds(time_str):
    if time_str == "":
        time_str = "0"
    colons = time_str.count(":")
    if colons == 2:
        hours, minutes, seconds = time_str.split(":")
        return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    elif colons == 0:
        return int(time_str)
    minutes, seconds = time_str.split(":")
    return int(minutes) * 60 + int(seconds)
