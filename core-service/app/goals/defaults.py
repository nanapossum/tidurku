def healthy_range(age: int) -> tuple[int, int]:
    # Acuan Hirshkowitz dkk. (2015), bukan saran medis.
    if age < 14:
        return 9, 11
    if age < 18:
        return 8, 10
    if age < 65:
        return 7, 9
    return 7, 8


def default_target(age: int) -> float:
    minimum, maximum = healthy_range(age)
    return (minimum + maximum) / 2


DEFAULT_BEDTIME = "23:00"
