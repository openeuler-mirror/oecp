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
import asyncio
from embedded_oecp.utils.logger import get_logger


def take_screenshot(url: str, output_path: str, width: int = 1920, height: int = 1080, timeout: int = 30) -> bool:
    logger = get_logger()
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if _pyppeteer_screenshot(url, output_path, width, height, timeout):
        return True

    if _system_browser_screenshot(url, output_path, width, height, timeout):
        return True

    return _render_url_screenshot(url, output_path, width, height)


def _pyppeteer_screenshot(url: str, output_path: str, width: int, height: int, timeout: int) -> bool:
    logger = get_logger()
    try:
        from pyppeteer import launch
    except ImportError:
        return False

    async def _do():
        browser = await launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gpu'],
        )
        page = await browser.newPage()
        await page.setViewport({'width': width, 'height': height})
        await page.goto(url, {'timeout': timeout * 1000, 'waitUntil': 'networkidle2'})
        await page.screenshot({'path': output_path})
        await browser.close()

    try:
        asyncio.get_event_loop().run_until_complete(_do())
        if os.path.isfile(output_path):
            logger.info(f"Pyppeteer screenshot saved: {output_path}")
            return True
    except Exception as e:
        logger.warning(f"Pyppeteer screenshot failed: {e}")
    return False


def _system_browser_screenshot(url: str, output_path: str, width: int, height: int, timeout: int) -> bool:
    import subprocess
    logger = get_logger()
    import shutil
    for browser_cmd in ["chromium-browser", "google-chrome", "chromium"]:
        browser = shutil.which(browser_cmd)
        if browser:
            cmd = [
                browser, "--headless", "--disable-gpu", "--no-sandbox",
                f"--screenshot={output_path}",
                f"--window-size={width},{height}",
                url,
            ]
            try:
                subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
                if os.path.isfile(output_path):
                    logger.info(f"Browser screenshot saved: {output_path}")
                    return True
            except Exception as e:
                logger.warning(f"Browser screenshot failed: {e}")
            break
    return False


def _render_url_screenshot(url: str, output_path: str, width: int, height: int) -> bool:
    logger = get_logger()
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        logger.warning("Pillow not installed, cannot generate screenshot")
        return False

    img = Image.new("RGB", (width, height), "#ffffff")
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except Exception:
        font_title = font_body = font_small = ImageFont.load_default()

    y = 40
    draw.text((40, y), "openEuler Embedded OSV - Evidence (Fallback Render)", fill="#999999", font=font_title)
    y += 50
    draw.text((40, y), f"URL: {url}", fill="#0366d6", font=font_body)
    y += 35
    draw.text((40, y), "(No headless browser available, rendered as fallback)", fill="#999999", font=font_small)

    img.save(output_path, "PNG")
    logger.info(f"Fallback screenshot saved: {output_path}")
    return True


def save_webpage_content(url: str, output_path: str, timeout: int = 30) -> bool:
    import subprocess
    import shutil
    logger = get_logger()
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    curl_path = shutil.which("curl")
    if not curl_path:
        logger.warning("curl not found in PATH")
        return False
    try:
        result = subprocess.run(
            [curl_path, "-sL", "-o", output_path, url],
            capture_output=True, text=True, timeout=timeout,
        )
        if result.returncode == 0 and os.path.isfile(output_path):
            logger.info(f"Webpage saved: {output_path}")
            return True
        return False
    except Exception as e:
        logger.warning(f"Save webpage failed: {e}")
        return False
