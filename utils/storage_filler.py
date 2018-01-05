from globals import loop, session, pool, root
from utils import timetables as tb
from os import path


def fetch_courses():
    url = 'https://www.lit.msu.ru/api/v1/study/Ulysses/2017–2018/'
    return session.get(url)


async def grab_courses():
    courses = await fetch_courses()
    return await courses.json()


async def fill_courses():
    courses = await grab_courses()
    async with pool.acquire() as conn:
        cur = await conn.cursor()

        for course in courses:
            await cur.execute(
                'INSERT INTO courses (teacher_id, grade, subject_id) VALUES (?, ?, ?)',
                course['teacher_id'], course['study_grade'], course['subject_id'])

            await cur.commit()

        await cur.close()
        await conn.close()


async def fill_subjects():
    courses = await grab_courses()
    inserted = []
    async with pool.acquire() as conn:
        cur = await conn.cursor()
        for course in courses:
            if course['subject_id'] not in inserted:
                await cur.execute(
                    'INSERT INTO subjects (subject_id, subject_name) VALUES (?, ?)', course['subject_id'],
                    course['subject'])
                await cur.commit()

                inserted.append(course['subject_id'])

        await cur.close()
        await conn.close()


async def fill_timetables():
    subjects_dict = {}
    async with pool.acquire() as conn:
        cur = await conn.cursor()
        await cur.execute('SELECT * FROM subjects')
        subjects = await cur.fetchall()

        for subject_cell in subjects:
            subjects_dict[subject_cell[1]] = subject_cell[0]

        for grade in range(5, 12):
            csv_file = path.join(root, 'timetables/{}.csv'.format(grade))
            timetables = tb.TablesFactory(csv_file).get_tables()
            for group_num, group_timetable in timetables.items():
                for day_table in group_timetable.day_tables:
                    print(group_num)
                    filtered = list(filter(lambda v:
                                           v != 'Физкультура' and v != 'Инф,Алгоритмика' and
                                           v != 'Алго,Информатика' and v != 'Алгоритмика'
                                           and v != 'ММЭ,КАД' and v != 'ТВП',
                                           day_table.subjects_names))
                    sets = list(map(lambda v: (grade, group_num[-1], subjects_dict[v],
                                               day_table.weekday_index), filtered))

                    for set in sets:
                        await cur.execute('INSERT INTO timetables '
                                          '(grade, group_num, subject_id, day) VALUES (?, ?, ?, ?)', set)
                        await cur.commit()

        await cur.close()
        await conn.close()

async def fill_teachers():
    courses = await grab_courses()
    inserted = []
    async with pool.acquire() as conn:
        cur = await conn.cursor()

        for course in courses:
            if course['teacher_fullname_shorten'] not in inserted:
                await cur.execute(
                    'INSERT INTO teachers (teacher_id, teacher_shorten) VALUES (?, ?)',
                    course['teacher_id'], course['teacher_fullname_shorten'])
                await cur.commit()
                inserted.append(course['teacher_fullname_shorten'])

        await cur.close()
        await conn.close()


async def do_all():
    await fill_courses()
    await fill_subjects()
    await fill_timetables()


loop.run_until_complete(fill_teachers())
