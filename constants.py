from pathlib import Path

WORKSPACE = Path.cwd()
CODER_HOME = Path.home() / ".coder"
TASK_DIR = CODER_HOME / ".task"
TEAM_DIR = CODER_HOME / ".team"
SKILL_DIR = CODER_HOME / ".skill"
TRANSCRIPT_DIR = CODER_HOME / ".transcript"

TOKEN_THRESHOLD = 100000
POLL_INTERVAL = 5
IDLE_TIMEOUT = 60
