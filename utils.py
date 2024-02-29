def convert_seconds(seconds):
    """Конвертация полученных от API секунд в дни, часы и минуты."""
    days = seconds // (24 * 3600)
    hours = (seconds % (24 * 3600)) // 3600
    minutes = (seconds % 3600) // 60
    return days, hours, minutes
