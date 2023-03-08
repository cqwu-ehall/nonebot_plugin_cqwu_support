from typing import Union

from cqwu.errors.auth import NeedCaptchaError, UsernameOrPasswordError

from nonebot import on_command, get_bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot_plugin_apscheduler import scheduler

from .utils import get_score
from .data import cqwu_data

score_year = 2022
score_semester = 1
score_text = "2022-2023 学年第一学期"
score_cqwu = on_command('cqwu_score', aliases={"期末成绩查询"}, priority=4, block=True)
score_cqwu.__help_name__ = '查询成绩'
score_cqwu.__help_info__ = '查询学期成绩。'


def get_score_text(client, scores) -> str:
    text = f"📝{client.me.institute} {client.me.now_class} {client.me.name} {score_text}成绩如下：\n\n" \
           f"课程名称     成绩   绩点\n"
    temp = "\n".join([f"{score.name}     {score.score}   {score.grade_point}" for score in scores])
    return text + temp


@score_cqwu.handle()
async def handle_first_receive(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if not cqwu_data.has_user(int(event.user_id)):
        await score_cqwu.finish("⚠️请先使用命令 /cqwu_login 登录网上办事大厅。")
    client = cqwu_data.get_user(int(event.user_id))
    scores = []
    try:
        scores = await get_score(client, year=2022, semester=1)
    except UsernameOrPasswordError:
        await score_cqwu.finish("⚠️查询失败，用户名或密码错误，请先使用命令 /cqwu_login 重新登录")
    except NeedCaptchaError:
        await score_cqwu.finish("⚠️查询失败，需要验证码，请先正确登录一次网上办事大厅")
    except Exception as e:
        await score_cqwu.finish(f"⚠️查询失败，请稍后重试，{type(e)}")
    if len(scores) == 0:
        await score_cqwu.finish(f"⚠️查询失败，没有找到 {score_text} 的成绩")
    await score_cqwu.finish(get_score_text(client, scores))


@scheduler.scheduled_job("interval", hours=1, id="cqwu.score")
async def update_cqwu_score():
    bot = get_bot()
    for key, value in cqwu_data.users.items():
        old_value = cqwu_data.scores.get(key, 0)
        try:
            scores = await get_score(value, year=score_year, semester=score_semester)
            new_value = len(scores)
            if old_value not in [0, new_value]:
                await bot.send_private_msg(
                    user_id=int(key),
                    message=get_score_text(value, scores)
                )
            if new_value != 0:
                cqwu_data.scores[key] = new_value
        except Exception as e:
            print(e)
            continue
