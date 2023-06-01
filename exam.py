from typing import Union, List

from cqwu.errors import UsernameOrPasswordError, NeedCaptchaError, NoExamData
from cqwu.types import AiExam
from nonebot import on_command
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageSegment,
)
from nonebot_plugin_htmlrender import template_to_pic

from .data import cqwu_data, PLUGIN_RES_PATH
from .utils import get_exam

exam_cqwu_title = "2022-2023 学年第二学期"
exam_cqwu = on_command("cqwu_exam", aliases={"考试查询"}, priority=4, block=False)
exam_cqwu.__help_name__ = "查询考试"
exam_cqwu.__help_info__ = "查询考试排期。"


@exam_cqwu.handle()
async def handle_first_receive(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if not cqwu_data.has_user(int(event.user_id)):
        await exam_cqwu.finish("⚠️请先使用命令 /cqwu_login 登录网上办事大厅。")
    client = cqwu_data.get_user(int(event.user_id))
    pic = None
    try:
        data: List[AiExam] = await get_exam(client)
        if not data:
            raise NoExamData
        data.sort(key=lambda x: x.get_time()[0])
        data_list = [data[i : i + 3] for i in range(0, len(data), 3)]
        pic = await template_to_pic(
            template_path=PLUGIN_RES_PATH,
            template_name="exam.jinja2",
            templates={
                "title": exam_cqwu_title,
                "data_list": data_list,
            },
            pages={
                "viewport": {"width": 1440, "height": 1000},
                "base_url": f"file://{PLUGIN_RES_PATH}",
            },
        )
    except UsernameOrPasswordError:
        await exam_cqwu.finish("⚠️查询失败，用户名或密码错误，请先使用命令 /cqwu_login 重新登录")
    except NeedCaptchaError:
        await exam_cqwu.finish("⚠️查询失败，需要验证码，请先正确登录一次网上办事大厅")
    except NoExamData:
        await exam_cqwu.finish("⚠️没有你的考试信息，可能还未发布。")
    except Exception as e:
        await exam_cqwu.finish(f"⚠️查询失败，请稍后重试，{type(e)}")
    if pic:
        await exam_cqwu.finish(MessageSegment.image(pic))
