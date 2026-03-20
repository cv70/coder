import json
import subprocess
from pathlib import Path
from typing import Optional

from langchain.tools import tool

from agent_manager import AGENT
from background_manager import BG
from constants import WORKSPACE
from message_bus import BUS, handle_plan_review, handle_shutdown_request
from skill import SKILLS
from task_manager import TASK_MGR
from teammate_manager import TEAM
from todo_manager import TODO


def safe_path(p: str) -> Path:
    path = (WORKSPACE / p).resolve()
    if not path.is_relative_to(WORKSPACE):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


@tool
def bash(command: str) -> str:
    """Run a shell command."""
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=120,
        )
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"


@tool
def read_file(path: str, limit: Optional[int] = None) -> str:
    """Read a file."""
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit is not None and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Write to a file."""
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error: {e}"


@tool
def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace exact text in file."""
    try:
        fp = safe_path(path)
        c = fp.read_text()
        if old_text not in c:
            return f"Error: Text not found in {path}"
        fp.write_text(c.replace(old_text, new_text, 1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"


@tool
def todo_write(items: list) -> str:
    """Update task tracking list."""
    return TODO.update(items)


@tool
def task(prompt: str, agent_type: str = "Explore") -> str:
    """Spawn a subagent for isolated exploration or work."""
    return AGENT.run_subagent(prompt, agent_type)


@tool
def load_skill(name: str) -> str:
    """Load specialized knowledge by name."""
    return SKILLS.load(name)


@tool
def compress() -> str:
    """Manually compress conversation context."""
    return "Compressing..."


@tool
def background_run(command: str, timeout: int = 120) -> str:
    """Run command in background thread."""
    return BG.run(command, timeout)


@tool
def check_background(task_id: str) -> str:
    """Check background task status."""
    return BG.check(task_id)


@tool
def task_create(subject: str, description: str = "") -> str:
    """Create a persistent file task."""
    return TASK_MGR.create(subject, description)


@tool
def task_get(task_id: int) -> str:
    """Get task details by ID."""
    return TASK_MGR.get(task_id)


@tool
def task_update(
    task_id: int,
    status: str = None,
    add_blocked_by: list = None,
    add_blocks: list = None,
) -> str:
    """Update task status or dependencies."""
    return TASK_MGR.update(task_id, status, add_blocked_by, add_blocks)


@tool
def task_list() -> str:
    """List all tasks."""
    return TASK_MGR.list_all()


@tool
def spawn_teammate(name: str, role: str, prompt: str) -> str:
    """Spawn a persistent autonomous teammate."""
    return TEAM.spawn(name, role, prompt)


@tool
def list_teammates() -> str:
    """List all teammates."""
    return TEAM.list_all()


@tool
def send_message(to: str, content: str, msg_type: str = "message") -> str:
    """Send a message to a teammate."""
    return BUS.send("lead", to, content, msg_type)


@tool
def read_inbox() -> str:
    """Read and drain the lead's inbox."""
    return json.dumps(BUS.read_inbox("lead"), indent=2)


@tool
def broadcast(content: str) -> str:
    """Send message to all teammates."""
    return BUS.broadcast("lead", content, TEAM.member_names())


@tool
def shutdown_request(teammate: str) -> str:
    """Request a teammate to shut down."""
    return handle_shutdown_request(teammate)


@tool
def plan_approval(request_id: str, approve: bool, feedback: str = "") -> str:
    """Approve or reject a teammate's plan."""
    return handle_plan_review(request_id, approve, feedback)


@tool
def idle() -> str:
    """Enter idle state."""
    return "Lead does not idle."


@tool
def claim_task(task_id: int) -> str:
    """Claim a task from the board."""
    return TASK_MGR.claim(task_id, "lead")
