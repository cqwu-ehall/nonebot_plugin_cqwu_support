import json
from typing import Union, List, Tuple

from cqwu.errors import UsernameOrPasswordError, NeedCaptchaError
from cqwu.types.calendar import AiCourse
from nonebot import on_command, get_bot
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageSegment,
)
from nonebot_plugin_apscheduler import scheduler

from .data import cqwu_data, DATA_PATH
from .html import html_to_pic
from .utils import get_calendar, get_calendar_change

calendar_cqwu = on_command("cqwu_calendar", aliases={"课表查询"}, priority=4, block=True)
calendar_cqwu.__help_name__ = "查询课表"
calendar_cqwu.__help_info__ = "查询本学期课表。"
calendar_change_cqwu = on_command(
    "cqwu_calendar_change", aliases={"调课查询"}, priority=4, block=True
)
calendar_change_cqwu.__help_name__ = "查询调课"
calendar_change_cqwu.__help_info__ = "查询本学期调课。"
calendar_refresh_cqwu = on_command("cqwu_calendar_refresh", priority=4, block=True)
CALENDAR_DATA_PATH = DATA_PATH / "calendar"
CALENDAR_DATA_PATH.mkdir(exist_ok=True, parents=True)


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


@calendar_change_cqwu.handle()
async def handle_first_receive(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if not cqwu_data.has_user(int(event.user_id)):
        await calendar_cqwu.finish("⚠️请先使用命令 /cqwu_login 登录网上办事大厅。")
    client = cqwu_data.get_user(int(event.user_id))
    pic = None
    try:
        html = await get_calendar_change(client)
        html = html.replace("../css/Print.css", "Print.css")
        pic = await html_to_pic(html, template_path=f"file://{DATA_PATH}")
    except UsernameOrPasswordError:
        await calendar_cqwu.finish("⚠️查询失败，用户名或密码错误，请先使用命令 /cqwu_login 重新登录")
    except NeedCaptchaError:
        await calendar_cqwu.finish("⚠️查询失败，需要验证码，请先正确登录一次网上办事大厅")
    except Exception as e:
        await calendar_cqwu.finish(f"⚠️查询失败，请稍后重试，{type(e)}")
    if pic:
        await calendar_cqwu.finish(MessageSegment.image(pic))


class CalendarData:
    @staticmethod
    def get_old_data(uid: int) -> List[AiCourse]:
        path = CALENDAR_DATA_PATH / f"{uid}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return [AiCourse(**i) for i in json.load(f)]
        return []

    @staticmethod
    def save_data(uid: int, data: List[AiCourse]):
        path = CALENDAR_DATA_PATH / f"{uid}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump([i.dict() for i in data], f, ensure_ascii=False, indent=4)

    @staticmethod
    def get_data(
        old_data: List[AiCourse], new_data: List[AiCourse]
    ) -> Tuple[List[AiCourse], List[AiCourse]]:
        old_data_map = {i.key: i for i in old_data}
        new_data_map = {i.key: i for i in new_data}
        old_result, new_result = [], []
        for key, value in new_data_map.items():
            if key not in old_data_map:
                new_result.append(value)
        for key, value in old_data_map.items():
            if key not in new_data_map:
                old_result.append(value)
        return new_result, old_result

    @staticmethod
    def format_course(course: AiCourse):
        end_num = course.start_num + course.sections - 1
        num = (
            course.start_num
            if course.sections == 1
            else f"{course.start_num}-{end_num}"
        )
        weeks = ",".join([str(i) for i in course.weeks])
        return f"{course.name} {course.position} 星期{course.day} 第{num}节 [{weeks}]"

    @staticmethod
    def format_text(old_data: List[AiCourse], new_data: List[AiCourse]):
        text = "⚠️课表有变动⚠️"
        if old_data:
            text += "\n\n旧课程：\n"
            for i in old_data:
                text += f"{CalendarData.format_course(i)}\n"
        if new_data:
            text += "\n\n新课程：\n"
            for i in new_data:
                text += f"{CalendarData.format_course(i)}\n"
        return text.strip()


@scheduler.scheduled_job("cron", hour=12, minute=0, id="cqwu.calendar.12")
@scheduler.scheduled_job("cron", hour=18, minute=0, id="cqwu.calendar.18")
async def update_cqwu_calendar():
    bot = get_bot()
    for key, value in cqwu_data.users.items():
        try:
            old_courses = CalendarData.get_old_data(int(key))
            new_courses = await get_calendar(value, use_model=True)
            new_result, old_result = CalendarData.get_data(old_courses, new_courses)
            if (len(new_result) != 0 or len(old_result) != 0) and len(old_courses) != 0:
                await bot.send_private_msg(
                    user_id=int(key),
                    message=CalendarData.format_text(old_result, new_result),
                )
            CalendarData.save_data(int(key), new_courses)
        except Exception as e:
            print(e)
            continue


@calendar_refresh_cqwu.handle()
async def handle_first_receive():
    await update_cqwu_calendar()
    await calendar_cqwu.finish("手动刷新完成。")
