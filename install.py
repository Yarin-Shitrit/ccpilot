"""Cross-platform installer for ccpilot.

Usage:
    python install.py [--dry-run] [--claude-dir DIR] [--no-skills]

Idempotent. Never overwrites existing keys in settings.json — deep-merges
the UserPromptSubmit hook entry and leaves everything else untouched.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
HOOK_ENTRY_MATCH = "ccpilot"  # identifier in hook command path

# ANSI palette — disabled automatically on dumb terminals / non-tty / NO_COLOR.
_NO_COLOR = bool(os.environ.get("NO_COLOR")) or not sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    if _NO_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def dim(s: str) -> str: return _c("2", s)
def bold(s: str) -> str: return _c("1", s)
def cyan(s: str) -> str: return _c("36", s)
def green(s: str) -> str: return _c("32", s)
def yellow(s: str) -> str: return _c("33", s)
def red(s: str) -> str: return _c("31", s)


BANNER = r"""
   ___            _  _       _
  / __|__ _ _ __ (_)| | ___ | |_
 | (__/ _` | '_ \| || |/ _ \|  _|
  \___\__,_| .__/|_||_|\___/ \__|
           |_|   routing autopilot for Claude Code
"""


def banner() -> None:
    print(cyan(BANNER))


def section(title: str) -> None:
    print()
    print(bold(cyan(f"── {title} ")) + cyan("─" * max(1, 60 - len(title) - 4)))


def ok(msg: str) -> None:
    print(f"  {green('✓')} {msg}")


def info(msg: str) -> None:
    print(f"  {cyan('·')} {msg}")


def warn(msg: str) -> None:
    print(f"  {yellow('!')} {msg}")


def fail(msg: str) -> None:
    print(f"  {red('✗')} {msg}")


def is_windows() -> bool:
    return os.name == "nt"


def hook_source() -> Path:
    return REPO / "hooks" / ("ccpilot.cmd" if is_windows() else "ccpilot.sh")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


POST_HOOK_MATCH = "ccpilot-post"


def post_hook_source() -> Path:
    return REPO / "hooks" / ("ccpilot-post.cmd" if is_windows() else "ccpilot-post.sh")


def install_post_hook(claude_dir: Path, dry_run: bool) -> Path:
    target_dir = claude_dir / "hooks"
    ensure_dir(target_dir)
    src = post_hook_source()
    target = target_dir / src.name
    if dry_run:
        print(f"[dry] copy {src} -> {target}")
    else:
        shutil.copy2(src, target)
        if not is_windows():
            target.chmod(0o755)
    return target


def merge_post_settings(after: dict, post_target: Path) -> dict:
    hooks = after.setdefault("hooks", {})
    ptu = hooks.setdefault("PostToolUse", [])
    ptu = [e for e in ptu if POST_HOOK_MATCH not in json.dumps(e)]
    ptu.append({"hooks": [{"type": "command", "command": str(post_target)}]})
    hooks["PostToolUse"] = ptu
    return after


def merge_settings(settings_path: Path, hook_target: Path) -> tuple[dict, dict]:
    """Return (before, after) settings dicts. Does not write."""
    before: dict = {}
    if settings_path.exists():
        try:
            before = json.loads(settings_path.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            before = {}

    after = json.loads(json.dumps(before))  # deep copy via json
    hooks = after.setdefault("hooks", {})
    ups = hooks.setdefault("UserPromptSubmit", [])

    # Remove any existing ccpilot entry to keep idempotent
    ups = [e for e in ups if HOOK_ENTRY_MATCH not in json.dumps(e)]
    ups.append({
        "hooks": [{"type": "command", "command": str(hook_target)}],
    })
    hooks["UserPromptSubmit"] = ups
    return before, after


def install_hook(claude_dir: Path, dry_run: bool) -> Path:
    target_dir = claude_dir / "hooks"
    ensure_dir(target_dir)
    src = hook_source()
    target = target_dir / src.name
    if dry_run:
        print(f"[dry] copy {src} -> {target}")
    else:
        shutil.copy2(src, target)
        if not is_windows():
            target.chmod(0o755)
    return target


def _replace_path(target: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"[dry] remove {target}")
        return
    if target.is_dir() and not target.is_symlink():
        shutil.rmtree(target)
    else:
        target.unlink()


def install_skills(claude_dir: Path, dry_run: bool, update: bool = False) -> list[str]:
    src_dir = REPO / "ccpilot-skills"
    dst_dir = claude_dir / "skills"
    ensure_dir(dst_dir)
    installed: list[str] = []
    if not src_dir.is_dir():
        return installed
    for skill_dir in sorted(src_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        name = skill_dir.name
        target = dst_dir / name
        if target.exists():
            if update:
                _replace_path(target, dry_run)
            else:
                target = dst_dir / (name + ".ccpilot")
                if target.exists():
                    continue  # already installed variant — skip
        if dry_run:
            print(f"[dry] copy {skill_dir} -> {target}")
        else:
            shutil.copytree(skill_dir, target)
        installed.append(target.name)
    return installed


def _install_tree(src_dir: Path, dst_dir: Path, dry_run: bool, suffix: str = ".ccpilot", update: bool = False) -> list[str]:
    ensure_dir(dst_dir)
    installed: list[str] = []
    if not src_dir.is_dir():
        return installed
    for entry in sorted(src_dir.iterdir()):
        if entry.name.startswith("."):
            continue
        target = dst_dir / entry.name
        if target.exists():
            if update:
                _replace_path(target, dry_run)
            else:
                target = dst_dir / (entry.name + suffix)
                if target.exists():
                    continue
        if dry_run:
            print(f"[dry] copy {entry} -> {target}")
        else:
            if entry.is_dir():
                shutil.copytree(entry, target)
            else:
                shutil.copy2(entry, target)
        installed.append(target.name)
    return installed


def install_agents(claude_dir: Path, dry_run: bool, update: bool = False) -> list[str]:
    return _install_tree(REPO / "ccpilot-agents", claude_dir / "agents", dry_run, update=update)


def install_commands(claude_dir: Path, dry_run: bool, update: bool = False) -> list[str]:
    return _install_tree(REPO / "ccpilot-commands", claude_dir / "commands", dry_run, update=update)


def install_config(claude_dir: Path, dry_run: bool) -> Path:
    target = claude_dir / "ccpilot" / "config.toml"
    ensure_dir(target.parent)
    if target.exists():
        return target  # never overwrite user-edited config
    sample = REPO / "ccpilot" / "config.sample.toml"
    content = sample.read_text() if sample.exists() else "# ccpilot config — see defaults in ccpilot/config.py\n"
    if dry_run:
        print(f"[dry] write {target}")
    else:
        target.write_text(content)
    return target


SMART_PKGS = ["anthropic>=0.40", "model2vec>=0.5", "numpy>=1.24"]
OPENAI_PKGS = ["openai>=1.40"]


def _pip_install(pkgs: list[str], dry_run: bool) -> bool:
    if dry_run:
        info(f"[dry] pip install {' '.join(pkgs)}")
        return True
    cmd = [sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", *pkgs]
    try:
        subprocess.run(cmd, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        fail(f"pip install failed: {e}")
        return False


def _probe(mod: str) -> bool:
    try:
        __import__(mod)
        return True
    except ImportError:
        return False


def install_python_deps(args: argparse.Namespace) -> None:
    want_smart = args.with_smart or (not args.no_smart and args.auto_deps)
    want_openai = args.with_openai

    if want_smart:
        missing = [p for p, m in zip(SMART_PKGS, ["anthropic", "model2vec", "numpy"]) if not _probe(m)]
        if not missing:
            ok("smart extras already installed (anthropic, model2vec, numpy)")
        else:
            info(f"installing smart extras: {', '.join(missing)}")
            if _pip_install(missing, args.dry_run):
                ok("smart extras ready")
        bundled = REPO / "ccpilot" / "models" / "potion-base-8M"
        if (bundled / "model.safetensors").exists():
            ok(f"bundled dense model present ({bundled.name}) — air-gapped ready")
        else:
            warn("bundled model2vec model missing — runtime will try HF Hub (fails in air-gapped envs)")
    elif args.no_smart:
        warn("skipping smart extras (--no-smart)")
    else:
        info("smart extras not requested — ccpilot will use stdlib fallbacks")
        info(f"  enable later with: {bold('pip install ccpilot[smart]')}")

    if want_openai:
        if _probe("openai"):
            ok("openai SDK already installed")
        else:
            info("installing openai SDK")
            if _pip_install(OPENAI_PKGS, args.dry_run):
                ok("openai SDK ready")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Install ccpilot hooks, skills, agents, and optional smart-routing deps.",
    )
    ap.add_argument("--dry-run", action="store_true", help="Print actions without touching disk.")
    ap.add_argument("--claude-dir", default=str(Path.home() / ".claude"))
    ap.add_argument("--no-skills", action="store_true")
    ap.add_argument("--no-agents", action="store_true",
                    help="Skip installing the curated ruflo agent pack.")
    ap.add_argument("--no-commands", action="store_true",
                    help="Skip installing the curated ruflo commands pack.")
    ap.add_argument("--with-learning", action="store_true",
                    help="Also register PostToolUse hook for verdict learning.")
    ap.add_argument("--with-smart", action="store_true",
                    help="Pip-install Haiku classifier + model2vec dense embeddings.")
    ap.add_argument("--no-smart", action="store_true",
                    help="Skip smart deps even when --auto-deps is on.")
    ap.add_argument("--with-openai", action="store_true",
                    help="Also install the openai SDK for OpenAI-compatible gateways.")
    ap.add_argument("--auto-deps", action="store_true",
                    help="Default-on smart deps unless --no-smart is passed.")
    ap.add_argument("--update", action="store_true",
                    help="Refresh existing installation: overwrite hooks, skills, agents, "
                         "and commands in place (config.toml is preserved).")
    args = ap.parse_args(argv)

    banner()
    claude_dir = Path(args.claude_dir).expanduser()
    ensure_dir(claude_dir)
    info(f"target: {bold(str(claude_dir))}")
    if args.update:
        info("update mode — existing skills/agents/commands will be refreshed in place")
    if args.dry_run:
        warn("dry-run mode — no files will change")

    section("Hooks")
    hook_target = install_hook(claude_dir, args.dry_run)
    ok(f"UserPromptSubmit → {dim(str(hook_target))}")
    settings_path = claude_dir / "settings.json"
    before, after = merge_settings(settings_path, hook_target)
    if args.with_learning:
        post_target = install_post_hook(claude_dir, args.dry_run)
        after = merge_post_settings(after, post_target)
        ok(f"PostToolUse    → {dim(str(post_target))}")

    if args.dry_run:
        info("settings.json diff (dry-run):")
        print(dim(json.dumps({"before": before, "after": after}, indent=2)))
    else:
        backup = settings_path.with_suffix(".json.ccpilot.bak")
        if settings_path.exists() and not backup.exists():
            shutil.copy2(settings_path, backup)
            info(f"backed up settings.json → {dim(backup.name)}")
        settings_path.write_text(json.dumps(after, indent=2))
        ok(f"merged settings: {dim(str(settings_path))}")

    section("Config & skills")
    cfg_target = install_config(claude_dir, args.dry_run)
    ok(f"config:   {dim(str(cfg_target))}")
    installed = [] if args.no_skills else install_skills(claude_dir, args.dry_run, args.update)
    agents = [] if args.no_agents else install_agents(claude_dir, args.dry_run, args.update)
    commands = [] if args.no_commands else install_commands(claude_dir, args.dry_run, args.update)
    verb = "refreshed" if args.update else "added"
    if installed: ok(f"skills:   {len(installed)} {verb}")
    if agents:    ok(f"agents:   {len(agents)} {verb}")
    if commands:  ok(f"commands: {len(commands)} {verb}")

    section("Python dependencies")
    install_python_deps(args)

    section("Done")
    ok("ccpilot installed")
    info(f"logs:     {dim('~/.claude/ccpilot/log.jsonl')}")
    info(f"disable:  {dim('export CCPILOT_DISABLED=1')}")
    info(f"next:     open Claude Code and type a prompt — the routing block should appear")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
