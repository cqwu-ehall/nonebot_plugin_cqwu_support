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
