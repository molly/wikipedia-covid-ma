def comma_separate(num):
    try:
        return "{:,}".format(num)
    except ValueError:
        return num
