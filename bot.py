from aiohttp import web
from utils import general, title_parser
from res import data
from tinydb import Query
import datetime
import asyncio


def get_ids(db, subjects):
    q = Query()
    r = []
    for s in subjects:
        ids = map(lambda v: (v['subject_id'], v['teacher_id']), db.search(q.subject.search(s)))
        r.extend(ids)
    return r


def get(grade, group):
    url = 'https://www.lit.msu.ru/api/v1/study/Ulysses/2017–2018/{}/{}/{}/'
    date = datetime.date.today() + datetime.timedelta(days=2)
    subjects = data[grade]['timetable'][group][0].subjects_names
    print(subjects)
    ids = get_ids(data[grade]['courses'], subjects)
    print(ids)
    r = []
    for id_pair in ids:
        r.append(general.fetch(url.format(grade, id_pair[0], id_pair[1])))
    return r

async def handle(request):
    date = datetime.date.today() + datetime.timedelta(days=3)
    requests = await asyncio.gather(*get(11, '11.4'))
    print(title_parser.get_suitable(requests, date, '11.4'))
    return web.Response(text='1')


app = web.Application()
app.router.add_get('/', handle)


web.run_app(app, host='127.0.0.1', port=8080)