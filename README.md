# Sisyphus - AI Coding Assistant

A Claude Code-like programmable AI agent that helps with coding tasks using various tools, multi-agent collaboration, and an extensible skill system.

## Overview

Sisyphus is an AI coding assistant inspired by Claude Code that enables developers to accomplish programming tasks through natural language interaction. It combines a powerful language model with tool usage capabilities, multi-agent coordination, and a skill-based extensibility system to provide a flexible and powerful development assistant.

The system is designed to help developers with:
- Writing and modifying code
- Debugging and troubleshooting
- Exploring codebases
- Managing development workflows
- Learning new technologies and patterns

## Key Features

### 🤖 Multi-Agent System
- Spawn and manage multiple AI agents for parallel task execution
- Agents can collaborate and share information through a message bus
- Specialized agents for different types of work (exploration, research, implementation)

### 🔧 Comprehensive Tool Usage
- File system operations (read, write, edit, search)
- Command execution (bash)
- Background task management for asynchronous operations

### 🧠 Extensible Skill System
- Load specialized skills for domain-specific knowledge
- Skills include: test-driven development, systematic debugging, writing plans, using git worktrees, and more
- User-installable skills override built-in defaults for customization

### 📋 Workflow Management
- Built-in todo list management for tracking progress
- Automatic reminder system for stalled tasks
- Plan approval workflows for complex implementations
- Session persistence and continuation

### 💬 Team Communication
- Message passing between agents and human users
- Inbox system for agent-to-agent communication
- Broadcast capabilities for system-wide notifications

### ⚡ Background Processing
- Run long-running tasks asynchronously
- Progress notifications and result collection
- Parallel execution of independent tasks
- Automatic cancellation and cleanup

## Usage

### Basic Interaction
Start the assistant and interact through the command line:
```
$ python main.py

coder >> Hello, can you help me create a Python function to calculate fibonacci numbers?
```

### Available Commands
In the main prompt, you can use these special commands:
- `/task` - List all active tasks
- `/team` - List all spawned agents/teammates
- `/inbox` - View messages in your agent's inbox
- `/compact` - Manually trigger conversation history compaction
- `q` or `exit` - Quit the assistant

### Working with Agents
The assistant can spawn specialized agents to help with different types of work:
- **Explore agents**: Search and analyze codebases
- **Librarian agents**: Find external documentation and examples
- **Task agents**: Execute specific implementation plans

## Architecture

### Core Components
- **AgentManager**: Main agent loop handling tool usage and reasoning
- **TaskManager**: Manages long-running tasks and subtasks
- **TodoManager**: Tracks progress through todo lists
- **MessageBus**: Enables communication between agents
- **BackgroundManager**: Handles asynchronous task execution
- **SkillLoader**: Manages the skill system and extensions
- **TeammateManager**: Handles spawning and managing AI agents

### Data Flow
1. User input is processed through the main agent loop
2. The LLM decides which tools to use based on the context
3. Tools are executed and results are fed back to the LLM
4. The process repeats until the task is complete
5. Background tasks run independently and notify when finished
6. Agents can communicate via the message bus system

## Extending the System

### Adding New Skills
Skills are markdown files stored in the `skill/` directory with YAML frontmatter:
```markdown
---
name: my-custom-skill
description: A brief description of what this skill does
---

# Skill Content
Detailed instructions for the skill...
```

Place skill files in:
- `~/.coder/skill/` for project-specific skills

### Custom Tools
New tools can be added by:
1. Implementing the tool function in `tools.py`
2. Adding it to the tool binding in `agent_manager.py`
3. Documenting its usage in the skill system

## Contributing

We welcome contributions to improve Sisyphus! Please feel free to submit pull requests or open issues.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure all tests pass
5. Submit a pull request

### Coding Standards
- Follow PEP 8 for Python code
- Write clear, descriptive commit messages
- Update documentation when adding features
- Add type hints where appropriate

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

Inspired by Claude Code and other AI coding assistants. Built with the goal of creating an extensible, programmable AI developer assistant.
