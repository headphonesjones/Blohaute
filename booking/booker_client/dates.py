from datetime import timedelta, datetime
import time


def parse_as_date(date_time):
    return date_time.strftime("%Y-%m-%d")


def parse_as_time(date_time):
    return date_time.strftime("%H:%M")


def format_date_for_booker_json(start_date):
    start_date = start_date - timedelta(hours=1)
    return "/Date(%s%s)/" % (int(time.mktime(start_date.timetuple()) * 1000), "-0600")


def parse_date(datestring):
    timepart = datestring.split('(')[1].split(')')[0]
    milliseconds = int(timepart[:-5])
    hours = int(timepart[-5:]) / 100
    # print("hours is what? %s" % hours)
    timepart = milliseconds / 1000

    dt = datetime.utcfromtimestamp(timepart + hours * 3600)
    return dt