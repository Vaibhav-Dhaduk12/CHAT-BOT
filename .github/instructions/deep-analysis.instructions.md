---
name: deep-analysis-prompter
description: "FORCE deep analysis and prompt refinement before ANY coding. Apply when: building chat-bot, writing python, using fastapi."
applyTo: "**/*.py"
---

# Deep Analysis & Prompt Refinement Protocol

Before generating or editing any code, you MUST follow this three-step process:

## Phase 1: Deep Analysis
Analyze the user's request against the existing codebase. Identify:
- **Core Intent**: What is the primary problem being solved?
- **Impact Surface**: Which modules, files, or functions will be affected?
- **Constraints**: Identify any technical debt, performance limits, or framework constraints (specifically for Python FastAPI).

## Phase 2: Prompt Refinement & Plan
Draft a "Refined Internal Prompt" for yourself. This prompt should:
1. Define the specific sub-tasks needed.
2. Outline the logic flow and architecture (e.g., Pydantic models for request/response validation).
3. Specify the exact tools or libraries to be used (LangChain, Pinecone, FastAPI).
4. Identify potential edge cases.

## Phase 3: Execution (Coding)
Only after completing Phase 1 and 2, proceed to implementation.
- **Python/FastAPI Standards**: 
    - Use type hints for all parameters and return types.
    - Leverage FastAPI dependency injection where appropriate.
    - Use Pydantic `BaseModel` for data validation.
    - Ensure asynchronous execution (`async def`) for I/O operations.
- **Error Handling**: Use structured error responses and FastAPI `HTTPException`.

## Feedback Loop
If the execution encounters an unforeseen complexity, RETURN to Phase 1 and re-evaluate.
