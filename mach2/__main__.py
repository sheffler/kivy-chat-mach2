import os
import asyncio

from .kivy_chat_app import ChatApp

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(ChatApp().async_run(async_lib='asyncio'))
    loop.close()
