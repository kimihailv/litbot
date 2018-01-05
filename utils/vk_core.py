from aiohttp import FormData
from globals import session
from time import time
from urllib import parse
import re


class VkApi:
    _API_TOKEN = '<group token>'
    _API_USER_TOKEN = '<personal token (for wiki pages)>'
    _SECRET = '<secret>'
    _URL_BASE = 'https://api.vk.com/method/{}'
    _API_VERSION = '5.69'

    @staticmethod
    async def call_method(method_name, params, http_method='get', need_auth=False):
        params['access_token'] = VkApi._API_TOKEN if not need_auth else VkApi._API_USER_TOKEN
        params['v'] = VkApi._API_VERSION
        if http_method == 'get':
            url = VkApi._URL_BASE.format(method_name)
            return await session.get(url, params=params)
        else:
            url = VkApi._URL_BASE.format(method_name)
            return await session.post(url, data=VkApi.create_form_data(params))

    async def send_answer(self, message, answer):
        method_name = 'messages.send'
        user_id = message['user_id']
        random_id = VkApi.gen_random_id(user_id)
        params = {'user_id': user_id,
                  'peer_id': user_id,
                  'message': answer,
                  'random_id': random_id}
        await self.mark_as_read(message)
        r = await self.call_method(method_name, params, 'post')
        print(await r.json())

    async def send_messages(self, users, message):
        method_name = 'messages.send'
        random_id = VkApi.gen_random_id(users[0])
        params = {'user_ids': users,
                  'message': message,
                  'random_id': random_id}
        r = await self.call_method(method_name, params, 'post')
        print(await r.json())

    async def send_attach(self, message, attach):
        method_name = 'messages.send'
        user_id = message['user_id']
        random_id = VkApi.gen_random_id(user_id)
        params = {'user_id': user_id,
                  'peer_id': user_id,
                  'attachment': attach,
                  'message': '',
                  'random_id': random_id}
        await self.mark_as_read(message)
        r = await self.call_method(method_name, params, 'post')
        print(await r.json())

    async def mark_as_read(self, message):
        method_name = 'messages.markAsRead'
        params = {'peer_id': message['user_id'],
                  'start_message_id': message['id']}
        await self.call_method(method_name, params)

    async def set_activity(self, message):
        method_name = 'messages.setActivity'
        params = {'user_id': message['user_id'], 'type': 'typing'}
        await self.call_method(method_name, params)

    @staticmethod
    async def get_history(message, count, offset):
        method_name = 'messages.getHistory'
        user_id = message['object']['user_id'] if 'object' in message else message['user_id']
        params = {'user_id': user_id, 'count': count, 'start_message_id': message['id'], 'offset': offset}
        response = await VkApi.call_method(method_name, params)
        return await response.json()

    @staticmethod
    def gen_random_id(data):
        timestamp = time()
        return int(timestamp + data)

    @staticmethod
    async def get_short_link(url):
        method_name = 'utils.getShortLink'
        params = {'url': url}
        response = await VkApi.call_method(method_name, params)
        json = await response.json()
        if 'response' in json:
            if 'short_url' in json['response']:
                return json['response']['short_url']
        return 'link is not found'

    @staticmethod
    def create_form_data(data):
        form_data = FormData()
        for k, v in data.items():
            form_data.add_field(k, str(v))

        return form_data

    @staticmethod
    def verify_request(request):
        return request['secret'] == VkApi._SECRET

    @staticmethod
    async def create_page(message, content, date):
        method_name = 'pages.save'
        title = 'ДЗ на {} [{}]'.format(date, message['user_id'])
        params = {'text': content,
                  'group_id': '155822098',
                  'title': title}
        r = await VkApi.call_method(method_name, params, 'post', True)
        r = await r.json()
        return 'https://vk.com/pages?oid=-155822098&{}'.format(parse.urlencode({'p': title}))

    @staticmethod
    async def get_members():
        method_name = 'groups.getMembers'
        params = {'group_id': 155822098}
        r = await VkApi.call_method(method_name, params, need_auth=True)
        return await r.json()


class Bot:
    commands = ['reg', 'help', 'дз', 'edit']

    help_text_full = '1) Хотите заполнить данные о Ваших учителях, чтобы получать самое нужное? ' \
                     'Отправьте сообщение с командой /edit\n' \
                     '2) Чтобы зарегистрироваться, отправьте сообщение с командой /reg и номером группы, ' \
                     'например: /reg 11.4\n' \
                     '3) Чтобы получить дз на завтра, отправьте сообщение с командой /дз (возвращает дз на завтра)\n' \
                     '4) Чтобы получить дз на конкретную дату, отправьте сообщение с командой ' \
                     '/дз и датой в формате дд.мм, например: /дз 05.09 (дз на 5 сентября).\n' \
                     'Или можно использовать ключевые слова: пн, вт, ср, чт, пн, сб. ' \
                     'Например, /дз пт вернет вам дз на пятницу.\n' \
                     '5) Чтобы получить справку, отправьте сообщение с командой /help'

    help_text_short = '1) Хотите заполнить данные о Ваших учителях, чтобы получать самое нужное? ' \
                      'Отправьте сообщение с командой /edit\n' \
                      '2) Чтобы получить дз на завтра, отправьте сообщение с командой /дз (возвращает дз на завтра)\n' \
                      '3) Чтобы получить дз на конкретную дату, отправьте сообщение с командой ' \
                      '/дз и датой в формате дд.мм, например: /дз 05.09 (дз на 5 сентября).\n' \
                      'Или можно использовать ключевые слова: пн, вт, ср, чт, пн, сб.\n' \
                      'Например, /дз пт вернет вам дз на пятницу.\n' \
                      '4) Чтобы получить справку, отправьте сообщение с командой /help'

    def __init__(self, vk_api):
        self.vk_api = vk_api
        self.handlers = {}

    async def handle_message(self, message):
        pattern = r'/\b(\S+)(?:\s)?(\S+)?\b'
        match = re.match(pattern, message['body'])
        if match is not None:
            print(match.groups())
            cmd = match.group(1)
            arg = match.group(2)
            if cmd in self.commands:
                if cmd == 'help' or cmd == 'edit':
                    await self.handlers[cmd](message)
                elif cmd == 'reg':
                    if arg is not None:
                        await self.handlers[cmd + '_arg'](message, arg)
                elif cmd == 'дз':
                    await self.handlers[cmd](message, arg)
            else:
                await self.send_help(message, 'short')

        else:
            if message['body'].isdigit():
                previous = await self.vk_api.get_history(message, 1, 1)
                previous = previous['response']['items'][0]
                if previous['out'] == 1:
                    if '[' in previous['body']:
                        section_data = re.findall(r'\[(.+?)\]\[(.+?)\]', previous['body'])[0]
                        print(section_data)
                        await self.handlers[section_data[0]](message, section_data[1])
            else:
                await self.send_help(message, 'short')

    def add_handler(self, command, handler):
        self.handlers[command] = handler

    async def send_answer(self, message, answer):
        await self.vk_api.send_answer(message, answer)

    async def send_reg_request(self, message):
        await self.vk_api.send_answer(message, 'Хмм, похоже Вы не зарегистрированы, '
                                               'для регистрации отправьте сообщение с командой /reg и номером группы, '
                                               'например: /reg 11.4')

    async def send_sorry(self, message):
        await self.vk_api.send_answer(message, 'Хьюстон, у нас проблемы! Попробуйте позже.')

    async def send_help(self, message, type):
        if type == 'short':
            await self.vk_api.send_answer(message, self.help_text_short)
        else:
            await self.vk_api.send_answer(message, self.help_text_full)

    async def send_success_reg(self, message):
        await self.vk_api.send_answer(message, 'Отлично, Вы зарегистрированы!\n\n{}'.format(self.help_text_short))

    async def notify(self, message):
        await self.vk_api.set_activity(message['object'])
        await self.handle_message(message['object'])

    async def send_attach(self, message, attach):
        await self.vk_api.send_attach(message, attach)
