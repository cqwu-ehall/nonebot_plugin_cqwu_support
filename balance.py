from typing import Union

from cqwu.errors.auth import NeedCaptchaError, UsernameOrPasswordError

from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent

from .utils import get_balance
from .data import cqwu_data

cqwu_balance = on_command('cqwu_balance', aliases={"校园卡余额"}, priority=4, block=True)
cqwu_balance.__help_name__ = '查询校园网余额'
cqwu_balance.__help_info__ = '查询校园网余额'


@cqwu_balance.handle()
async def handle_first_receive(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if not cqwu_data.has_user(int(event.user_id)):
        await cqwu_balance.finish("⚠️请先使用命令 /cqwu_login 登录网上办事大厅。")
    client = cqwu_data.get_user(int(event.user_id))
    try:
        text = await get_balance(client)
        await cqwu_balance.finish(f"你的校园卡余额为：{text}")
    except UsernameOrPasswordError:
        await cqwu_balance.finish("⚠️查询失败，用户名或密码错误，请先使用命令 /cqwu_login 重新登录")
    except NeedCaptchaError:
        await cqwu_balance.finish("⚠️查询失败，需要验证码，请先正确登录一次网上办事大厅")
    except Exception as e:
        await cqwu_balance.finish(f"⚠️查询失败，请稍后重试，{type(e)}")
