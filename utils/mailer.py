from utils import vk_core
from asyncio import get_event_loop

loop = get_event_loop()
vk_api = vk_core.VkApi()

message = 'Привет! У нас есть парочка новых плюшек для вас:\n' \
          '* Теперь получать дз можно с помощью команды /дз\n' \
          '* Получайте дз на желаемые дни с помощью слов: пн, вт, ср, чт, пн, сб.\n' \
          'Например, /дз пт вернет вам дз на пятницу.'


async def broadcast():
    members = (await vk_core.VkApi.get_members())['response']['items']
    print(members)
    await vk_api.send_messages(members, message)

loop.run_until_complete(broadcast())