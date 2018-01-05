import datetime, time
import asyncio
import re
from aiohttp import web, client_exceptions
from globals import session, pool, loop
from utils import title_parser, vk_core

vk_api = None
bot = None
current_year = datetime.date.today().year - 2000
days = {
    'пн': 0,
    'вт': 1,
    'ср': 2,
    'чт': 3,
    'пт': 4,
    'сб': 5
}


def init_app():
    global vk_api, bot
    vk_api = vk_core.VkApi()
    bot = vk_core.Bot(vk_api)

    bot.add_handler('reg_arg', register_user)
    bot.add_handler('дз', send_hw)
    bot.add_handler('help', lambda message: bot.send_help(message, 'full'))
    bot.add_handler('edit', edit_profile)
    bot.add_handler('Настройка профиля', edit_profile_ans)

    app = web.Application()
    app.router.add_get('/', handle_get)
    app.router.add_post('/', handle_post)
    return app


async def handle_get(request):
    return web.Response(text='42 What are you doing here%s')


async def handle_post(request):
    message = await request.json()
    if vk_core.VkApi.verify_request(message):
        await bot.notify(message)
        return web.Response(text='ok')


def get_date(date):
    today = datetime.date.today()
    if date is not None:
        date_pattern = r'(.+)\.(.+)'
        match = re.match(date_pattern, date)
        if match is not None:
            try:
                return datetime.datetime.strptime('{}.{}'.format(date, current_year), '%d.%m.%y')
            except ValueError:
                pass
        else:
            if date in days.keys():
                if days[date] < today.weekday():
                    return today + datetime.timedelta(days=(7 - today.weekday() + days[date]))
                else:
                    return today + datetime.timedelta(days=(days[date] - today.weekday()))

    if today.weekday() == 4:
        return today + datetime.timedelta(days=3)
    elif today.weekday() == 5:
        return today + datetime.timedelta(days=2)
    return today + datetime.timedelta(days=1)


async def get_user(user_id):
    async with pool.acquire() as conn:
        cur = await conn.cursor()
        await cur.execute('SELECT grade, group_num, set_up FROM users WHERE vk_id = %s', user_id)
        user = await cur.fetchone()
        await cur.close()

    return user is not None, user


async def register_user(message, args):
    user_check, user = await get_user(message['user_id'])

    if not user_check:
        grade, group_num = args.split('.')
        try:
            grade = int(grade)
            group_num = int(group_num)
        except ValueError:
            await bot.send_error(message)

        if grade >= 5 and 6 >= group_num >= 1:
            async with pool.acquire() as conn:
                cur = await conn.cursor()
                await cur.execute('INSERT INTO users (vk_id, grade, group_num, set_up) VALUES (%s, %s, %s, 0)',
                                  (message['user_id'], grade, group_num))
                await conn.commit()

            await bot.send_success_reg(message)
    else:
        await bot.send_answer(message, 'Вы уже зарегистрированы.')


async def send_hw(message, date=None):

    user_check, user = await get_user(message['user_id'])
    print(user_check, user)

    if user_check:
        st = time.time()
        print(1, time.time() - st)
        try:
            st1 = time.time()
            date = get_date(date)
            print(date)
            if user[2] == 1:
                pairs = await get_personal_pairs(message['user_id'], user[0], user[1], date)
            else:
                pairs = await get_courses_ids(user[0], user[1], date)
            courses = await fetch_courses(user[0], pairs)
            hw, date = await title_parser.get_hw(courses, pairs, date, user[0], user[1])
            print(2, time.time() - st1)
            st2 = time.time()
            page_link = await vk_core.VkApi.create_page(message, hw, date)
            await bot.send_answer(message, 'ДЗ по ссылке: {}'.format(page_link))
            print(3, time.time() - st2)
        except client_exceptions.ContentTypeError:
            await bot.send_sorry(message)
    else:
        await bot.send_reg_request(message)


async def edit_profile(message):
    user_check, user = await get_user(message['user_id'])

    if user_check:
        teacher_opts = await get_teachers_options(user[0])
        async with pool.acquire() as conn:
            cur = await conn.cursor()

            await cur.execute('DELETE FROM memory WHERE vk_id = %s', message['user_id'])
            await cur.execute('DELETE FROM user_data WHERE vk_id = %s', message['user_id'])
            await cur.execute('UPDATE users SET set_up = 0 WHERE vk_id = %s', message['user_id'])

            for num, e in enumerate(teacher_opts):
                await cur.execute('INSERT INTO memory '
                                  '(vk_id, subject_id, subject_name, teachers_id, teachers_shorten, question_num) '
                                  'VALUES (%s, %s, %s, %s, %s, %s)', (message['user_id'], e[0], e[1], e[2], e[3], num))
            await conn.commit()
        await bot.send_answer(message, form_edit_question(teacher_opts[0][3], teacher_opts[0][1], 1, len(teacher_opts)))

    else:
        await bot.send_answer(message, 'Ой, похоже Вы не зарегистрировались :(\n'
                                       'Для более подробной информация отправьте сообщение с командой /help')


async def edit_profile_ans(message, args):
    q_num, total = map(int, args.split(' из '))
    answer = int(message['body']) - 1
    q_num -= 1

    async with pool.acquire() as conn:
        cur = await conn.cursor()
        # connect user answer wih db data

        await cur.execute('SELECT subject_id, teachers_id FROM memory '
                          'WHERE vk_id = %s and question_num = %s', (message['user_id'], q_num))
        subject = await cur.fetchone()
        if subject is None:
            print('ERROR', message)
            return
        teachers_id = subject[1].split()
        if 0 <= answer < len(teachers_id):

            # add new data into db
            await cur.execute('INSERT INTO user_data (vk_id, subject_id, teacher_id) '
                              'VALUES(%s, %s, %s)', (message['user_id'], subject[0], teachers_id[answer]))
            await conn.commit()

            if q_num + 1 < total:
                # send next question
                await cur.execute('SELECT subject_name, teachers_shorten FROM memory '
                                  'WHERE vk_id = %s and question_num = %s', (message['user_id'], q_num + 1))
                data = await cur.fetchone()
                await bot.send_answer(message, form_edit_question(data[1], data[0], q_num + 2, total))
            else:
                await bot.send_answer(message, 'Отлично, Ваш аккаунт настроен! '
                                               'Теперь мы будем присылать Вам только самое нужное.')
                await cur.execute('UPDATE users SET set_up = 1 WHERE vk_id = %s', message['user_id'])
                # clear up
                await cur.execute('DELETE FROM memory WHERE vk_id = %s', message['user_id'])
                await conn.commit()
        else:
            await cur.execute('SELECT subject_name, teachers_shorten FROM memory '
                              'WHERE vk_id = %s and question_num = %s', (message['user_id'], q_num))
            data = await cur.fetchone()
            await bot.send_answer(message, form_edit_question(data[1], data[0], q_num + 1, total))


def form_edit_question(teachers, subject_name, current, total):
    message = '[Настройка профиля][{} из {}]\n\nКто ведет у вас "{}"?\n\n{}\nОтправьте номер учителя.'
    choices = ''
    teachers = teachers.split(',')

    for num, teacher in enumerate(teachers):
        choices += '{}) {}\n'.format(num + 1, teacher)

    return message.format(current, total, subject_name, choices)


async def get_courses_ids(grade, group_num, date):
    async with pool.acquire() as conn:
        cur = await conn.cursor()
        await cur.execute('SELECT t.subject_id, c.teacher_id FROM'
                          ' timetables AS t JOIN courses AS c ON t.subject_id = c.subject_id AND t.grade = c.grade'
                          ' WHERE t.grade = %s AND t.group_num = %s AND t.day = %s', (grade, group_num, date.weekday()))
        pairs = await cur.fetchall()
        await cur.close()

    return pairs

async def get_personal_pairs(vk_id, grade, group_num, date):
    async with pool.acquire() as conn:
        cur = await conn.cursor()
        await cur.execute('SELECT u.subject_id, u.teacher_id FROM user_data u '
                          'JOIN timetables t on u.subject_id = t.subject_id '
                          'WHERE u.vk_id = %s and t.grade = %s and t.group_num = %s and t.day = %s',
                          (vk_id, grade, group_num, date.weekday()))
        pairs = await cur.fetchall()
        await cur.close()

    return pairs

async def get_teachers_options(grade):
    async with pool.acquire() as conn:
        cur = await conn.cursor()
        await cur.execute('SELECT c.subject_id, '
                          's.subject_name, '
                          'group_concat(t.teacher_id SEPARATOR " "), group_concat(t.teacher_shorten SEPARATOR ",") '
                          'FROM courses c '
                          'JOIN subjects s ON c.subject_id = s.subject_id '
                          'JOIN teachers t ON t.teacher_id = c.teacher_id '
                          'WHERE c.grade = %s '
                          'GROUP BY c.subject_id '
                          'HAVING COUNT(t.teacher_id) > 1', grade)
        options = await cur.fetchall()
        await cur.close()
    return options


async def fetch_courses(grade, pairs):
    url = 'https://www.lit.msu.ru/api/v1/study/Ulysses/2017–2018/{}/{}/{}'
    tasks = list(map(lambda pair: session.get(url.format(grade, pair[0], pair[1])), pairs))
    return await asyncio.gather(*tasks, loop=loop)


app = init_app()
web.run_app(app, host='0.0.0.0', port=10080)
