# Changelog

## 0.2.1

- All skills need taskrock 0.2.1.
- `taskrock-goal`: every issue it files (a follow-up, a Bug, a task for the owner, the retro) goes under the goal with the goal's milestone. It sweeps the Triage items under the goal before it stops, and says the work is done only when the goal's milestone has no open issue.
- `taskrock-issue`: a friction Bug goes under the parent of the task, with the task's milestone.
- `taskrock-plan`: every issue has a milestone, and the Done when of an initiative counts the Bugs filed while it is built.
- `taskrock-goal`, `taskrock-issue` and `taskrock-triage`: no code is written for an issue that `taskrock claim` did not take, and an issue in Triage is never built.
- Every skill and page names the skill to call, for example `/taskrock:taskrock-goal <link>`, instead of free text.
- `scripts/check.py` fails when a skill routes a finding outside the goal, tells a person to type a build request without a skill name, or loses the claim rule or the title rule.

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
