import re
from utils import vk_core
from urllib import parse as urlparse
from html import unescape

months = {
    '01': 'январ', '02': 'феврал', '03': 'март',
    '04': 'апрел', '05': 'ма', '06': 'июн',
    '07': 'июл', '08': 'август', '09': 'сентябр',
    '10': 'октябр', '11': 'ноябр', '12': 'декабр'
}


def parse(title, day, month, grade, group_num):
    date = r'(?:\s|^)0?({day})\.0?({month})|' \
           r'(?:\s|^)0?({day}) ?({month_name}.*?)|' \
           r'/?(?:\s|^|/)0?({day})/?.+ ?({month_name}.*?)'\
        .format(day=day, month=month, month_name=months[month])
    date_range = r'(?P<day_bn>\d+)\.?(?P<month_bn>\d+)? ?(?:[-‐−‒⁃–—―]|по|до) ?' \
                 r'(?P<day_ed>\d+)\.?(?P<month_ed>\d+)? ?(?P<month_name>\b{month_name}.\b)?' \
        .format(month_name=months[month])

    group = r'({}\.\d\b)'.format(grade)
    # simple date check
    date_check = len(re.findall(date, title)) != 0
    if not date_check:
        # date range check
        matches = [m.groupdict() for m in re.finditer(date_range, title)]
        if len(matches) != 0:
            matches = matches[0]
            if matches['month_name'] is not None:
                # case when dd - dd month name
                date_check = int(matches['day_bn']) <= int(day) <= int(matches['day_ed'])
            else:
                # case when dd.mm - dd.mm
                matched_month = matches['month_bn'] or matches['month_ed']
                if matched_month is not None:
                    matched_month = int(matched_month)
                    month = int(month)
                    date_check = matched_month == int(month) and \
                                 int(matches['day_bn']) <= int(day) <= int(matches['day_ed'])

                    if matches['month_bn'] is not None and matches['month_ed'] is not None:
                        date_check = date_check or (int(matches['month_bn']) == int(month) and
                                                    int(matches['month_ed']) > int(month) or
                                                    int(matches['month_ed']) == 1 and int(month) > 1)
                else:
                    date_check = False
        else:
            date_check = False

    group_match = re.findall(group, title)

    if len(group_match) == 0:
        group_check = True
    elif '{}.{}'.format(grade, group_num) in group_match:
        group_check = True
    else:
        group_check = False

    return date_check and group_check


async def get_suitable(courses, pairs, date, grade, group_num):
    day, month = date.strftime("%d %m").split()
    day = day[1:] if day.startswith('0') else day
    r = []
    no_match = []
    found = False
    for i, course in enumerate(courses):

        materials = await course.json()
        for material in materials:
            content = material['title'] if len(material['title']) > 4 else material['body_clean']
            match = parse(content, day, month, grade, group_num)
            if match:
                r.append(material)
                found = True
                break
        if not found:
            no_match.append((materials[0]['subject'], pairs[i], grade))
        found = False

    return r, no_match


async def get_hw(courses, pairs, date, grade, group_num):
    materials, no_match = await get_suitable(courses, pairs, date, grade, group_num)
    return await generate_response(materials, no_match), date.strftime('%d.%m')


async def generate_response(materials, no_match):
    subject_block = ''
    for material in materials:
        subject_block += '\n\n=== {} ({}) ===\n\n'.format(material['subject'], material['teacher_fullname'])
        if material['body'] is not None and material['body'].replace(' ', '') != '':
            subject_block += unescape(material['body_clean'].strip(' &nbsp; \t\n\r'))
            links = await link_extractor(material['body'])
            if len(links) != 0:
                subject_block += '\n\n\'\'\'Ссылки\'\'\': {}\n\n\n'.format(' '.join(links))

        if material['attachments'] is not None:
            attaches = await format_attach(material['attachments'])
            if material['body'] is not None and material['body'].replace(' ', '') != '':
                subject_block += '\n\n'
            subject_block += '\'\'\'Приложения\'\'\': {}\n\n\n'.format(' '.join(attaches))

    no_match_block = '\n\n=== Не найдено ДЗ для следующих предметов: ===\n\n'

    for subject in no_match:
        link = 'https://www.lit.msu.ru/study/Ulysses/2017–2018/{}/{}/{}'.format(subject[2], subject[1][0],
                                                                                       subject[1][1])
        no_match_block += '[{}|{}]\n\n'.format(link, subject[0])
    return subject_block[2:] + no_match_block


async def link_extractor(body):
    r = []
    pattern = r'<a href=(.+?)>(.+?)<\/a>'
    matches = re.findall(pattern, body)
    for match in matches:
        r.append('[{}|{}]'.format(match[0].replace('"', ''), match[1]))
    return r


async def format_attach(attaches):
    r = []
    for attach in attaches.split(';'):
        attach_name = urlparse.unquote(attach.split('/')[-1]).rsplit('.', 1)[0]
        r.append('[{}|{}]'.format(attach, attach_name))

    return r
