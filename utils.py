from typing import List

from cqwu import Client
from cqwu.errors import CookieError
from cqwu.types.score import Score


async def get_score(client: Client, year: int, semester: int) -> List[Score]:
    try:
        return await client.get_score(year=year, semester=semester)
    except CookieError:
        await client.login_with_password()
        return await client.get_score()


async def get_balance(client: Client) -> str:
    try:
        return await client.get_balance()
    except CookieError:
        await client.login_with_password()
        return await client.get_balance()


async def get_calendar(client: Client) -> str:
    try:
        if not client.web_ehall_path:
            raise CookieError()
        return await client.get_calendar()
    except CookieError:
        await client.login_with_password()
        await client.login_web_vpn()
        return await client.get_calendar()


async def get_calendar_change(client: Client) -> str:
    try:
        if not client.web_ehall_path:
            raise CookieError()
        return await client.get_calendar_change()
    except CookieError:
        await client.login_with_password()
        await client.login_web_vpn()
        return await client.get_calendar_change()
