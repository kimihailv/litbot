import csv


# Class for parsing
class TablesFactory:
    def __init__(self, csv_path, encoding='windows-1251'):
        self.dict_data = {}
        with open(csv_path, 'rt') as f:
            content = csv.reader(f, delimiter=';')
            self.process_raw_data(content)

    def process_raw_data(self, csv_reader):
        r = []
        current_group = ''
        for row in csv_reader:
            r.append(self.smart_clear(row))

        for row in r[2:]:
            if len(row) == 1:
                current_group = row[0]
                self.dict_data[current_group] = []
                continue

            if len(row) != 0:
                self.dict_data[current_group].append(row[3:])

        self.dict_data = self.dict_data.items()

    def get_tables(self):
        r = {}

        for group, subjects in self.dict_data:
            r[group.replace('_', '.')] = WeekTable(group, subjects)

        return r

    @staticmethod
    def smart_clear(row):
        new_row = list(filter(lambda v: v.replace(' ', '') != '', row))
        if len(new_row) == 1:
            return new_row
        return row


# Table on a whole week for all groups of grade
class WeekTable:
    def __init__(self, group, subjects):
        self._grade, self._group_num = map(int, group.split('_'))
        self._day_tables = []
        total_days = len(list(filter(lambda v: v!= '', subjects[0])))

        for day in range(total_days):
            day_table = DayTable(day)

            for row in subjects:
                    day_table.__add_subject__(row[day])

            self._day_tables.append(day_table)

    @property
    def grade(self):
        return self._grade

    @property
    def group_num(self):
        return self._group_num

    @property
    def day_tables(self):
        return self._day_tables

    def print(self):
        for day_table in self._day_tables:
            day_table.print()

    def __getitem__(self, key):
        if type(key) is str:
            key = key.lower().capitalize()
            return self._day_tables[DayTable.days_names.index(key)]
        else:
            return self.day_tables[key]


# Table on a day
class DayTable:
    days_names = ('Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота')

    def __init__(self,  weekday):
        self._weekday = self.days_names[weekday]
        self._subjects = []

    @property
    def weekday(self):
        return self._weekday

    @property
    def subjects(self):
        return self._subjects

    @property
    def lessons_count(self):
        return len(list(filter(lambda v: not v.is_empty, self._subjects)))

    @property
    def subjects_names(self):
        subjects = []
        for subject in self._subjects:
            subjects.append(subject.name)
        return list(set(list(filter(lambda v: v != '', subjects))))

    def __getitem__(self, key):
        return self._subjects[key]

    def __add_subject__(self, subject):
        self._subjects.append(Subject(subject))

    def print(self):
        print('{}\n############'.format(self._weekday))
        for subject in self._subjects:
            subject.print()
        print()


class Subject:
    def __init__(self, data):
        if data != '':
            self._name, self._room = data.rsplit(' ', 1)
        else:
            self._name = ''
            self._room = ''

    @property
    def room(self):
        return self._room

    @property
    def name(self):
        return self._name

    @property
    def is_empty(self):
        return self.name == ''

    def print(self):
        if self._name != '':
            print(self._name, self._room)


'''
Usage example:

tables = TablesFactory('path to csv file, for example for 5th grade').get_tables() - array of tables for all groups of 5th grade
tables['5.1'] - week table
tables['5.1'].day_tables - array of tables on each day
tables['5.1']['название дня недели'] - table on some day
 
Methods and properties:

WeekTable: 
print()
.grade
.group_num
.day_tables
and also override of brackets (for tables['5.1']['название дня недели'])

DayTable:
print()
.weekday
.subjects - array of Subject class' instances
.lessons_count

Subject:
print()
.room
.name

'''