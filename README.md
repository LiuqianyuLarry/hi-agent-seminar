# hi-agent-seminar (v2.10.0)

An English **EEEE4149 Advanced Computational Engineering** teaching plugin for Claude Code, covering Weeks 1–6. Mentor Liu guides you through each 2 × 50-minute seminar with real local code, predictions, experiments, and result checks while keeping all learning records and code in your own workspace.

## Install from GitHub

**Prerequisites:** Git, Python 3.11+, and Claude Code.

Run these commands in your terminal (PowerShell on Windows), not inside Claude chat:

```text
claude plugin marketplace add LiuqianyuLarry/hi-agent-seminar
claude plugin install hi-agent-seminar@hi-agent-seminar-marketplace
claude plugin list
```

Create or open your own student work folder **outside** the plugin repository, launch `claude` there, and run:

```text
/hi-agent-seminar:menu
```

## Update from GitHub

```text
claude plugin marketplace update hi-agent-seminar-marketplace
claude plugin update hi-agent-seminar@hi-agent-seminar-marketplace
```

Restart Claude Code and reopen the same student workspace. Updating the plugin never resets or overwrites saved progress or student code. To experience a newly revised lesson script while keeping older work intact, choose **Start again from the beginning** when entering a week.

## Seminars (Weeks 1–6)

| Week | Topic | Core Requirements | Start Command |
| --- | --- | --- | --- |
| Week 1 | Model APIs, prompts, context & verification | Python 3.11+ & DeepSeek API key | `/hi-agent-seminar:start week01` |
| Week 2 | Inside the Transformer & MiniGPT | Local PyTorch (CPU or CUDA; see `week02/resources/SETUP.md`) | `/hi-agent-seminar:start week02` |
| Week 3 | Tools, function calling & MCP | Python 3.11+ & DeepSeek API key (for live calls) | `/hi-agent-seminar:start week03` |
| Week 4 | Agent loops, verification & failure analysis | Python 3.11+, Pydantic, pytest (no API key or GPU required) | `/hi-agent-seminar:start week04` |
| Week 5 | State machines, checkpoints, approval & recovery | Python 3.11+ & `week05/resources/workflow/requirements.txt` (no API key or GPU) | `/hi-agent-seminar:start week05` |
| Week 6 | Context engineering, SQL, CAG/RAG & citation audit | Python 3.11+ & SQLite (fully offline; optional labs in menu) | `/hi-agent-seminar:start week06` |

## Commands

All commands use the `/hi-agent-seminar:` prefix:

| Command | Purpose |
| --- | --- |
| `menu` | Browse Weeks 1–6, saved progress, sessions, and optional topics |
| `start [week01–week06]` | Start a week or resume an existing session |
| `status [week01–week06]` | Check saved core percentage and next step without advancing |
| `review [week01–week06]` | Complete three reflection questions and save a local code snapshot |
| `help` | Show available commands and usage notes |

## Good to Know

- **Two learning modes:** Choose **Review lecture + code** to revisit lecture diagrams alongside Python, or **Start seminar practice** to jump straight into the exercises with explanations on demand. Both reach 100% core progress in two 50-minute sessions; optional extensions are tracked separately.
- **Local progress & privacy:** Records and student code are stored locally in your workspace under `.hi-agent-seminar/v2/` and `hi-agent-seminar-work/v2/`—nothing is uploaded to GitHub. Never paste API keys into chat or GitHub issues.
- **For instructors & maintainers:** See `PUBLISHING.md` for release and integrity checks (`prepare-release.py` / `verify-package.py`), `VERIFICATION.md` for test coverage, and `persona.md` / `MENTOR.md` / `OUTPUT.md` for teaching rules.
