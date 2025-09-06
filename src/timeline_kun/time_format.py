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
        if src == "":
            return ""
        colons = src.count(":")
        if colons == 2:
            return src
        elif colons == 1:
            minutes, seconds = src.split(":")
            hours = int(minutes) // 60
            minutes = int(minutes) % 60
            return f"{hours}:{minutes:02}:{int(seconds):02}"
        elif colons == 0:
            sec = int(src)
    else:
        sec = src
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
