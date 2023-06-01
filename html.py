from os import getcwd
from typing import Literal, Union, Optional

import jinja2
from nonebot_plugin_htmlrender import get_new_page


class QuerySelectorNotFound(Exception):
    """ 未找到元素 """


async def html_to_pic(
    html: str,
    wait: int = 0,
    template_path: str = f"file://{getcwd()}",
    type: Literal["jpeg", "png"] = "png",
    quality: Union[int, None] = None,
    query_selector: Optional[str] = None,
    **kwargs,
) -> bytes:
    """html转图片

    Args:
        html (str): html文本
        wait (int, optional): 等待时间. Defaults to 0.
        template_path (str, optional): 模板路径 如 "file:///path/to/template/"
        type (Literal["jpeg", "png"]): 图片类型, 默认 png
        quality (int, optional): 图片质量 0-100 当为`png`时无效
        query_selector (Optional[str], optional): 选择器, 用于选择需要截图的元素. Defaults to None.
        **kwargs: 传入 page 的参数

    Returns:
        bytes: 图片, 可直接发送
    """
    # logger.debug(f"html:\n{html}")
    if "file:" not in template_path:
        raise Exception("template_path 应该为 file:///path/to/template")
    async with get_new_page(**kwargs) as page:
        await page.goto(template_path)
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(wait)
        clip = None
        if query_selector:
            try:
                card = await page.query_selector(query_selector)
                if not card:
                    raise QuerySelectorNotFound
                clip = await card.bounding_box()
                if not clip:
                    raise QuerySelectorNotFound
            except QuerySelectorNotFound:
                pass
        img_raw = await page.screenshot(
            clip=clip,
            full_page=True,
            type=type,
            quality=quality,
        )
    return img_raw


async def template_to_pic(
    template_path: str,
    template_name: str,
    templates: dict,
    pages: dict = None,
    wait: int = 0,
    type: Literal["jpeg", "png"] = "png",
    quality: Union[int, None] = None,
    query_selector: Optional[str] = None,
) -> bytes:
    """使用jinja2模板引擎通过html生成图片

    Args:
        template_path (str): 模板路径
        template_name (str): 模板名
        templates (dict): 模板内参数 如: {"name": "abc"}
        pages (dict): 网页参数 Defaults to
            {"base_url": f"file://{getcwd()}", "viewport": {"width": 500, "height": 10}}
        wait (int, optional): 网页载入等待时间. Defaults to 0.
        type (Literal["jpeg", "png"]): 图片类型, 默认 png
        quality (int, optional): 图片质量 0-100 当为`png`时无效
        query_selector (Optional[str], optional): 选择器, 用于选择需要截图的元素. Defaults to None.

    Returns:
        bytes: 图片 可直接发送
    """

    if pages is None:
        pages = {
            "viewport": {"width": 500, "height": 10},
            "base_url": f"file://{getcwd()}",
        }
    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path),
        enable_async=True,
    )
    template = template_env.get_template(template_name)

    return await html_to_pic(
        template_path=f"file://{template_path}",
        html=await template.render_async(**templates),
        wait=wait,
        type=type,
        quality=quality,
        query_selector=query_selector,
        **pages,
    )
