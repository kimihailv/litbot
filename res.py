from tinydb import TinyDB
from utils.csv_parser import TablesFactory

data = {}

for grade in range(5, 12):
    data[grade] = {}
    data[grade]['courses'] = TinyDB('courses_db/{}.json'.format(grade))
    data[grade]['timetable'] = TablesFactory('timetables/{}.csv'.format(grade)).get_tables()

