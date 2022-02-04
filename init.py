import autobook
import csv
import pandas as pd
from json import loads
from datetime import datetime, timedelta
import re


def check_schedule():
   
    ##
    current_time = datetime.now()
    nextweek_ct = current_time + timedelta(weeks=1) + timedelta(days=1)
    need_booking = False

    with open('config.json', 'r', encoding='utf-8') as f:
        config = loads(f.read())
    user_name = config['username']
    pass_word = config['password']
    book_schedule = pd.read_csv('schedule.csv')
    book_schedule_repeat = book_schedule[book_schedule["repeat"] == 1]
    book_schedule_specific = book_schedule[book_schedule["repeat"] == 0]

    if len(book_schedule_specific) > 0:
        for index, row in book_schedule_specific.iterrows():
            print(row["date"])
            contem_date = datetime.strptime(row["date"],"%m/%d/%Y")
            if contem_date.date() == nextweek_ct.date():
                date = datetime.strftime(contem_date.date(),"%d %b")
                time = row["time"]
                pref_court = row["pref_court"]
                sport = row["sports"]
                policy = row["backward"]
                length = row["twoslots"]
                need_booking = True
                break

    if need_booking:
        booking_core = autobook.BookingCore(user_name, pass_word, sport, date, time, pref_court, length=length,
                                    policy=policy)
        booking_core.init_booking()
    else:
        print("No need to book court today")


if __name__ == '__main__':
    check_schedule()