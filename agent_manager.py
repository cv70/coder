import json

from langchain.messages import AIMessage

from background_manager import BackgroundManager
from constants import TOKEN_THRESHOLD
from message_bus import MessageBus
from todo_manager import TodoManager
from langchain_openai import ChatOpenAI

from constants import WORKSPACE
from utils import auto_compact, estimate_tokens, microcompact
from tools import bash, read_file, write_file, edit_file, todo_write, task, load_skill, compress, background_run, check_background, task_create, task_get, task_update, task_list, spawn_teammate, list_teammates, send_message, read_inbox, broadcast, shutdown_request, plan_approval, idle, claim_task


class AgentManager:
    def __init__(self, model: ChatOpenAI, bg: BackgroundManager, bus: MessageBus, todo: TodoManager):
        self.model = model
        self.bg = bg
        self.bus = bus
        self.todo = todo

    def agent_loop(self, messages: list):
        rounds_without_todo = 0
        while True:
            # compression pipeline
            microcompact(messages)
            if estimate_tokens(messages) > TOKEN_THRESHOLD:
                print("[auto-compact triggered]")
                messages[:] = auto_compact(WORKSPACE, messages)
            # drain background notifications
            notifs = self.bg.drain()
            if notifs:
                txt = "\n".join(
                    f"[bg:{n['task_id']}] {n['status']}: {n['result']}" for n in notifs
                )
                messages.append(
                    {
                        "role": "user",
                        "content": f"<background-results>\n{txt}\n</background-results>",
                    }
                )
                messages.append(
                    {"role": "assistant", "content": "Noted background results."}
                )
            # check lead inbox
            inbox = self.bus.read_inbox("lead")
            if inbox:
                messages.append(
                    {
                        "role": "user",
                        "content": f"<inbox>{json.dumps(inbox, indent=2)}</inbox>",
                    }
                )
                messages.append({"role": "assistant", "content": "Noted inbox messages."})

            # LLM call
            response: AIMessage = self.model.bind_tools(
                bash, read_file, write_file, edit_file, todo_write, task, load_skill, compress, background_run,
                check_background, task_create, task_get, task_update, task_list, spawn_teammate, list_teammates,
                send_message, read_inbox, broadcast, shutdown_request, plan_approval, idle, claim_task
            ).invoke(messages)
            messages.append(response)
            print(response)

            if len(response.tool_calls) == 0:
                break

            # Tool execution
            results = []
            used_todo = False
            manual_compress = False
            for tool_call in response.tool_calls:
                try:
                    tool_result = tool_call.invoke()
                except Exception as e:
                    tool_result = f"Error: {e}"
                results.append(tool_result)
                print(f"> {tool_call.name}: {str(tool_result)[:200]}")
                if tool_call.name == "todo_write":
                    used_todo = True

  
            # nag reminder (only when todo workflow is active)
            rounds_without_todo = 0 if used_todo else rounds_without_todo + 1
            if self.todo.has_open_items() and rounds_without_todo >= 3:
                results.insert(
                    0, {"type": "text", "text": "<reminder>Update your todos.</reminder>"}
                )
            messages.append({"role": "user", "content": results})
            # manual compress
            if manual_compress:
                print("[manual compact]")
                messages[:] = auto_compact(WORKSPACE, messages)


    def run_subagent(self, prompt: str, agent_type: str = "Explore") -> str:
        sub_tools = [bash, read_file]
        if agent_type != "Explore":
            sub_tools += [write_file, edit_file]
        sub_msgs = [{"role": "user", "content": prompt}]
        resp = None
        for _ in range(30):
            resp: AIMessage = self.model.bind_tools(sub_tools).invoke(
                model=MODEL, messages=sub_msgs, max_tokens=8000
            )
            sub_msgs.append({"role": "assistant", "content": resp.content})
            if not resp.tool_calls:
                break
            results = []
            for tool_call in resp.tool_calls:
                tool_result = tool_call.invoke()
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": str(tool_result)[:50000],
                    }
                )
            sub_msgs.append({"role": "user", "content": results})
        if resp:
            return (
                "".join(b.text for b in resp.content if hasattr(b, "text"))
                or "(no summary)"
            )
        return "(subagent failed)"


from model import MODEL
from background_manager import BG
from message_bus import BUS
from todo_manager import TODO
AGENT = AgentManager(MODEL, BG, BUS, TODO)
