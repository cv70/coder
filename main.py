#!/usr/bin/env python3
import json

from agent_manager import AGENT
from constants import WORKSPACE, CODER_HOME, TASK_DIR, TEAM_DIR, SKILL_DIR, TRANSCRIPT_DIR
from task_manager import TASK_MGR
from utils import auto_compact
from message_bus import BUS
from skill import SKILLS
from teammate_manager import TEAM


# === System Prompt ===
SYSTEM = f"""You are a coding agent at {WORKSPACE}. Use tools to solve tasks.
Prefer task_create/task_update/task_list for multi-step work. Use TodoWrite for short checklists.
Use task for subagent delegation. Use load_skill for specialized knowledge.
Skills: {SKILLS.descriptions()}"""


def ensure_workspace():
    CODER_HOME.mkdir(exist_ok=True)
    TASK_DIR.mkdir(exist_ok=True)
    TEAM_DIR.mkdir(exist_ok=True)
    SKILL_DIR.mkdir(exist_ok=True)
    TRANSCRIPT_DIR.mkdir(exist_ok=True)


if __name__ == "__main__":
    ensure_workspace()
    history = []
    while True:
        try:
            query = input("\033[36mcoder >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        if query.strip() == "/compact":
            if history:
                print("[manual compact via /compact]")
                history[:] = auto_compact(history)
            continue
        if query.strip() == "/task":
            print(TASK_MGR.list_all())
            continue
        if query.strip() == "/team":
            print(TEAM.list_all())
            continue
        if query.strip() == "/inbox":
            print(json.dumps(BUS.read_inbox("lead"), indent=2))
            continue
        history.append({"role": "user", "content": query})
        AGENT.agent_loop(history)
        print()
