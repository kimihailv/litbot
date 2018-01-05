from aiohttp import ClientSession
from asyncio import get_event_loop
import aiomysql
from os import path

loop = get_event_loop()
session = None
pool = None
root = path.abspath(path.dirname(__file__))
db_full_path = path.join(root, 'dbs/storage.db')

async def init_common():
    global pool, session
    session = ClientSession()
    pool = await aiomysql.create_pool(host='0.0.0.0',
                                      user='user', password='',
                                      db='', charset='utf8', use_unicode=True, loop=loop)
loop.run_until_complete(init_common())