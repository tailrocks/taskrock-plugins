# Changelog

## 0.5.1

- `taskrock-goal`: reviews each ready head once, in one round. The code reviewer reviews every head. The code reviewer is the `Review agent`, `Review runtime`, `Review model` and `Review effort` of the task. The security reviewer is a `routing.subagent` entry whose `can` lists `review` and whose name contains `security`. It reviews when the routing of the task names it, and when the diff touches sandboxing, credentials, CI trust, parsers of untrusted input or new dependencies. When a security review is due and no such entry exists, it cannot run. The manager does not merge and tells the user. A finding with the owner `human` (`rounds_exhausted`, `threads_human`) starts no review: the manager hands the task to the user. The manager posts one verdict that ends with `VERDICT: PASS head=<sha>` only when each reviewer that ran passed, and otherwise with `VERDICT: FAIL head=<sha>`.
- `taskrock-goal`: every finding carries a severity, P0 (critical), P1 (high), P2 (medium) or P3 (low), from Codex and from a reviewer alike. A reproduced P0, P1 or P2 finding is always in the FAIL, and a medium finding is never deferred and never merged. Only a P3 finding is listed under `Non-blocking` in a PASS. A P0 to P2 finding is no longer a Follow-up route: only a P3 finding of a PASS may be filed as a follow-up.
- `taskrock-goal`: round 1 is a full review. From round 2 the reviewers check that each finding of the previous FAIL is fixed and review the fix diff. A P0, P1 or P2 finding that they reproduce anywhere still blocks.
- `taskrock-goal`: the reviewers read the `threads` of `taskrock pr status <pull request> --json`. A `blocking` thread that a reviewer reproduces goes into the FAIL. The manager resolves one that no reviewer reproduces with `taskrock pr threads <pull request> --resolve <id> --reason "Not reproduced: <command and output>"`, and runs `taskrock pr threads <pull request> --defer` each round for P3 bot threads. The manager posts no `@codex review` comment: Codex reviews when the builder marks the pull request ready.
- `taskrock-goal`: the gate is `taskrock pr status <pull request>` with exit code 0 and `READY`. The finding `rounds_exhausted` replaces the manual read of `review.max_rounds`, and counts reviewed heads.
- `taskrock-goal`: merges with `taskrock pr merge <pull request> --json`, which retargets the pull requests based on the branch and queues or squash-merges. The retarget lines and `gh pr merge` are gone, with the `enqueuePullRequest` mutation and its `mergeQueueEntry` poll. A `queued` finding goes to the queue poll, not back to the review. On exit code 10 with `queued`, the manager runs `taskrock pr status <pull request>` every 5 minutes until `MERGED` or until the pull request is no longer queued, and stops after 12 polls with no change (60 polls of 60 seconds before). After the merge, `gh pr update-branch <child>` runs once for each pull request in `retargeted`, and a conflict sends the child back to its builder.
- `scripts/check.py`: the rule `merge_queue_rule` is replaced by `merge_rule`. It requires `taskrock pr status`, `taskrock pr threads`, `taskrock pr merge`, `rounds_exhausted`, the four severities and `gh pr update-branch` in `taskrock-goal`, and the queue-poll sentence, and fails on `gh pr merge`, `@codex review` and `enqueuePullRequest` there. A new rule fails on any sentence in a skill that defers a medium (P2) finding, unless it says the finding is never deferred. `base_not_default` is a blocker that exits 20: the base's `taskrock pr merge` retargets the pull request.
- The `check` task in `mise.toml` builds taskrock 0.5.1 from its release commit, `62f650229243a0e0c0b5ca3c519fca4c4776b60b`. `taskrock-goal` needs taskrock 0.5.1, because the gate relies on `pr status` counting only the newest run of each check name: 0.5.0 counts a superseded failed run. Its version gate accepts taskrock 0.5.x from 0.5.1, and `scripts/check.py` has a floor for it (`VERSION_FLOORS`). The other skills still accept 0.5.0 and later 0.5 patch releases, because 0.5.1 changes no command, flag or exit code that they name. `README.md` and `docs/installation.md` say so.

## 0.5.0

- All skills need taskrock 0.5.0. Every skill that runs `taskrock --version` accepts only taskrock 0.5.x, and `scripts/check.py` checks every `taskrock X.Y.Z` mention against `VERSION`. The `check` task in `mise.toml` builds taskrock 0.5.0 from its release commit.
- `taskrock-issue`: opens its pull request as a draft with `gh pr create --draft`, and first reuses the open pull request of `feat/issue-<number>` when a rerun finds one. The lookup skips a pull request from a fork (`isCrossRepository`), because `--head` matches the branch name alone, and a second match stops the builder. Codex skips a draft, so the builder pushes as often as it needs while the pull request is a draft.
- `taskrock-issue`: after every `Done when` command passes, it reads `taskrock pr status <pull request>` and fixes each `builder` finding except `draft`: `closes_missing` (add `Closes #<number>` to the body), `conflict` (merge the base branch) and `check_failed` (fix the code). Then it runs `gh pr ready <pull request>` once, which starts the Codex code and security review, and reports `DONE` when no `builder` finding is left.
- `taskrock-issue`: a fix round starts from a FAIL verdict (`verdict_failed`). It runs `gh pr ready --undo <pull request>`, fixes every finding that the manager routed as Fix (Decision and Follow-up findings are filed by the manager), pushes, resolves each fixed bot thread with `taskrock pr threads <pull request> --resolve <id> --reason "Fixed in <sha>"`, and runs `gh pr ready <pull request>` once.
- `taskrock-issue`: `GH_PR_CREATE_DRAFT=0` is gone from the `gh pr create` line.

## 0.4.0

- All skills need taskrock 0.4.0.
- Every skill that runs `taskrock --version` accepts only taskrock 0.4.x. On a newer minor or major version it stops and tells the user to update the plugin. `scripts/check.py` requires that stop text, and fails when a skill names another major.minor than `VERSION` in its "version X.Y.Z, on PATH" line, in `--tag vX.Y.Z`, in `taskrock X.Y.` or in a full `taskrock X.Y.Z`, in a skill, in `README.md` or in `docs/installation.md`; the title-rule example `taskrock 0.2.1: …` is exempt. A plugin patch release changes no skill text.
- `taskrock-goal`: attaches each loose Task, Bug, Feature or Epic in every round: from the key `loose` of `taskrock ready --json` for an issue link, and from the milestone sweep for a project link. A loose Bug or Feature is triaged when its status in the delivery project is Triage, read with one command for both kinds of link; only the line of the delivery project counts, so `Velnor Triage` beats `Roadmap Todo`. The sweep lists up to 1000 issues for each milestone, and `--parent` takes the link of the parent, never a bare number. A filed issue gets its parent by the parent rule, and `apply` sets the milestone of that parent. The issue goes under the parent that the parent rule gives when it has room, else under a child Epic of it with room, else the filing walks up the parent chain to the goal link, and nothing is filed when the goal link and its child Epics are full. A missing milestone stops the filing and is reported. No step sets a milestone with `gh issue edit`.
- `taskrock-goal`: files the Bug that a builder could not file (no parent, or a full parent) from the text in its report, with the task of the builder as the source.
- `taskrock-issue`: a friction Bug gets the full link of the parent of the task as its `parent`, and `apply` gives it the milestone of that parent. When the task has no parent, when `apply` stops because its parent has 100 sub-issues, or when `apply` finds no milestone, the Bug stays in the final report and the manager files it. The plan `id` of each Bug is new, `friction-<task number>-<what>`, because `apply` skips a key that it has already created under that id.
- `taskrock-triage`: a Feature split into sub-issues gets the full link of the Feature as each `parent`, and `apply` gives each sub-issue the milestone of the Feature.
- `scripts/check.py`: fails on `gh issue edit --milestone` (also on a continuation line), on "leave out that line" in any case, on an example of an issue type with no `parent` that is a full link, and on a `taskrock-goal` whose step 2 does not name the key `loose`.
- `taskrock-goal`: step 6 merges through the merge queue when the default branch has one, enqueuing the pull request with its head commit pinned by `expectedHeadOid`, and keeps `gh pr merge` when it has none; `scripts/check.py` requires `enqueuePullRequest` and `expectedHeadOid`. The merge group run of a dequeued pull request is picked from the last 100 runs by a conclusion other than `success` (failure, cancelled or timed out) and its branch prefix; when no run matches, the merge queue events of the pull request timeline are read, and either result is handled as a failed check. The head commit and the project number are named placeholders, `<head commit>` and `<project number>`. A pull request that shows no change after 60 polls of its queue entry is a stop state of the Result section.

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
