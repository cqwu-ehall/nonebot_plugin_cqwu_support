from typing import List, Union

from cqwu import Client
from cqwu.errors import CookieError, NoExamData
from cqwu.types import AiExam
from cqwu.types.calendar import AiCourse
from cqwu.types.score import Score


async def get_score(client: Client) -> List[Score]:
    try:
        return await client.get_score()
    except CookieError:
        await client.login_with_password()
        return await client.get_score()


async def get_balance(client: Client) -> str:
    try:
        return await client.get_balance()
    except CookieError:
        await client.login_with_password()
        return await client.get_balance()


async def get_calendar(
    client: Client, use_model: bool = False
) -> Union[str, List[AiCourse]]:
    try:
        if not client.web_ehall_path:
            raise CookieError()
        return await client.get_calendar(use_model=use_model)
    except CookieError:
        await client.login_with_password()
        await client.login_web_vpn()
        return await client.get_calendar(use_model=use_model)


async def get_calendar_change(client: Client) -> str:
    try:
        if not client.web_ehall_path:
            raise CookieError()
        return await client.get_calendar_change()
    except CookieError:
        await client.login_with_password()
        await client.login_web_vpn()
        return await client.get_calendar_change()


async def get_exam(client: Client, need_exit: bool = False) -> List[AiExam]:
    try:
        if not client.web_ehall_path:
            raise CookieError()
        data: List[AiExam] = []
        action = await client.get_exam_calendar_action()
        rounds = [action.scattered, action.concentration]
        for r in rounds:
            try:
                data.extend(await client.get_exam_calendar(r, use_model=True))
            except NoExamData:
                pass
        return data
    except CookieError:
        if need_exit:
            return []
        await client.login_with_password()
        await client.login_web_vpn()
        return await get_exam(client, need_exit=True)
