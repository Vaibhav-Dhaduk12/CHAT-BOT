# Workspace Instructions (CHAT-BOT)

This file contains primary project-wide instructions that GitHub Copilot will follow automatically for every request within this workspace.

## AI Agent Interaction & Problem Solving

- **Deep Analysis Protocol**: Before executing any tool that modifies the codebase, the agent MUST perform a deep analysis of the request.
- **Prompt Refinement**: The agent MUST summarize its understanding of the task and its plan in a "Refined Prompt" format before writing any code. This ensures alignment between the agent's internal logic and the user's intent.
- **Framework Focus**: The primary architecture is **Python (FastAPI)**. Always prioritize:
    - Asynchronous I/O (`async`/`await`).
    - Type hints for all function signatures.
    - Pydantic models for data validation and API documentation.
    - Modular code structure (separation of routes, logic, and data).

## Coding Standards

- **RESTful API**: Standardized HTTP status codes and response headers.
- **Error Handling**: Use structured `HTTPException` for all client-facing errors.
- **Documentation**: All public API endpoints must have clear Docstrings or Pydantic `Field` descriptions for automatic Swagger generation.
