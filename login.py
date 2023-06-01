from typing import Union

from cqwu import Client
from cqwu.errors import NeedCaptchaError, UsernameOrPasswordError
from nonebot import on_command
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot.internal.params import ArgPlainText
from nonebot.typing import T_State

from .data import cqwu_data

login_cqwu = on_command("cqwu_login", priority=4, block=True)
login_cqwu.__help_name__ = "登录网上办事大厅"
login_cqwu.__help_info__ = "跟随指引，通过学号+密码的方式登录网上办事大厅。"


@login_cqwu.handle()
async def handle_first_receive(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if isinstance(event, GroupMessageEvent):
        await login_cqwu.finish("⚠️为了保护您的隐私，请添加机器人好友后私聊进行登录。")
    await login_cqwu.send(
        """\
            登录过程概览：\
            \n1.发送学号\
            \n2.发送网上办事大厅密码\
            \n🚪过程中发送“退出”即可退出\
                """.strip()
    )


@login_cqwu.got("学号", prompt="1.请发送您的学号：")
async def _(
    __: PrivateMessageEvent, state: T_State, username: str = ArgPlainText("学号")
):
    if username == "退出":
        await login_cqwu.finish("🚪已成功退出")
    try:
        username = int(username)
    except Exception:
        await login_cqwu.reject("⚠️学号应为数字，请重新输入")
    if len(str(username)) != 12:
        await login_cqwu.reject("⚠️学号应为12位数字，请重新输入")
    else:
        state["username"] = username


@login_cqwu.got("密码", prompt="2.请发送您的网上办事大厅密码：")
async def _(
    event: PrivateMessageEvent, state: T_State, password: str = ArgPlainText("密码")
):
    if password == "退出":
        await login_cqwu.finish("🚪已成功退出")
    client = Client(username=state["username"], password=password)
    try:
        await client.check_captcha(show_qrcode=False)
    except NeedCaptchaError:
        await login_cqwu.reject("⚠️登录失败，需要验证码，请先正确登录一次网上办事大厅")
    try:
        await client.login_with_password()
    except UsernameOrPasswordError:
        await login_cqwu.reject("⚠️登录失败，用户名或密码错误")
    text = (
        f"欢迎你，{client.me.institute} {client.me.now_class} 的 {client.me.name}，"
        f"你可以使用 /cqwu 查询相关命令。"
    )
    cqwu_data.add_user(
        int(event.user_id), username=state["username"], password=password, client=client
    )
    await login_cqwu.finish(text)
