from urllib.parse import urlparse
from redis import Redis
from pyrogram.types import CallbackQuery
from pyrogram import filters

CONTEXT_NAMES = [
    'INITIALIZE',
    'SETTINGS',
    'LIST',
    'SELECT_DIRECTORY',
    'IDLE',
    'UPLOAD_FILE',
    'UPLOAD_URL',
]

CONTEXT = {v: 1 << k for k, v in enumerate(CONTEXT_NAMES)}

class UserContext(object):
    def __init__(self, db: int = 0, **kwargs):
        ret = urlparse(kwargs.get('config')['redis']['host'])

        self._redis = Redis(host=ret.hostname,
                            port=ret.port if ret.port != 80 else 6379,
                            username=ret.username,
                            password=ret.password,
                            db=db)

    def update(self, id: int, context: int) -> bool:
        assert isinstance(context, int)
        return self.__redis.set(f'ctx:{id}', context)

    def resolve(self, id: int) -> int:
        if self.__redis.exists(f'ctx:{id}'):
            return int(self.__redis.get(f'ctx:{id}'))
        return 0

    def filter(self, data):
        async def func(flt, _, query: CallbackQuery):
            ctx = self.resolve(query.from_user.id)
            return (ctx & flt.data) != 0

        return filters.create(func, data=data)
