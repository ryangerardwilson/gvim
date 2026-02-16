from __future__ import annotations

import json
from pathlib import Path

import config
from design_constants import colors_for


def render_latex_html(source: str, ui_mode: str | None = None) -> str:
    palette = colors_for(ui_mode or config.get_ui_mode() or "dark")
    text_color = palette.webkit_latex_text
    latex = json.dumps(source)
    css_uri = Path(__file__).with_name("katex.min.css").resolve().as_uri()
    js_uri = Path(__file__).with_name("katex.min.js").resolve().as_uri()
    return (
        "<!doctype html>\n"
        "<html>\n"
        "  <head>\n"
        '    <meta charset="utf-8" />\n'
        f'    <link rel="stylesheet" href="{css_uri}" />\n'
        f"    <style>html, body {{ margin: 0; background: transparent; color: {text_color}; overflow: hidden; }}</style>\n"
        "  </head>\n"
        "  <body>\n"
        '    <div id="gvim-latex" style="padding: 1px 12px 1px 10px;"></div>\n'
        f'    <script src="{js_uri}"></script>\n'
        "    <script>\n"
        f"      const latex = {latex};\n"
        "      const target = document.getElementById('gvim-latex');\n"
        "      try {\n"
        "        katex.render(latex, target, { throwOnError: false, displayMode: true });\n"
        "      } catch (err) {\n"
        "        target.textContent = String(err);\n"
        "      }\n"
        "    </script>\n"
        "  </body>\n"
        "</html>\n"
    )
