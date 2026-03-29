#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import subprocess
import textwrap
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOT_DIR = PROJECT_ROOT / "docs" / "screenshots"
SCRIPT_DIR = PROJECT_ROOT / ".local" / "runtime" / "capture_scripts"
SUBMISSION_DIR = PROJECT_ROOT / ".local" / "submissions"
NOTES_MD = SUBMISSION_DIR / "live-demo-notes.md"
VENV_ACTIVATE = PROJECT_ROOT / ".local" / "runtime" / "venv" / "bin" / "activate"
BINARY_PATH = PROJECT_ROOT / "sample" / "crackme_mcp"

DEFAULT_REPORT_NAME = "live-demo-report"
DEFAULT_AUTHOR_NAME = "Your Name"
DEFAULT_PROJECT_NAME = "ghidra_hw1_11"
DEFAULT_PROGRAM_NAME = "crackme_mcp"
GHIDRA_HTTP = "http://127.0.0.1:8080/"


def run(cmd: list[str], *, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.stdout


def shell(cmd: str, *, cwd: Path | None = None) -> str:
    proc = subprocess.run(
        ["/bin/bash", "-lc", cmd],
        cwd=str(cwd) if cwd else None,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.stdout


def ensure_dirs() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    SUBMISSION_DIR.mkdir(parents=True, exist_ok=True)


def verify_live_server() -> None:
    out = shell(f"curl -sf {GHIDRA_HTTP}methods?offset=0&limit=3 | sed -n '1,5p'")
    if "No program loaded" in out or not out.strip():
        raise RuntimeError("Live GhidraMCP server is not ready or no program is loaded in the MCP-enabled CodeBrowser.")
    if not VENV_ACTIVATE.exists():
        raise RuntimeError(f"Expected local runtime venv at {VENV_ACTIVATE}")
    if not BINARY_PATH.exists():
        raise RuntimeError(f"Expected sample binary at {BINARY_PATH}")


def write_script(name: str, content: str) -> Path:
    path = SCRIPT_DIR / name
    path.write_text(content)
    path.chmod(0o755)
    return path


def create_scripts() -> dict[str, Path]:
    scripts: dict[str, Path] = {}
    header = f"cd {PROJECT_ROOT}\nsource {VENV_ACTIVATE}\n"

    scripts["task0"] = write_script(
        "task0_tool_call.sh",
        "#!/usr/bin/env bash\n"
        + header
        + "python - <<'PY'\n"
        + "import bridge_mcp_ghidra as b\n"
        + f"b.ghidra_server_url='{GHIDRA_HTTP}'\n"
        + "print('Live GhidraMCP Tool Call')\n"
        + "print('Tool: list_functions()')\n"
        + "print('-' * 60)\n"
        + "for line in b.list_functions()[:20]:\n"
        + "    print(line)\n"
        + "PY\n"
        + "printf '\\nPress Enter to close...'\n"
        + "read -r _\n",
    )

    scripts["task1_functions"] = write_script(
        "task1_functions.sh",
        "#!/usr/bin/env bash\n"
        + header
        + "python - <<'PY'\n"
        + "import bridge_mcp_ghidra as b\n"
        + f"b.ghidra_server_url='{GHIDRA_HTTP}'\n"
        + "print('Task 1 - Function List (first 30)')\n"
        + "print('-' * 60)\n"
        + "for line in b.list_functions()[:30]:\n"
        + "    print(line)\n"
        + "PY\n"
        + "printf '\\nPress Enter to close...'\n"
        + "read -r _\n",
    )

    scripts["task1_verify_format"] = write_script(
        "task1_verify_format.sh",
        "#!/usr/bin/env bash\n"
        + header
        + "python - <<'PY'\n"
        + "import bridge_mcp_ghidra as b\n"
        + f"b.ghidra_server_url='{GHIDRA_HTTP}'\n"
        + "print('Task 1 - Decompile verify_format')\n"
        + "print('-' * 60)\n"
        + "print(b.decompile_function('verify_format'))\n"
        + "PY\n"
        + "printf '\\nPress Enter to close...'\n"
        + "read -r _\n",
    )

    scripts["task2_strings_xrefs"] = write_script(
        "task2_strings_xrefs.sh",
        "#!/usr/bin/env bash\n"
        + header
        + "python - <<'PY'\n"
        + "import bridge_mcp_ghidra as b\n"
        + f"b.ghidra_server_url='{GHIDRA_HTTP}'\n"
        + "print('Task 2 - Strings + Xrefs')\n"
        + "print('-' * 60)\n"
        + "print('Strings matching HINT:')\n"
        + "for line in b.list_strings(filter='HINT')[:10]:\n"
        + "    print(line)\n"
        + "print('\\nXrefs to 0x001020c8:')\n"
        + "for line in b.get_xrefs_to('0x001020c8')[:10]:\n"
        + "    print(line)\n"
        + "PY\n"
        + "printf '\\nPress Enter to close...'\n"
        + "read -r _\n",
    )

    scripts["task2_key_recovery"] = write_script(
        "task2_key_recovery.sh",
        "#!/usr/bin/env bash\n"
        + header
        + "python - <<'PY'\n"
        + "import bridge_mcp_ghidra as b\n"
        + f"b.ghidra_server_url='{GHIDRA_HTTP}'\n"
        + "print('Task 2 - Key Recovery Evidence')\n"
        + "print('-' * 60)\n"
        + "print('[verify_key decompile]')\n"
        + "print(b.decompile_function('verify_key'))\n"
        + "print('\\n[decode_expected_key disassembly excerpt]')\n"
        + "for line in b.disassemble_function('0x001015c8')[:32]:\n"
        + "    print(line)\n"
        + "PY\n"
        + "printf '\\n[rodata bytes near 0x21d0]\\n'\n"
        + f"objdump -s -j .rodata {BINARY_PATH} | sed -n '/21c0/,/21f0/p'\n"
        + "printf '\\n[decoded key from XOR helper]\\n'\n"
        + "python - <<'PY'\n"
        + "ENC = bytes.fromhex('47 49 5a 51 67 69 7a 75 6d 62 63 6e 78 6b 57')\n"
        + "print('mcp key =', ''.join(chr(b ^ 0x2A) for b in ENC))\n"
        + "PY\n"
        + "printf '\\nPress Enter to close...'\n"
        + "read -r _\n",
    )

    scripts["task3_flag"] = write_script(
        "task3_flag.sh",
        "#!/usr/bin/env bash\n"
        + f"cd {PROJECT_ROOT}\n"
        + "printf \"%s\\n\" \"$ ./sample/crackme_mcp 'mcp{MCP_GHIDRA}'\"\n"
        + "./sample/crackme_mcp 'mcp{MCP_GHIDRA}'\n"
        + "printf '\\nPress Enter to close...'\n"
        + "read -r _\n",
    )

    return scripts


def list_windows() -> list[tuple[str, str, str]]:
    out = shell(
        "python3 - <<'PY'\n"
        "import re, subprocess\n"
        "root = subprocess.check_output(['xprop', '-root', '_NET_CLIENT_LIST_STACKING'], text=True)\n"
        "ids = re.findall(r'0x[0-9a-f]+', root)\n"
        "for wid in ids:\n"
        "    try:\n"
        "        name = subprocess.check_output(['xprop', '-id', wid, 'WM_NAME'], text=True, stderr=subprocess.DEVNULL).strip()\n"
        "        cls = subprocess.check_output(['xprop', '-id', wid, 'WM_CLASS'], text=True, stderr=subprocess.DEVNULL).strip()\n"
        "    except subprocess.CalledProcessError:\n"
        "        continue\n"
        "    print(f'{wid}\\t{name}\\t{cls}')\n"
        "PY",
        cwd=PROJECT_ROOT,
    )
    rows = []
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            rows.append((parts[0], parts[1], parts[2]))
    return rows


def wait_for_window(title_fragment: str, timeout: float = 20.0) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        for wid, name, cls in list_windows():
            if title_fragment in name:
                return wid
        time.sleep(0.3)
    raise RuntimeError(f"Timed out waiting for window: {title_fragment}")


def capture_window(window_id: str, output_path: Path) -> None:
    run(["import", "-window", window_id, str(output_path)], cwd=PROJECT_ROOT)


def launch_and_capture(title: str, script_path: Path, output_path: Path) -> None:
    proc = subprocess.Popen(
        ["xterm", "-T", title, "-geometry", "150x44", "-e", "bash", str(script_path)],
        cwd=str(PROJECT_ROOT),
    )
    try:
        window_id = wait_for_window(title, timeout=20)
        time.sleep(2.0)
        capture_window(window_id, output_path)
        shell(f"xkill -id {window_id}", cwd=PROJECT_ROOT)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


def capture_supporting_ghidra_windows(project_name: str, program_name: str) -> dict[str, Path]:
    support: dict[str, Path] = {}
    windows = list_windows()
    for wid, name, _cls in windows:
        if f"Ghidra: {project_name}" in name:
            out = SCREENSHOT_DIR / "00_frontend_server_started.png"
            capture_window(wid, out)
            support["frontend"] = out
        if f"CodeBrowserMCP: {project_name}:/{program_name}" in name:
            out = SCREENSHOT_DIR / "00_codebrowser_mcp_loaded.png"
            capture_window(wid, out)
            support["codebrowser"] = out
    return support


def write_notes(
    report_name: str,
    author_name: str,
    project_name: str,
    program_name: str,
    support: dict[str, Path],
) -> Path:
    text = f"""# `{report_name}.pdf` Notes

## Report Metadata
- Report name: `{report_name}`
- Author: `{author_name}`

## What Was Done
1. Opened the real Ghidra project `{project_name}` and verified `{program_name}` was present.
2. Created a new user tool definition `code_browser_mcp.tcd` so the original CodeBrowser config stayed untouched.
3. Opened the new `CodeBrowserMCP` tool and verified the real GhidraMCP HTTP server started on port `8080`.
4. Loaded `{program_name}` into the real MCP-enabled CodeBrowser.
5. Ran live GhidraMCP-backed tool calls from terminal windows by importing `bridge_mcp_ghidra.py` and pointing it at `http://127.0.0.1:8080/`.
6. Ran the binary with the recovered key in a real terminal window.

## Screenshot Explanations
- `01_task0_tool_call_live.png`
  This window shows a real live GhidraMCP tool call: `list_functions()`. It proves the MCP-backed tool path is working against the loaded program.
- `02_task1_functions_live.png`
  This window shows the first 30 functions returned by the live tool call. The important internal functions visible here are `verify_format`, `decode_expected_key`, `verify_key`, `check_konami`, `print_decoys`, and `main`.
- `03_task1_key_format_live.png`
  This window shows the real decompile output of `verify_format`. From this we conclude the key must be 15 characters, start with `mcp{{`, end with `}}`, and only use `[A-Za-z0-9_]` inside.
- `04_task2_strings_xrefs_live.png`
  This window shows real string results and real xrefs from GhidraMCP. The HINT strings point us toward XOR and `verify_key`, and the xrefs show where those strings are used in `main`.
- `05_task2_key_recovery_live.png`
  This window shows the live `verify_key` decompile plus real `decode_expected_key` disassembly. The crucial instruction is `XOR EAX,0x2a` applied to bytes from `0x001021d0`, which leads to the decoded key `mcp{{MCP_GHIDRA}}`.
- `06_task3_flag_live.png`
  This window shows the real execution of `./sample/crackme_mcp 'mcp{{MCP_GHIDRA}}'` and the resulting flag `FLAG{{MCP_GHIDRA_NS_2026}}`.

## Supporting Windows
These are extra real windows from the same live session:
{f"- `00_frontend_server_started.png`: real Ghidra front-end showing the selected binary and the MCP-enabled tool running in the Running Tools area.\n" if 'frontend' in support else ""}
{f"- `00_codebrowser_mcp_loaded.png`: real MCP-enabled CodeBrowser with `{program_name}` loaded.\n" if 'codebrowser' in support else ""}

## Key
`mcp{{MCP_GHIDRA}}`

## Flag
`FLAG{{MCP_GHIDRA_NS_2026}}`
"""
    NOTES_MD.write_text(text)
    return NOTES_MD


def load_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def create_cover(report_name: str, author_name: str) -> Image.Image:
    img = Image.new("RGB", (1700, 2200), "#f4f2ec")
    draw = ImageDraw.Draw(img)
    title_font = load_font(70, True)
    heading_font = load_font(40, True)
    body_font = load_font(30, False)

    draw.rectangle((80, 80, 1620, 2120), outline="#bca26e", width=4)
    draw.text((130, 160), "GhidraMCP Reverse Engineering Demo", font=title_font, fill="#2f2418")
    draw.text((130, 320), f"Report: {report_name}", font=heading_font, fill="#1d1b18")
    draw.text((130, 390), f"Author: {author_name}", font=heading_font, fill="#1d1b18")
    draw.text((130, 520), "Live Window Capture Pack", font=heading_font, fill="#7a4c12")

    paragraphs = [
        "This PDF uses live window-only screenshots captured from the real Ghidra + GhidraMCP session.",
        "The MCP-enabled CodeBrowser was opened from a separate new tool definition so the original CodeBrowser tool file was not overwritten.",
        "The live tool-call screenshots were generated from real calls through bridge_mcp_ghidra.py against the running GhidraMCP HTTP server on 127.0.0.1:8080.",
        "Recovered key: mcp{MCP_GHIDRA}",
        "Recovered flag: FLAG{MCP_GHIDRA_NS_2026}",
    ]
    y = 640
    for paragraph in paragraphs:
        for line in textwrap.wrap(paragraph, width=74):
            draw.text((130, y), line, font=body_font, fill="#2c281f")
            y += 44
        y += 26
    return img


def build_pdf(report_name: str, author_name: str, pages: list[Path]) -> Path:
    pdf_path = SUBMISSION_DIR / f"{report_name}.pdf"
    images = [create_cover(report_name, author_name)]
    for page in pages:
        images.append(Image.open(page).convert("RGB"))
    first, rest = images[0], images[1:]
    first.save(pdf_path, save_all=True, append_images=rest, resolution=150)
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a live GhidraMCP evidence pack")
    parser.add_argument("--report-name", default=DEFAULT_REPORT_NAME)
    parser.add_argument("--author", default=DEFAULT_AUTHOR_NAME)
    parser.add_argument("--project-name", default=DEFAULT_PROJECT_NAME)
    parser.add_argument("--program-name", default=DEFAULT_PROGRAM_NAME)
    args = parser.parse_args()

    ensure_dirs()
    verify_live_server()
    scripts = create_scripts()
    support = capture_supporting_ghidra_windows(args.project_name, args.program_name)

    mapping = [
        ("01_task0_tool_call_live.png", "Task 0 - Live Tool Call", scripts["task0"]),
        ("02_task1_functions_live.png", "Task 1 - Live Functions", scripts["task1_functions"]),
        ("03_task1_key_format_live.png", "Task 1 - Live verify_format", scripts["task1_verify_format"]),
        ("04_task2_strings_xrefs_live.png", "Task 2 - Live Strings Xrefs", scripts["task2_strings_xrefs"]),
        ("05_task2_key_recovery_live.png", "Task 2 - Live Key Recovery", scripts["task2_key_recovery"]),
        ("06_task3_flag_live.png", "Task 3 - Live Flag Run", scripts["task3_flag"]),
    ]

    image_paths: list[Path] = []
    for filename, title, script_path in mapping:
        output_path = SCREENSHOT_DIR / filename
        launch_and_capture(title, script_path, output_path)
        image_paths.append(output_path)

    write_notes(args.report_name, args.author, args.project_name, args.program_name, support)
    pdf_path = build_pdf(args.report_name, args.author, image_paths)
    print(pdf_path)


if __name__ == "__main__":
    main()
