# Changelog

## 0.2.0

- All skills need taskrock 0.2.0 and read the organization's `taskrock.toml`. No skill calls `gh issue create` or `gh issue edit --body`.
- `taskrock-plan`: questions in rounds with recommended answers, facts found by commands, a self-review before the tree, Done-when rules, wide changes as prefactor, expand, migrate and contract, parents with Not yet specified and Decisions so far, routing from the config.
- `taskrock-issue`: reads the comments first, merges the default branch and reruns Done when before the pull request, ends with DONE, BLOCKED or TASK_WRONG, hands off with `taskrock release --note`.
- `taskrock-goal`: verdicts bound to the head commit, only reproduced findings count, at most `review.max_rounds` failed reviews, no merge without a reviewer, a retro owner task when an epic closes, Decisions so far on parents.
- New `taskrock-triage`: checks, reproduces and routes reported Bugs and Features.
- New `taskrock-setup`: interviews the owner, writes `taskrock.toml` and runs `taskrock setup`.

## 0.1.0

- The skills `taskrock-plan`, `taskrock-issue` and `taskrock-goal` move here from `tailrocks/tailrocks-taskrock-skills`, as the plugin `taskrock` with its own marketplace.
- Manifests for Claude Code, Codex, Grok Build, Muse Code and Antigravity.
- Each skill first checks that `taskrock` 0.1.0 or newer is installed.
- The skills no longer name tailrocks roles, no longer copy a template project, and no longer carry the model routing reference.
