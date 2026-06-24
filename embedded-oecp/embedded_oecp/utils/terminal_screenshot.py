# **********************************************************************************
# Copyright (c) Huawei Technologies Co., Ltd. 2026-2026. All rights reserved.
# [embedded-oecp] is licensed under the Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#     http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT, MERCHANTABILITY OR FIT FOR A PARTICULAR
# PURPOSE.
# See the Mulan PSL v2 for more details.
# Author: lixinyu
# Create: 2025-01-01
# Description: embedded-oecp utility
# **********************************************************************************
import os
import datetime
from embedded_oecp.utils.logger import get_logger


def render_terminal_screenshot(
    title: str,
    lines: list,
    output_path: str,
    **kwargs,
):
    width = kwargs.get("width", 1200)
    prompt = kwargs.get("prompt", "$ ")
    show_header = kwargs.get("show_header", True)
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False

    logger = get_logger()

    font = _load_font(16)
    font_title = _load_font(13)
    font_small = _load_font(12)

    padding_x = 20
    padding_y = 16
    title_bar_h = 32
    line_h = 22
    bottom_bar_h = 24

    max_line_w = 0
    for line in lines:
        text = line.get("text", "")
        tw = _text_width(text, font, padding_x)
        if tw > max_line_w:
            max_line_w = tw

    img_w = max(width, max_line_w + padding_x * 2)
    content_h = len(lines) * line_h
    img_h = padding_y + title_bar_h + padding_y + content_h + padding_y + bottom_bar_h

    img = Image.new("RGB", (img_w, img_h), "#1e1e2e")
    draw = ImageDraw.Draw(img)

    if show_header:
        draw.rectangle([(0, 0), (img_w, title_bar_h)], fill="#313244")
        draw.text((padding_x, 8), f" {title}", fill="#cdd6f4", font=font_title)
        btn_y = 10
        for color in ["#f38ba8", "#f9e2af", "#a6e3a1"]:
            draw.ellipse([(img_w - 70, btn_y), (img_w - 56, btn_y + 14)], fill=color)
            img_w_local = img_w
            btn_y_draw = btn_y
            btn_y += 0

        for i, c in enumerate(["#f38ba8", "#f9e2af", "#a6e3a1"]):
            draw.ellipse([(img_w - 70 + i * 18, 10), (img_w - 56 + i * 18, 24)], fill=c)

    y = padding_y + title_bar_h + padding_y

    for line_data in lines:
        text = line_data.get("text", "")
        color = line_data.get("color", "#cdd6f4")
        line_font = font

        if line_data.get("type") == "prompt":
            draw.text((padding_x, y), prompt, fill="#a6e3a1", font=line_font)
            draw.text((padding_x + _text_width(prompt, line_font, 0), y), text, fill="#cdd6f4", font=line_font)
        elif line_data.get("type") == "command":
            draw.text((padding_x, y), prompt, fill="#a6e3a1", font=line_font)
            draw.text((padding_x + _text_width(prompt, line_font, 0), y), text, fill="#f9e2af", font=line_font)
        elif line_data.get("type") == "highlight":
            draw.text((padding_x, y), text, fill=color, font=line_font)
        elif line_data.get("type") == "success":
            draw.text((padding_x, y), f"✓ {text}", fill="#a6e3a1", font=line_font)
        elif line_data.get("type") == "error":
            draw.text((padding_x, y), f"✗ {text}", fill="#f38ba8", font=line_font)
        else:
            draw.text((padding_x, y), text, fill=color, font=line_font)

        y += line_h

    draw.rectangle([(0, img_h - bottom_bar_h), (img_w, img_h)], fill="#313244")
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    draw.text((padding_x, img_h - bottom_bar_h + 5), f"embedded-oecp | {ts}", fill="#6c7086", font=font_small)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    img.save(output_path, "PNG")
    logger.info(f"Terminal screenshot saved: {output_path}")
    return True


def _load_font(size: int):
    from PIL import ImageFont

    cjk_paths = [
        ("/usr/share/fonts/opentype/noto/NotoSansMonoCJK-Regular.ttc", 2),
        ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 2),
        ("/usr/share/fonts/noto-cjk/NotoSansMonoCJKsc-Regular.otf", 0),
        ("/usr/share/fonts/truetype/noto/NotoSansCJKsc-Regular.ttf", 0),
    ]
    for path, index in cjk_paths:
        try:
            return ImageFont.truetype(path, size, index=index)
        except Exception:
            pass

    mono_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
    ]
    for path in mono_paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass

    return ImageFont.load_default()


def _text_width(text: str, font, extra: int = 0) -> int:
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0] + extra
    except Exception:
        return len(text) * 9 + extra
