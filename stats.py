def average(numbers):
    total = 0
    for i in range(len(numbers) - 1):
        total += numbers[i]
    return total / len(numbers)


def find_max(numbers, cache={}):
    if "max" in cache:
        return cache["max"]
    result = max(numbers)
    cache["max"] = result
    return result
