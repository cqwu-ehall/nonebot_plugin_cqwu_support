import json
from typing import Union, List

from cqwu.errors.auth import NeedCaptchaError, UsernameOrPasswordError
from cqwu.types import Score, ScoreDetailCourse
from nonebot import on_command, get_bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot_plugin_apscheduler import scheduler

from .data import cqwu_data, DATA_PATH
from .utils import get_score, get_score_origin

score_text = "2022-2023 学年第二学期"
score_cqwu = on_command("cqwu_score", aliases={"期末成绩查询"}, priority=4, block=True)
score_cqwu.__help_name__ = "查询成绩"
score_cqwu.__help_info__ = "查询学期成绩。"
score_refresh_cqwu = on_command("cqwu_score_refresh", priority=4, block=True)
USE_ORIGIN = True
SCORE_DATA_PATH = DATA_PATH / "score"
SCORE_DATA_PATH.mkdir(exist_ok=True, parents=True)
SCORE_ORIGIN_DATA_PATH = DATA_PATH / "score_origin"
SCORE_ORIGIN_DATA_PATH.mkdir(exist_ok=True, parents=True)


def get_score_text(client, scores) -> str:
    text = (
        f"📝{client.me.institute} {client.me.now_class} {client.me.name} {score_text}成绩如下：\n\n"
        f"课程名称     成绩   绩点\n"
    )
    temp = "\n".join(
        [f"{score.name}     {score.score}   {score.grade_point}" for score in scores]
    )
    return text + temp


def get_score_origin_text(client, scores: List["ScoreDetailCourse"]) -> str:
    text = (
        f"📝{client.me.institute} {client.me.now_class} {client.me.name} {score_text}成绩如下：\n\n"
        f"课程名称     原始成绩\n"
    )
    temp = "\n".join(
        [f"{score.name}     {score.score}" for score in scores]
    )
    return text + temp


@score_cqwu.handle()
async def handle_first_receive(event: Union[GroupMessageEvent, PrivateMessageEvent]):
    if not cqwu_data.has_user(int(event.user_id)):
        await score_cqwu.finish("⚠️请先使用命令 /cqwu_login 登录网上办事大厅。")
    client = cqwu_data.get_user(int(event.user_id))
    scores = []
    text = ""
    try:
        if USE_ORIGIN:
            scores = await get_score_origin(client)
            text = get_score_origin_text(client, scores)
        else:
            scores = await get_score(client)
            text = get_score_text(client, scores)
    except UsernameOrPasswordError:
        await score_cqwu.finish("⚠️查询失败，用户名或密码错误，请先使用命令 /cqwu_login 重新登录")
    except NeedCaptchaError:
        await score_cqwu.finish("⚠️查询失败，需要验证码，请先正确登录一次网上办事大厅")
    except Exception as e:
        await score_cqwu.finish(f"⚠️查询失败，请稍后重试，{type(e)}")
    if len(scores) == 0:
        await score_cqwu.finish(f"⚠️查询失败，没有找到 {score_text} 的成绩")
    if text:
        await score_cqwu.finish(text)


class ScoreData:
    @staticmethod
    def get_old_data(uid: int) -> List[Union[Score, ScoreDetailCourse]]:
        if USE_ORIGIN:
            path = SCORE_ORIGIN_DATA_PATH / f"{uid}.json"
            model = ScoreDetailCourse
        else:
            path = SCORE_DATA_PATH / f"{uid}.json"
            model = Score
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return [model(**i) for i in json.load(f)]
        return []

    @staticmethod
    def save_data(uid: int, data: List[Union[Score, ScoreDetailCourse]]):
        if USE_ORIGIN:
            path = SCORE_ORIGIN_DATA_PATH / f"{uid}.json"
        else:
            path = SCORE_DATA_PATH / f"{uid}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump([i.dict() for i in data], f, ensure_ascii=False, indent=4)

    @staticmethod
    def get_data(
        old_data: List[Union[Score, ScoreDetailCourse]], new_data: List[Union[Score, ScoreDetailCourse]]
    ) -> List[Union[Score, ScoreDetailCourse]]:
        old_data_map = {i.name: i for i in old_data}
        new_data_map = {i.name: i for i in new_data}
        new_result = []
        for key, value in new_data_map.items():
            if key not in old_data_map:
                new_result.append(value)
        return new_result

    @staticmethod
    def format_text(new_data: Union[List[Score], List[ScoreDetailCourse]]):
        if isinstance(new_data[0], Score):
            return ScoreData.format_score_text(new_data)
        else:
            return ScoreData.format_origin_text(new_data)

    @staticmethod
    def format_score_text(new_data: List[Score]) -> str:
        text = "⚠️成绩有变动⚠️"
        text += "\n\n课程名称     成绩   绩点\n"
        for score in new_data:
            text += f"{score.name}     {score.score}   {score.grade_point}\n"
        return text.strip()

    @staticmethod
    def format_origin_text(new_data: List[ScoreDetailCourse]) -> str:
        text = "⚠️成绩有变动⚠️"
        text += "\n\n课程名称     原始成绩\n"
        for score in new_data:
            text += f"{score.name}     {score.score}\n"
        return text.strip()


@scheduler.scheduled_job("interval", hours=1, id="cqwu.score")
async def update_cqwu_score():
    bot = get_bot()
    for key, value in cqwu_data.users.items():
        try:
            old_scores = ScoreData.get_old_data(int(key))
            if USE_ORIGIN:
                new_scores = await get_score_origin(value)
            else:
                new_scores = await get_score(value)
            if len(new_scores) == 0:
                continue
            new_result = ScoreData.get_data(old_scores, new_scores)
            if (len(new_result) != 0) and len(old_scores) != 0:
                await bot.send_private_msg(
                    user_id=int(key),
                    message=ScoreData.format_text(new_result),
                )
            ScoreData.save_data(int(key), new_scores)
        except Exception as e:
            print(e)
            continue


@score_refresh_cqwu.handle()
async def handle_first_receive():
    await update_cqwu_score()
    await score_refresh_cqwu.finish("手动刷新完成。")
