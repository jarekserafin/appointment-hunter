import datetime

x = datetime.date.today()
new_date = x + datetime.timedelta(weeks=2)
print(new_date)