# taskrock-plugins

The plugin `taskrock` for five agent CLIs: Claude Code, Codex, Grok Build, Muse Code and Antigravity. Its skills plan work on GitHub, build one planned issue, and manage a whole goal through review and merge with the [`taskrock`](https://github.com/tailrocks/taskrock) command-line tool.

| Skill | Use it to |
| --- | --- |
| `taskrock-plan` | Turn the work you explained into an initiative, epics and tasks on GitHub |
| `taskrock-issue` | Build one planned issue and open its pull request |
| `taskrock-goal` | Build, review and merge everything under an initiative, epic or project |

## Requirements

- `taskrock` 0.1.0 or newer on `PATH`. See the [taskrock README](https://github.com/tailrocks/taskrock#install).
- `gh` signed in to GitHub, and `git`.

## Install

See [docs/installation.md](docs/installation.md) for each agent.

## Develop

```sh
python3 scripts/check.py
```

## License

Apache-2.0. See [LICENSE](LICENSE).
