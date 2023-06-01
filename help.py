from typing import Union

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent

cqwu_help_t = "重文理帮助"
cqwu_help = on_command("cqwu", aliases={cqwu_help_t}, priority=4, block=False)
cqwu_help.__help_name__ = cqwu_help_t
cqwu_help.__help_info__ = cqwu_help_t


@cqwu_help.handle()
async def handle_first_receive(_: Union[GroupMessageEvent, PrivateMessageEvent]):
    await cqwu_help.finish(
        "重文理帮助\n\n"
        "/cqwu_login 登录账号\n"
        "/cqwu_score 查询期末成绩\n"
        "/cqwu_balance 查询校园卡余额\n"
        "/cqwu_calendar 查询本学期课表\n"
        "/cqwu_calendar_change 查询本学期调课\n"
        "/cqwu_exam 查询本学期考试安排"
    )
