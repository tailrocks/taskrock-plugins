# Installation

The plugin `taskrock` installs on five agent CLIs. Each one needs `taskrock` 0.5.2 or a later 0.5 patch release on `PATH` for `taskrock-goal` and `taskrock-issue`, and `gh` signed in to GitHub. The other skills also accept `taskrock` 0.5.0. Every skill checks the `taskrock` version first and stops if it is missing, too old, or on a newer minor or major version.

The commands below were run on 2026-11-26 with the versions in the table. Each agent then listed the three skills `taskrock-plan`, `taskrock-issue` and `taskrock-goal`.

| Agent | Version tested | Call a skill |
| --- | --- | --- |
| Claude Code | 2.1.332 | `/taskrock:taskrock-plan` |
| Codex | 0.172.0 | `$taskrock:taskrock-plan`, or pick it from `/skills` |
| Grok Build | 1.0.92 | `/taskrock-plan` |
| Muse Code | 1.4.25 | `/taskrock-plan` |
| Antigravity | 1.5.17 | `/taskrock-plan` |

If you installed the old plugin `tailrocks-taskrock-skills`, remove it first. Both plugins have the same skill names. The remove command for each agent is under its section.

## Build planned work

Name the skill in every request. The generic form works in all five agents. Each agent also has its own form.

| Agent | One task | A whole initiative, epic or project |
| --- | --- | --- |
| Claude Code | `/taskrock:taskrock-issue <link>` | `/taskrock:taskrock-goal <link>`, or `/goal /taskrock:taskrock-goal <link>` |
| Codex | `$taskrock:taskrock-issue <link>` | `$taskrock:taskrock-goal <link>` |
| Grok Build, Muse Code, Antigravity | `/taskrock-issue <link>` | `/taskrock-goal <link>` |
| Any agent | "use the skill taskrock-issue with `<link>`" | "use the skill taskrock-goal with `<link>`" |

## Claude Code

```sh
claude plugin marketplace add tailrocks/taskrock-plugins
claude plugin install taskrock@taskrock --scope user
```

Check with `claude plugin list`. Update with `claude plugin marketplace update taskrock`, then `claude plugin update taskrock@taskrock`, then `/reload-plugins` in a session. Remove with `claude plugin uninstall taskrock@taskrock --scope user`.

Old plugin: `claude plugin uninstall tailrocks-taskrock-skills@tailrocks --scope user`.

## Codex

```sh
codex plugin marketplace add tailrocks/taskrock-plugins
codex plugin add taskrock@taskrock
```

Check with `codex plugin list`. Update with `codex plugin marketplace upgrade taskrock`, then run the `plugin add` command again and open a new session. Remove with `codex plugin remove taskrock@taskrock`.

Old plugin: `codex plugin remove tailrocks-taskrock-skills@tailrocks`.

## Grok Build

```sh
grok plugin marketplace add tailrocks/taskrock-plugins
grok plugin install taskrock --trust
```

Grok Build also reads the marketplaces of Claude Code. If Claude Code already has the marketplace, the first command prints `Marketplace source already configured`. Go on with the second command.

Check with `grok plugin list`. Update with `grok plugin marketplace update`, then `grok plugin update taskrock`. Remove with `grok plugin uninstall taskrock`.

Old plugin: `grok plugin uninstall tailrocks-taskrock-skills`.

## Muse Code

```sh
muse plugins marketplace add taskrock tailrocks/taskrock-plugins
muse plugins install taskrock@taskrock
```

Check with `muse skills list --source plugin`. Update with `muse plugins marketplace update taskrock`, then `muse plugins remove taskrock` and the install command again. Remove with `muse plugins remove taskrock`.

Old plugin: `muse plugins remove tailrocks-taskrock-skills`.

Muse Code 1.4.25 refuses `remove` when `~/.config/muse/settings.json` has no `"schema_version": 1` at the top level. Add that member and run the command again.

## Antigravity

Antigravity installs from a local folder. It copies the plugin, so the clone can be deleted afterwards.

```sh
git clone https://github.com/tailrocks/taskrock-plugins
agy plugin install ./taskrock-plugins/plugins/taskrock
```

Check with `agy plugin list --json`. Update with `git -C taskrock-plugins pull`, `agy plugin uninstall taskrock`, and the install command again. Remove with `agy plugin uninstall taskrock`.

Old plugin: `agy plugin uninstall tailrocks-taskrock-skills`.
