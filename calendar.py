from typing import Union

from cqwu.errors import UsernameOrPasswordError, NeedCaptchaError
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent, MessageSegment
from nonebot_plugin_htmlrender import html_to_pic

from .data import cqwu_data, DATA_PATH
from .utils import get_calendar


calendar_cqwu = on_command('cqwu_calendar', aliases={"课表查询"}, priority=4, block=True)
calendar_cqwu.__help_name__ = '查询课表'
calendar_cqwu.__help_info__ = '查询本学期课表。'


@calendar_cqwu.handle()
async def handle_first_receive(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if not cqwu_data.has_user(int(event.user_id)):
        await calendar_cqwu.finish("⚠️请先使用命令 /cqwu_login 登录网上办事大厅。")
    client = cqwu_data.get_user(int(event.user_id))
    pic = None
    try:
        html = await get_calendar(client)
        pic = await html_to_pic(html, template_path=f"file://{DATA_PATH}")
    except UsernameOrPasswordError:
        await calendar_cqwu.finish("⚠️查询失败，用户名或密码错误，请先使用命令 /cqwu_login 重新登录")
    except NeedCaptchaError:
        await calendar_cqwu.finish("⚠️查询失败，需要验证码，请先正确登录一次网上办事大厅")
    except Exception as e:
        await calendar_cqwu.finish(f"⚠️查询失败，请稍后重试，{type(e)}")
    if pic:
        await calendar_cqwu.finish(MessageSegment.image(pic))
