import json
import threading
import time

from langchain_openai import ChatOpenAI

from constants import IDLE_TIMEOUT, POLL_INTERVAL, WORKSPACE, TASK_DIR, TEAM_DIR
from message_bus import MessageBus
from task_manager import TaskManager
from tools import bash, read_file, write_file, edit_file, send_message, idle, claim_task


class TeammateManager:
    def __init__(self, model: ChatOpenAI, bus: MessageBus, task_mgr: TaskManager):
        self.model = model
        self.bus = bus
        self.task_mgr = task_mgr
        self.config_path = TEAM_DIR / "config.json"
        self.config = self._load()
        self.threads = {}

    def _load(self) -> dict:
        if self.config_path.exists():
            return json.loads(self.config_path.read_text())
        return {"team_name": "default", "members": []}

    def _save(self):
        self.config_path.write_text(json.dumps(self.config, indent=2))

    def _find(self, name: str) -> dict:
        for m in self.config["members"]:
            if m["name"] == name:
                return m
        return None

    def spawn(self, name: str, role: str, prompt: str) -> str:
        member = self._find(name)
        if member:
            if member["status"] not in ("idle", "shutdown"):
                return f"Error: '{name}' is currently {member['status']}"
            member["status"] = "working"
            member["role"] = role
        else:
            member = {"name": name, "role": role, "status": "working"}
            self.config["members"].append(member)
        self._save()
        threading.Thread(
            target=self._loop, args=(name, role, prompt), daemon=True
        ).start()
        return f"Spawned '{name}' (role: {role})"

    def _set_status(self, name: str, status: str):
        member = self._find(name)
        if member:
            member["status"] = status
            self._save()

    def _loop(self, name: str, role: str, prompt: str):
        team_name = self.config["team_name"]
        system_prompt = (
            f"You are '{name}', role: {role}, team: {team_name}, at {WORKSPACE}. "
            f"Use idle when done with current work. You may auto-claim tasks."
        )
        system_message = {"role": "system", "content": system_prompt}
        messages = [{"role": "user", "content": prompt}]
        tools = [bash, read_file, write_file, edit_file, send_message, idle, claim_task]
        while True:
            # -- WORK PHASE --
            for _ in range(50):
                inbox = self.bus.read_inbox(name)
                for msg in inbox:
                    if msg.get("type") == "shutdown_request":
                        self._set_status(name, "shutdown")
                        return
                    messages.append({"role": "user", "content": json.dumps(msg)})
                try:
                    response = self.model.bind_tools(tools).invoke([system_message] + messages, max_tokens=8000)
                except Exception:
                    self._set_status(name, "shutdown")
                    return
                messages.append({"role": "assistant", "content": response.content})
                if not response.tool_calls:
                    break
                results = []
                idle_requested = False
                for tool_call in response.tool_calls:
                    if tool_call.name == "idle":
                        idle_requested = True
                        output = "Entering idle phase."
                    elif tool_call.name == "claim_task":
                        output = self.task_mgr.claim(tool_call.args["task_id"], name)
                    elif tool_call.name == "send_message":
                        output = self.bus.send(
                            name, tool_call.args["to"], tool_call.args["content"]
                        )
                    else:
                        output = tool_call.invoke()
                        print(f"  [{name}] {tool_call.name}: {str(output)[:120]}")
                    results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_call.id,
                            "content": str(output),
                        }
                    )
                messages.append({"role": "user", "content": results})
                if idle_requested:
                    break
            # -- IDLE PHASE: poll for messages and unclaimed tasks --
            self._set_status(name, "idle")
            resume = False
            for _ in range(IDLE_TIMEOUT // max(POLL_INTERVAL, 1)):
                time.sleep(POLL_INTERVAL)
                inbox = self.bus.read_inbox(name)
                if inbox:
                    for msg in inbox:
                        if msg.get("type") == "shutdown_request":
                            self._set_status(name, "shutdown")
                            return
                        messages.append({"role": "user", "content": json.dumps(msg)})
                    resume = True
                    break
                unclaimed = []
                for f in sorted(TASK_DIR.glob("task_*.json")):
                    t = json.loads(f.read_text())
                    if (
                        t.get("status") == "pending"
                        and not t.get("owner")
                        and not t.get("blockedBy")
                    ):
                        unclaimed.append(t)
                if unclaimed:
                    task = unclaimed[0]
                    self.task_mgr.claim(task["id"], name)
                    # Identity re-injection for compressed contexts
                    if len(messages) <= 3:
                        messages.insert(
                            0,
                            {
                                "role": "user",
                                "content": f"<identity>You are '{name}', role: {role}, team: {team_name}.</identity>",
                            },
                        )
                        messages.insert(
                            1,
                            {
                                "role": "assistant",
                                "content": f"I am {name}. Continuing.",
                            },
                        )
                    messages.append(
                        {
                            "role": "user",
                            "content": f"<auto-claimed>Task #{task['id']}: {task['subject']}\n{task.get('description', '')}</auto-claimed>",
                        }
                    )
                    messages.append(
                        {
                            "role": "assistant",
                            "content": f"Claimed task #{task['id']}. Working on it.",
                        }
                    )
                    resume = True
                    break
            if not resume:
                self._set_status(name, "shutdown")
                return
            self._set_status(name, "working")

    def list_all(self) -> str:
        if not self.config["members"]:
            return "No teammates."
        lines = [f"Team: {self.config['team_name']}"]
        for m in self.config["members"]:
            lines.append(f"  {m['name']} ({m['role']}): {m['status']}")
        return "\n".join(lines)

    def member_names(self) -> list:
        return [m["name"] for m in self.config["members"]]


from model import MODEL
from message_bus import BUS
from task_manager import TASK_MGR
TEAM = TeammateManager(MODEL, BUS, TASK_MGR)
