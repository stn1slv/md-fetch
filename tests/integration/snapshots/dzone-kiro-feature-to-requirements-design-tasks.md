# AWS Kiro: The Agentic IDE That Makes Specs the Unit of Work

The agentic IDE space has gotten crowded fast. Cursor, Claude Code, Copilot, Windsurf — they all share the same core model: you type a prompt, the AI writes some code, you iterate. It works well for prototyping. It breaks down when you're building production systems on a large codebase with a team of more than one.

AWS Kiro takes a different bet. Instead of chat-first, it's **spec-first**. The unit of work isn't a prompt — it's a structured specification that the agent uses to plan, implement, verify, and document your feature end to end. That's a meaningful philosophical difference, and in practice it changes what the tool is useful for.

Here's what Kiro actually is, how its core concepts fit together, and an honest take on when it makes sense over the alternatives.

## What Kiro Is

Kiro launched from AWS in mid-2025 and is built on top of Amazon Bedrock, routing between Claude Sonnet for reasoning-heavy work and Amazon Nova for high-throughput code generation. It ships in three forms:

* **Kiro IDE** – a VS Code-compatible editor (built on Code OSS, so you can import your existing themes, keybindings, and Open VSX plugins)
* **Kiro CLI** – the same agent in your terminal, useful for SSH sessions or scripted workflows
* **Kiro Autonomous Agent** – a background agent that picks up tasks, implements them, and opens PRs without you sitting in the loop

You don't need an AWS account to get started — you can sign in with GitHub or Google. The IDE feels immediately familiar if you've used VS Code, which removes one of the usual adoption barriers for new tooling.

In January 2026, AWS also announced the end of Amazon Q Developer for new signups (effective May 15, 2026), explicitly directing users to Kiro as its successor for IDE-based AI assistance. That's a significant signal about where AWS is placing its bets.

## The Three Concepts That Make Kiro Different

### 1. Specs

When you start a new feature in Kiro, you don't jump straight to code. You describe what you want to build, and Kiro generates three structured files:

* `requirements.md` — user stories and acceptance criteria
* `design.md` — system design, component breakdown, data flow
* `tasks.md` — a numbered implementation checklist the agent works through