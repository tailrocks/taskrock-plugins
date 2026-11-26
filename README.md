# taskrock-plugins

The plugin `taskrock` for five agent CLIs: Claude Code, Codex, Grok Build, Muse Code and Antigravity. Its skills plan work on GitHub, build one planned issue, and manage a whole goal through review and merge with the [`taskrock`](https://github.com/tailrocks/taskrock) command-line tool.

| Skill | Use it to |
| --- | --- |
| `taskrock-plan` | Turn the work you explained into an initiative, epics and tasks on GitHub |
| `taskrock-issue` | Build one planned issue and open its pull request |
| `taskrock-goal` | Build, review and merge everything under an initiative, epic or project |
| `taskrock-triage` | Check a reported Bug or Feature and make it ready to build, or close it with the reason |
| `taskrock-setup` | Write the organization's taskrock.toml and make GitHub match it |

## Requirements

- `taskrock` 0.1.0 or newer on `PATH`. See the [taskrock README](https://github.com/tailrocks/taskrock#install).
- `gh` signed in to GitHub, and `git`.

## Install

| Agent | Commands |
| --- | --- |
| Claude Code | `claude plugin marketplace add tailrocks/taskrock-plugins` then `claude plugin install taskrock@taskrock --scope user` |
| Codex | `codex plugin marketplace add tailrocks/taskrock-plugins` then `codex plugin add taskrock@taskrock` |
| Grok Build | `grok plugin marketplace add tailrocks/taskrock-plugins` then `grok plugin install taskrock --trust` |
| Muse Code | `muse plugins marketplace add taskrock tailrocks/taskrock-plugins` then `muse plugins install taskrock@taskrock` |
| Antigravity | `git clone https://github.com/tailrocks/taskrock-plugins` then `agy plugin install ./taskrock-plugins/plugins/taskrock` |

Call a skill with `/taskrock:taskrock-plan` in Claude Code, `$taskrock:taskrock-plan` in Codex, and `/taskrock-plan` in Grok Build, Muse Code and Antigravity. [docs/installation.md](docs/installation.md) has the tested versions, updates, removal, and how to remove the old plugin `tailrocks-taskrock-skills`.

## Develop

```sh
python3 scripts/check.py
```

## License

Apache-2.0. See [LICENSE](LICENSE).
