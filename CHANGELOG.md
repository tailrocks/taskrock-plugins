# Changelog

## Unreleased

- `taskrock-goal`: attaches each loose Task, Bug, Feature or Epic in every round: from the key `loose` of `taskrock ready --json` for an issue link, and from the milestone sweep for a project link. A loose Bug or Feature is triaged when it is in Triage: its number is in the `triage` key of `taskrock ready`, or, in the project-link sweep, its status is Triage. A filed issue gets its parent by the parent rule, and `apply` sets the milestone of that parent. When that parent has 100 sub-issues, the issue goes under a child Epic of it with room, else under the next entry of the parent rule up to the goal link, and nothing is filed when the goal link is full. A missing milestone stops the filing and is reported. No step sets a milestone with `gh issue edit`.
- `taskrock-goal`: files the Bug that a builder could not file (no parent, or a full parent) from the text in its report, with the task of the builder as the source.
- `taskrock-issue`: a friction Bug gets the full link of the parent of the task as its `parent`, and `apply` gives it the milestone of that parent. When the task has no parent, when its parent has 100 sub-issues, or when `apply` finds no milestone, the Bug stays in the final report and the manager files it. The plan `id` of each Bug is new, `friction-<task number>-<what>`, because `apply` skips a key that it has already created under that id.
- `taskrock-triage`: a Feature split into sub-issues gets the full link of the Feature as each `parent`, and `apply` gives each sub-issue the milestone of the Feature.
- `scripts/check.py`: fails on `gh issue edit --milestone` (also on a continuation line), on "leave out that line" in any case, on an example of an issue type with no `parent` that is a full link, and on a `taskrock-goal` whose step 2 does not name the key `loose`.

## 0.3.0

- All skills need taskrock 0.3.0.
- `taskrock-goal`: lists ready tasks with `taskrock ready --stacked`, takes a task whose blockers' pull requests are open with `taskrock claim --stacked`, merges a stack from the bottom up, and retargets each pull request to the default branch before its base merges.
- `taskrock-issue`: checks a stacked claim, merges its base branch before the pull request, opens the pull request against the base branch, and merges the default branch after the base merged.
- `taskrock-goal`, `taskrock-issue` and `taskrock-triage`: a blocked task waits until its blockers close, or until the manager takes it with `taskrock claim --stacked`.
- `scripts/check.py` checks each flag that a skill passes to `taskrock`, allows `taskrock claim --stacked` only in `taskrock-goal`, refuses a switch to any branch other than `feat/issue-<number>`, and requires the stack rule in `taskrock-goal`.

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
