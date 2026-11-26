# Rules for agents in this repository

This repository is the marketplace and the plugin `taskrock` for Claude Code, Codex, Grok Build, Muse Code and Antigravity. The command-line tool lives in [tailrocks/taskrock](https://github.com/tailrocks/taskrock).

## Layout

- `.claude-plugin/marketplace.json`: the marketplace that Claude Code and Grok Build read.
- `.agents/plugins/marketplace.json`: the marketplace that Codex and Muse Code read.
- `plugins/taskrock/`: the plugin. One manifest for each agent and one shared `skills/` tree.
- `VERSION`: the one version of the plugin. Every manifest repeats it.
- `scripts/check.py`: the rules of the package. CI runs it.

## Rules

- Keep one skill tree. Never copy a skill for one agent.
- A change to a skill bumps `VERSION`, every manifest and `CHANGELOG.md` in the same pull request. Agents update a plugin only when its version changes.
- A skill names only `taskrock` commands that the released tool has. `scripts/check.py` runs `taskrock <command> --help` for each one.
- Release order: tag the tool in tailrocks/taskrock first, then raise the tool version that the skills and CI require.
- Run `python3 scripts/check.py` before each commit. It must print `OK`.
- Commit with `git commit -s` and a Conventional Commits title. Merge by squash.
