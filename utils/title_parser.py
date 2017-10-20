import re
import json
import unicodedata

months = {
    '01': 'январ', '02': 'феврал', '03': 'март',
    '04': 'апрел', '05': 'ма', '06': 'июн',
    '07': 'июл', '08': 'август', '09': 'сентябр',
    '10': 'октябр', '11': 'ноябр', '12': 'декабр'
}


def parse(title, date, group):
    date = date.strftime("%d.%m.%y")
    day, month, year = date.split('.')
    if day.startswith('0'):
        day = day[1:]
    grade, group_num = group.split('.')

    keywords = r'(?:дз|домашняя работа|hw|homework|домашнее задание)?'
    date_group = r'\b0?{day}\.0?{month}(?:\.(?:20)?{year})?\b'.format(day=day, month=month, year=year)
    date_alt_group = r'\b{day} (?:\b{month_name}.\b)\b'.format(day=day, month_name=months[month])
    date_range_pattern = r'на (?:неделю)? ([\d\.]+(?:\.\d+)?)-([\d\.]+(?:\.\d+)?)'
    focus_group = r'({date_group}|{date_alt}|\b{grade}\.{group_num}\b)' \
        .format(date_group=date_group, date_alt=date_alt_group, grade=grade, group_num=group_num)
    pattern = r'(?:.*?){keywords}(?:.*?)' \
              '{focus_group}(?:.*?)' \
              '{focus_group}|{keywords}(?:.*?)' \
              '({date_group}|{date_alt})'.format(keywords=keywords, focus_group=focus_group,
                                                 date_group=date_group, date_alt=date_alt_group)
    matches = re.search(pattern, title, flags=re.IGNORECASE)
    if matches is not None:
        return list(filter(lambda v: v is not None, matches.groups()))
    else:
        matches = re.search(date_range_pattern, title, flags=re.IGNORECASE)
        if matches is not None:
            matches = list(map(lambda v: int(float(v)), matches.groups()))
            if matches[0] <= int(day) <= matches[1]:
                return True
    return None


def gen_answer(hw):
    body = None
    if hw['body_clean'] is not None:
        body = unicodedata.normalize('NFKD', hw['body_clean'])

    return hw['subject'], hw['teacher_fullname'], body, hw['attachments']


def get_suitable(materials, date, group):
    found = []
    result = []

    for material in materials:
        for hw in json.loads(material):
            id = '{}{}'.format(hw['subject_id'], hw['teacher_fullname'])
            if id not in found:
                if len(hw['title']) > 2:
                    matches = parse(hw['title'], date, group)
                else:
                    matches = parse(hw['body'], date, group)
                #print(hw['title'], hw['teacher_fullname'], matches)
                if matches is not None:
                    found.append(id)
                    result.append(gen_answer(hw))
            else:
                continue

    return result