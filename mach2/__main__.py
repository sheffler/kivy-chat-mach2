import os
import asyncio
import argparse

from .kivy_chat_app import ChatApp

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog="mach2",
        description="NLIP Chat App"
    )
    parser.add_argument("-p", "--plain", action='store_true', help="Use plain formatting")
    parser.add_argument("-m", "--mock", action='store_true', help="Use Mock response server")

    # Parse the argument from the command line
    cmdargs = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(ChatApp(cmdargs=cmdargs).async_run(async_lib='asyncio'))
    loop.close()
