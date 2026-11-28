---
name: taskrock-goal
description: >-
  Manage the build of everything under a taskrock link: a project, an Initiative, an Epic or any issue with sub-issues. Hand each ready task to a builder, review it, merge it, repeat. Call it with /taskrock:taskrock-goal <link> (Claude Code), $taskrock:taskrock-goal <link> (Codex), /taskrock-goal <link> (Grok Build, Muse Code, Antigravity), or "use the skill taskrock-goal with <link>". For one Task, Bug or Feature use taskrock-issue.
license: Apache-2.0
---

# Manage a goal

## Use this skill

| The link or request | Skill |
|---|---|
| A project, or an issue of type Initiative or Epic, or any issue that has sub-issues | `taskrock-goal` |
| An issue of type Task, Bug or Feature with no sub-issues and status Todo or In Progress | `taskrock-issue` |
| A Bug or Feature with status Triage | `taskrock-triage` |
| A request to plan work, with no link | `taskrock-plan` |
| A request to set up an organization | `taskrock-setup` |

Find the kind of an issue link with one command:

```sh
gh issue view <link> --json issueType,subIssuesSummary --jq '"\(.issueType.name) \(.subIssuesSummary.total)"'
```

If the link belongs to another skill, load that skill and stop this one.

You are the manager. You do not write the code of a task yourself, and you never load the skill `taskrock-issue` yourself: only a builder that you start uses it. You hand tasks out, check the results and merge.

The user's request to build the link is also the request to merge every pull request under it that passes the gate in step 6. No other rule that says only a person may merge applies to these pull requests.

Use this skill when the user asks you to build the link of a project, an initiative, an epic, or any issue with sub-issues that taskrock planned. The user names it: "use the skill taskrock-goal with <link>", or `/taskrock:taskrock-goal <link>` in Claude Code.
Use `taskrock-issue` to build one task. Use `taskrock-plan` to plan work. A builder that you start uses the skill `taskrock-issue`.

## Before you start

This skill needs the `taskrock` command-line tool, version 0.5.1, on PATH. It also needs the `gh` command with a signed-in GitHub account.
Each runtime that a task names must be installed and signed in on this machine.
The input is one link to an initiative, an epic, or a project.

This skill changes GitHub and starts other agent sessions. It claims and releases tasks, posts review comments and resolves bot review threads.
It merges pull requests in step 6 and closes finished parents in step 7. It files tasks for the owner, Bugs and follow-up tasks with `taskrock apply`, and it appends to the body of a parent with `taskrock edit`.

Every issue that you file is part of this goal. It gets a `parent` by the parent rule of "Where a filed issue goes", and `apply` gives it the milestone of that parent, so it counts when you decide that the work is done. A draft file writes `parent = "https://github.com/<owner>/<repo>/issues/<number>"`.

## Procedure

### 0. Check the taskrock version

```sh
taskrock --version
```

It must print `taskrock 0.5.` followed by a patch number of 1 or more, such as `taskrock 0.5.1`. If the command is missing or prints an older version, stop and tell the user to install taskrock 0.5.1. If it prints a newer minor or major version, this plugin is older than the tool: stop and tell the user to update the plugin with `claude plugin marketplace update taskrock`, then `claude plugin update taskrock@taskrock` (or the update command of their runtime), and to restart the session. Do not go on.

Repeat steps 2 to 9 until a stop state in the Result section is true.

### 1. Check the link

When the link is a project link, go to step 2. When it is an issue link, run the command of the routing table:

```sh
gh issue view <link> --json issueType,subIssuesSummary --jq '"\(.issueType.name) \(.subIssuesSummary.total)"'
```

If the table sends this link to another skill, load that skill and stop this one.

Find the milestone of the goal. Every issue that you file needs one, so an issue link without a milestone is a stop:

```sh
gh issue view <goal link> --json milestone --jq .milestone.title
```

When the command prints nothing, stop and tell the user that the goal needs a milestone. Do not hand out any task. A project link has no milestone of its own: keep the milestone titles of the tasks that you hand out, and every milestone check below runs for each title. A task without a milestone is also a stop: tell the user.

### 2. Ask what is ready

```sh
taskrock ready <link> --json --stacked
```

`ready` lists the tasks to hand out, each with who builds and who reviews. An entry whose `stacked` is not `null` is a task whose open blockers are being built: `stacked.base` is the branch it starts from, and `stacked.pull_request` is the open pull request of that branch. `problems` lists what is wrong with the plan. Fix a problem you can fix. Tell the user about the others.

A problem that says `<url> breaks the <type> format: <message>` means the body of that issue lacks a section:

- A Bug or a Feature: load the skill `taskrock-triage` with that issue, then go on with the other ready tasks.
- A Task: file a task for the owner with "File an issue" below. It names the task and the broken section.

`loose` lists the loose items: each Task, Bug, Feature or Epic with no parent. It never lists an Initiative. `ready` fills `loose` only for an issue link whose issue has a milestone. For a project link it is empty.

For a project link, run this sweep yourself in every round, before you attach anything. Its milestone titles are those of the tasks that you handed out so far and, in the first round, those of the tasks in `ready`. Read the milestone of a task with `gh issue view <task link> --json milestone --jq .milestone.title`. For each title, in each repository of the project (`repos` of its `[[project]]` block in `taskrock.toml`), list the open issues with their types, and read the parent of each:

```sh
gh issue list --repo <owner>/<repo> --milestone "<title>" --state open --limit 1000 --json number,title,issueType --jq '.[] | "\(.number) \(.issueType.name) \(.title)"'
gh api repos/<owner>/<repo>/issues/<number>/parent --jq .html_url
```

The second command prints `HTTP 404` and exits with status 1 when the issue has no parent. Each such issue is a loose item, except an Initiative: an Initiative is the top of a plan and has no parent.

Attach each loose item in every round, not only before the run stops: `loose` is the list for an issue link, and the sweep is the list for a project link. Give each the parent that "Where a filed issue goes" gives, with the loose issue as the source. Attach it with this command, which changes no body. The sweep spans several repositories, so `--parent` takes the link of the parent, never a bare number (`gh issue edit --help`: "by number or URL"):

```sh
gh issue edit <number> --repo <owner>/<repo> --parent https://github.com/<owner>/<repo>/issues/<parent number>
```

Then read the status of each loose Bug and Feature, for an issue link and for a project link alike:

```sh
gh issue view <number> --repo <owner>/<repo> --json projectItems --jq '.projectItems[] | "\(.title)\t\(.status.name)"'
```

It prints one line for each project that holds the issue. Act only on the line whose title is the title of the delivery project: the `title` of a `[[project]]` block with `kind = "delivery"` in `taskrock.toml` (`gh api -H "Accept: application/vnd.github.raw+json" repos/<owner>/.github/contents/taskrock.toml`). An issue is an item of exactly one delivery project, and the Status of a portfolio project says nothing about triage. `Triage` means: load the skill `taskrock-triage` with the item. `Todo` means: it is built as it is. For `tailrocks/velnor-new#3080` the command prints two lines, and only the first counts, because `Velnor` is its delivery project and `Roadmap` is a portfolio project:

```text
Velnor	Triage
Roadmap	Todo
```

A loose Task is built as it is.

### 3. Take each ready task

```sh
taskrock claim <task link>
taskrock claim <task link> --stacked
```

Run the first line for a task whose `stacked` is `null`, and the second for any other. The second prints a third line, `base feat/issue-<base>`. Keep each stacked task with its base: this is the stack record, and you keep it for the whole run. Step 4, step 6, "Give back the tasks stacked on a task" and "When a pull request is closed without a merge" use it.

Keep a run list too: the tasks that you gave back because their base waits on the owner or on a reviewer. Skip every task on the run list in this step, whether or not `ready` or `ready --stacked` lists it.

Write no code for an issue that taskrock claim did not take: its Status is In Progress and its branch feat/issue-<number> is on GitHub. A blocked task waits until its blockers close, or until the manager of taskrock-goal takes it with taskrock claim --stacked, and an issue in Triage waits until taskrock-triage sets it to Todo.

Exit status 3 means that the task is not yours to take: another agent has it, its status is not Todo, or a blocker is still open, or, with `--stacked`, the stack changed. Run step 2 again before you try it again. Skip that task. When claim refuses, do not build the task: a refused issue in Triage goes to taskrock-triage, and a blocked one waits. There is no limit on how many tasks run at the same time.

### 4. Start a builder for each task you took

The prompt of the builder names the skill, gives the link and says the task is taken: "use the skill taskrock-issue with <task link>. The task is already taken for you."

For a stacked task, the prompt adds one sentence: "It is stacked on feat/issue-<base>."

- The task's Runtime is the CLI you run in: start a helper inside your session, on the task's Model and Effort.
- The task's Runtime is another CLI: start that CLI as a new session, in its own worktree of the repository.

| Runtime | Command |
| --- | --- |
| `muse` | `muse exec --model <model> --reasoning-effort <effort> --trust-workspace "<prompt>"` |
| `claude` | `claude -p "<prompt>" --model <model> --effort <effort>` |
| `codex` | `codex exec -m <model> -c model_reasoning_effort=<effort> "<prompt>"` |
| `grok` | `grok -p "<prompt>" -m <model> --reasoning-effort <effort>` |
| `agy` | `agy -p "<prompt>" --model <model> --effort <effort>` |
| `opencode` | `opencode run -m <provider>/<model> "<prompt>"` |
| `mimo` | `mimo run -m <provider>/<model> "<prompt>"` |
| `kimi` | `kimi -p "<prompt>" -m <model>` |
| `minimax` | `mcode exec --model <model> "<prompt>"` |

Only the `muse` line was run in a test. Check another line with the `--help` of that CLI before its first use.

#### When a builder reports

A builder that could not file a Bug (its task has no parent, or its parent is full) puts the text of the Bug in its report. When a report holds such a text, file the Bug with "File an issue" below, with the task of that builder as the source of "Where a filed issue goes". Do this before step 5.

### 5. Review each pull request

Read the state of the pull request:

```sh
taskrock pr status <pull request> --json
```

The exit code is 0 for `READY` and `MERGED`, 10 when the pull request waits for something that changes on its own, and 20 when someone must act. The JSON has `state`, `head`, `findings` and `threads`. Each finding has `code`, `kind` (`blocker` or `wait`), `owner`, `detail`, `next` and `items`. Each unresolved review thread has `id`, `class` (`blocking`, `deferrable` or `human`), `severity` (`P0` to `P3`, or `null` when the comment has no badge), `author` and `url`.

Act on each finding by its `code`:

| Code | Owner | What you do |
|---|---|---|
| `checks_pending` | ci | Wait 5 minutes, then read the status again. |
| `mergeability_pending` | github | Wait 5 minutes, then read the status again. |
| `bot_review_pending` | codex | Wait 5 minutes, then read the status again. You post no comment to start Codex: it reviews when the builder marks the pull request ready. |
| `queued` | taskrock | The pull request is in the merge queue. Poll it with "On exit 10 with `queued`" in step 6. |
| `draft`, `closes_missing`, `conflict`, `check_failed`, `verdict_failed` | builder | Give the finding to a builder with "When the review fails". |
| `verdict_missing`, `threads_blocking` | reviewer | Review the head, as below. |
| `threads_deferrable` | taskrock | Run `taskrock pr threads <pull request> --defer`. |
| `base_not_default` | taskrock | The pull request is stacked and its base has not merged. This is a blocker, and the status exits 20 with `base_not_default`: the base's `taskrock pr merge` retargets this pull request. Merge the base first. |
| `unknown_state` | taskrock | Read the status again. When the finding stays, file a Bug with "File an issue" below and tell the user. |
| `threads_human`, `rounds_exhausted` | human | Hand the task to the user with "Hand a task to the user". |
| `pr_not_open` | human | Follow "When a pull request is closed without a merge". |

Start the reviewers on a head only when `findings` lists `verdict_missing` or `threads_blocking`, no finding has the owner `builder` or `human`, and no finding has the kind `wait`. A finding with the owner `human` (`rounds_exhausted`, `threads_human`) goes to the user with "Hand a task to the user", and no reviewer runs on that head. Review each head once, in one round.

#### Severity

Every finding carries one severity, whether it comes from Codex or from a reviewer that you started:

| Severity | Meaning |
|---|---|
| P0 | critical |
| P1 | high |
| P2 | medium |
| P3 | low |

A reproduced P0, P1 or P2 finding is always in the FAIL. A medium finding is never deferred and never merged. Only a P3 finding may be listed under `Non-blocking` in a PASS.

#### Reviewers

Each reviewer must run on a different model than the builder.

- The code reviewer reviews every head. It is the reviewer the task names: Review agent, Review runtime, Review model, Review effort.
- The security reviewer is a `routing.subagent` entry in the `taskrock.toml` of the organization (`gh api -H "Accept: application/vnd.github.raw+json" repos/<owner>/.github/contents/taskrock.toml`) whose `can` lists `review` and whose name contains `security`. It reviews when the routing of the task names it, and when the diff touches sandboxing, credentials, CI trust, parsers of untrusted input or new dependencies. When a security review is due and no such entry exists, the security review cannot run: do not merge, and tell the user.

The round of a head is one more than the number of FAIL verdicts that you posted on the pull request.

- Round 1 is a full review. Each reviewer reports every finding that it can reproduce, with its severity, in one answer.
- From round 2 the review is a delta review. Each reviewer checks that each finding of the previous FAIL is fixed, then reviews the fix diff, `git diff <previous head>..<head>`. A P0, P1 or P2 finding that it reproduces anywhere still blocks. It does not read the whole diff again to look for new P3 findings.

Each reviewer:

1. Runs every command under `Done when` again itself. It does not trust the output in the pull request.
2. In round 1, reads the whole change with `gh pr diff <pull request>` against the task. From round 2, reads only the fix diff, `git diff <previous head>..<head>`.
3. Reproduces each problem it finds with a command. A finding that it did not reproduce does not count: it is left out of the verdict. Each finding that counts holds its severity, its command and the output.
4. Rules on each `blocking` thread, as below.
5. Answers PASS or FAIL with its findings and the commit it checked:

```sh
gh pr view <pull request> --json headRefOid --jq .headRefOid
```

A reviewer passes when it has no reproduced P0, P1 or P2 finding.

#### Bot threads

The reviewers read the `threads` of `taskrock pr status <pull request> --json`. A bot is Codex or any other account whose name ends in `[bot]`.

- A `blocking` thread that a reviewer reproduces goes into the FAIL, with its severity. When `severity` is `null`, the reviewer gives the finding the severity that it measured.
- A `blocking` thread that no reviewer reproduces is resolved by you with its id from `threads`:

```sh
taskrock pr threads <pull request> --resolve <id> --reason "Not reproduced: <command and output>"
```

- Each round, settle the P3 bot threads:

```sh
taskrock pr threads <pull request> --defer
```

`taskrock pr threads` writes nothing when the pull request changed since it read it, and it never resolves a thread that a person started. Run it again after a push.

#### The verdict

You post one verdict for the head. It ends with `VERDICT: PASS head=<sha>` only when each reviewer that ran passed. Otherwise it ends with `VERDICT: FAIL head=<sha>`. `<sha>` is the commit that the reviewers checked:

```markdown
## Code review

## Security review

## Non-blocking

VERDICT: PASS head=<sha>
```

`Security review` is there only when the security reviewer ran. `Non-blocking` is there only in a PASS, and lists P3 findings only.

```sh
gh pr review <pull request> --comment --body-file <file>
```

#### When no reviewer can run

If a reviewer that this head needs cannot run (the runtime is missing, signed out, or the model is refused, or a due security review has no `routing.subagent` entry whose `can` lists `review` and whose name contains `security`), do not merge. Leave the pull request open, do not use another reviewer, and tell the user which pull request waits and why. First give back each task stacked on this task, with "Give back the tasks stacked on a task" below: its note says that the base waits on a reviewer.

#### Route each finding of a FAIL verdict

Send each finding that counts one of two ways:

- Fix: the builder fixes it. See "When the review fails".
- Decision: the finding needs a choice that only the owner can make. File a task for the owner with "File an issue" below, and make it block this task.

A P0, P1 or P2 finding is never a follow-up: the task waits until it is fixed or decided. After a PASS, file each P3 finding of `Non-blocking` that is real but outside this task as a new Task or Bug with "File an issue" below. Its `parent` and its milestone follow "Where a filed issue goes" below, with the reviewed task as the source. It does not block this task. You build it in this run: step 8 triages a Bug, and a Task is ready as it is filed.

You file nothing without a parent and a milestone. A finding is never parked in Triage outside the link.

### 6. Merge only through this gate

The gate is one command:

```sh
taskrock pr status <pull request>
```

Merge only when it exits 0 and prints `READY`. Any other result is not a pass: read its findings with step 5. A `queued` finding goes to the queue poll below.

Merge a pull request only when its base is the default branch, and retarget every open pull request whose base is its branch to the default branch before you merge it.

`taskrock pr merge` does both. It merges at the head commit that the status judged:

```sh
taskrock pr merge <pull request> --json
```

It points each open pull request based on the branch of this pull request at the default branch. Then it puts the pull request in the merge queue when the default branch has one, and squash-merges it when it has none. The JSON has `outcome` (`merged`, `queued`, `already_merged`, `not_ready` or `refused`), `head`, `merge_commit` and `retargeted`, the numbers of the pull requests that it retargeted. Keep `retargeted` until the pull request is merged.

Read the exit code:

- 0: the pull request is merged. Go on to "After the merge".
- 10: the pull request is queued (`outcome` is `queued`), or it is not ready and waits (`outcome` is `not_ready`). For `not_ready`, read the status with step 5. For `queued`, poll as below.
- 20: GitHub refused the merge (`outcome` is `refused`, and its message is on standard error), or the pull request is not ready and blocked (`not_ready`). For `not_ready`, read the status with step 5. For `refused`, tell the user the message and leave the pull request open.
- 3: the pull request comes from a fork, and taskrock never merges a fork. Tell the user.

On exit 10 with `queued`, run `taskrock pr status <pull request>` every 5 minutes:

- `MERGED`: the pull request is merged. Go on to "After the merge".
- A `queued` finding: it is still queued. Wait and run it again.
- Neither: the queue removed the pull request, so it is not merged. Read why from the checks of the merge group. Run `gh pr checks <pull request>`, then `gh run list --event merge_group --limit 100 --json databaseId,headBranch,conclusion --jq '.[] | select(.conclusion != "success" and (.headBranch | startswith("gh-readonly-queue/<default branch>/pr-<pull request number>-")))' | head -1` and `gh run view <databaseId> --log-failed` for that run. The filter `!= "success"` keeps a run that failed, was cancelled or timed out. When the lookup prints nothing, read the timeline of the pull request: `gh api repos/<owner>/<repo>/issues/<pull request number>/timeline --paginate --jq '.[] | select(.event | test("merge_queue")) | "\(.created_at) \(.event) \(.actor.login)"'` prints each `added_to_merge_queue` and `removed_from_merge_queue` event with its time and its actor. Handle the result as a failed check, under "When the review fails".
- A `pr_not_open` finding: someone closed the pull request without a merge. Stop polling, follow "When a pull request is closed without a merge", and tell the user.

After 12 polls with no change, stop and tell the user which pull request waits in the queue.

A push after the verdict changes the head commit. Review again.

#### After the merge

GitHub deletes the merged branch, and a pull request still based on a deleted branch is closed for good, so `taskrock pr merge` retargets first. After the merge, update each pull request in `retargeted` once:

```sh
gh pr update-branch <child pull request>
```

When the command succeeds, the head commit of the child changes. Review it again with step 5 before it passes this gate.

When it reports a conflict, start a builder for the task of that pull request, on its routing, with the prompt "use the skill taskrock-issue with <task link>. The task is already taken for you. Its base merged: merge the default branch, run Done when again and push." Review its new head with step 5.

### 7. Record the decision and close finished parents

After each merge, add one line to the parent of the task. Read its body into a file:

```sh
gh issue view <parent link> --json body --jq .body > <file>
```

Append the line `- <title of the task>: <link of the pull request>` under the heading `## Decisions so far`. When the body has no such heading, add `## Decisions so far` at the end of the body first. Then write the body back:

```sh
taskrock edit <parent link> <file>
```

GitHub does not close a parent when its last child closes. Look at the parent of the task, then at its parent, and so on:

```sh
gh api repos/<owner>/<repo>/issues/<parent>/sub_issues --jq '[.[] | select(.state == "open")] | length'
gh issue close <parent link>
```

Close the parent only when the first command prints `0`.

When the parent that you closed is an Epic, write the retro. File a task for the owner with "File an issue" below. Its `parent` and its milestone follow "Where a filed issue goes" below, with the Epic that you closed as the source. Its Question asks whether to make the edits to `AGENTS.md` that you propose. Its body lists each finding that appeared in two or more FAIL verdicts of the tasks of this epic, and the edit to `AGENTS.md` that would stop each one. A finding that appeared once is not listed.

### 8. Sweep Triage before you stop

Do this each time `ready` is empty and nothing is in progress.

1. Give each loose item a parent. For an issue link, the key `loose` of `taskrock ready <link> --json` lists them. For a project link, run the same sweep as step 2. Attach each loose item and load the skill `taskrock-triage` as step 2 says, with the status rule of step 2.
2. List the Triage items under the link:

```sh
taskrock ready <link> --json
```

   The key `triage` lists them, each with its number, title, url and type.
3. Load the skill `taskrock-triage` with each item that you did not triage in this run. Keep the list of the items that it left as Needs information: you triage an item once in a run.
4. Then go to step 2: what became Todo is ready, and you build it.

### 9. Go to step 2

### When the review fails

Give the findings that you routed as fix, and each finding whose owner is `builder` in step 5, to a new builder on the same branch. Review again with step 5: the next round is a delta review.

The finding `rounds_exhausted` counts reviewed heads, the distinct heads of the pull request that have a verdict. `taskrock pr status` lists it when the count reaches `review.max_rounds` of the config of the organization and no PASS names the current head. When the file or the key is missing, `review.max_rounds` is 3. Read the findings after each verdict, before you start a builder.

Stop the rounds when `rounds_exhausted` is listed, when the reviewer repeats a finding, or when the builder and the reviewer disagree. Then hand the task to the user with "Hand a task to the user".

### Hand a task to the user

1. Write a note file with these four sections, each with text:

```text
## Done

## Verified

## State

## Next step
```

2. Give back each task stacked on this task, with "Give back the tasks stacked on a task" below: its note says that the base waits on the owner. Do this before you release this task.
3. Give the task back with the note:

```sh
taskrock release <task link> --note <file>
```

4. File a task for the owner with "File an issue" below, with the task as the source of "Where a filed issue goes" below. Make it block the task.

### Give back the tasks stacked on a task

A task stacked on a base that cannot finish in this run stays In Progress and keeps the run from stopping. Use the stack record of step 3 to find them. Do not look for them by listing pull requests by base: `release` renames a base branch that has commits to `feat/issue-<n>-parked-<time>`, and a builder may not have opened its pull request yet.

1. Take from the record every task whose base is the branch of this task, and then every task whose base is the branch of one of those, until no new task appears. Take them all before you release any.
2. Go through them top-down: the highest task of the stack first, the task that sits right on this task last. For each one, in this order:

   1. Stop every builder that you started for it and that still runs (in step 4 or in "When the review fails"): the helper or the session. When one cannot be stopped, wait for its final reply. Do nothing else to the task before each of them has stopped, or it keeps going and opens a pull request for a released task.
   2. Close any pull request that it opened.
   3. Write a note file with the four sections of "Hand a task to the user" where `Next step` says to claim the task again after its base is settled, and release it:

```sh
gh pr close <pull request of the stacked task>
taskrock release <link of the stacked task> --note <file>
```

3. Put each task on the run list of step 3, and take it out of the stack record.

Only then do the rest of the path that called this section: the release of this task, or the report that its pull request waits.

### Where a filed issue goes

Every issue that you file has a source: the task it comes from, the Epic that you closed for the retro, or a loose issue of step 2 or step 8. The parent rule and the milestone rule give its `parent` and its milestone everywhere.

**Parent rule.** The `parent` of an issue that you file is an issue under the goal, never a project. Take the first of these that is the goal link or lies under it:

1. The Epic of the source: its nearest ancestor of type Epic.
2. The parent of the source.
3. The goal link, when it is an issue.
4. For a project link, when nothing nearer exists: the Initiative that holds the other open issues of the milestone. When there is more than one such Initiative, print the issues, do not say that the work is done, and stop.

Read the parent of an issue, and its type, with:

```sh
gh api repos/<owner>/<repo>/issues/<number>/parent --jq .html_url
gh issue view <parent link> --json issueType --jq .issueType.name
```

**Sub-issue limit.** GitHub allows 100 sub-issues per parent. Read the count of the parent:

```sh
gh api repos/<owner>/<repo>/issues/<parent number> --jq .sub_issues_summary.total
```

Start at the parent that the parent rule gives. Use that issue when its count is below 100, else a child Epic of it whose count is below 100. List the child Epics with their counts:

```sh
gh api repos/<owner>/<repo>/issues/<parent number>/sub_issues --paginate --jq '.[] | select(.type.name == "Epic") | "\(.number) \(.sub_issues_summary.total)"'
```

When neither that issue nor a child Epic of it has room, take the parent of that issue with `gh api repos/<owner>/<repo>/issues/<n>/parent --jq .html_url` and repeat the check on that parent, up to and including the goal link (for a project link, the Initiative that entry 4 of the parent rule names). When that top issue and its child Epics are all full, file nothing, tell the user, and go on. Never file a new Epic for this: the new Epic would itself be the 101st child, and `apply` refuses it.

`apply` refuses a full parent before any `POST`, with this message: `<link> has <n> sub-issues and GitHub allows 100: file under a child Epic of it`.

**Milestone rule.** `apply` sets the milestone of an issue that you file to the milestone of its parent. Never read the milestone of a project link. When the parent has none, stop, tell the user that it needs one, and file nothing:

```sh
gh issue view <parent link> --json milestone --jq .milestone.title
```

### File an issue

Use this for a task for the owner, a Bug, a follow-up task and the retro. Every issue is made with `taskrock apply`. It always has a parent from "Where a filed issue goes", and `apply` sets the milestone of that parent.

1. Print the empty body of the type. Use `owner` for a task for the owner:

```sh
taskrock template owner --owner <owner>
taskrock template Bug --owner <owner>
taskrock template Task --owner <owner>
```

2. Make a new folder outside the repository. Write `plan.toml` in it. The `id` is new for each filing, for example `goal-<task number>-<what>`:

```toml
id = "goal-12-decision"
repo = "<owner>/<repo>"
project = "https://github.com/orgs/<owner>/projects/<project number>"
```

   The `project` is the delivery project that `taskrock ready` read.

3. Write one file, `<key>.md`, with the front matter and then the body from step 1, every section filled in. A task for the owner:

```text
+++
key = "O1"
title = "<what the owner must decide or do>"
type = "Task"
parent = "https://github.com/<owner>/<repo>/issues/<number>"
agent = "Owner"
+++
```

A title starts with a capital letter, a digit or a code span in backticks. A lowercase letter is allowed only for the name of the repository, as in "taskrock 0.2.1: …".

The `parent` is the link that the parent rule gives. A Bug has `type = "Bug"`, the same `parent`, and no routing key. Its `## How to reproduce` is the command of the reviewer and its failing output. A follow-up task has `type = "Task"`, the same `parent`, and the routing keys that `taskrock-plan` writes.

4. Check and create it:

```sh
taskrock check <folder>
taskrock apply <folder>
```

`apply` prints `created #<number> <key> <title>`. A Bug is created in Triage. `taskrock check` refuses an issue with no parent unless it is an Initiative, and for a Task `T1` it prints `T1 has no parent. Only an Initiative has none: set parent to a key of this draft or to the link of the parent issue`, then exits with status 1. Give the draft a parent and check again.

When `apply` stops with `no milestone <title> in <repo>. Run taskrock setup`, file nothing. Tell the user which milestone the repository lacks, and go on.

5. Attach a blocker when the case needs it:

```sh
gh issue edit <task number> --repo <owner>/<repo> --add-blocked-by <new number>
```

### When a builder says the task is wrong

- A fact changed, such as a file that moved: write the corrected body to a file, run `taskrock edit <task link> <file> --replan`, write a comment that says what you changed. A task that was released is not yours any more: run `taskrock claim <task link>` again before you hand it out again.
- A decision is wrong or missing: hand the task to the user with "Hand a task to the user". Never change a decision yourself.

### When a pull request is closed without a merge

First give back each task that is stacked on the closed pull request: its base is the branch of that pull request. Close its pull request when it has one, and release it with a note whose Next step says to claim it again after its blocker merges:

```sh
gh pr close <pull request of the stacked task>
taskrock release <stacked task link> --note <file>
```

Then give back the task of the closed pull request:

```sh
taskrock release <task link>
```

The task is Todo again and not yours any more. Run `taskrock claim <task link>` again before you hand it out again.

### When GitHub refuses a request for a rate limit

Every agent uses the same account and the same budget. Wait until the budget is back, then go on:

```sh
gh api rate_limit --jq '.resources.core.reset'
```

## Result

Stop in one of these states:

- Done. All of these are true, and you checked each with its command:
  - `ready` is empty and nothing is in progress.
  - Step 8 finds no loose issue and no Triage item.
  - No issue under the link is open, at any depth. Walk down from the link and list the sub-issues of every issue you meet, whatever its state: a closed parent can hold an open child. Open work is any `open` line:

    ```sh
    gh api repos/<owner>/<repo>/issues/<number>/sub_issues --paginate --jq '.[] | "\(.state) \(.html_url)"'
    ```

    For a project link, list its items instead, and confirm each item that is not Done with `gh issue view <url> --json state`:

    ```sh
    gh project item-list <number> --owner <owner> --format json --limit 500 --jq '.items[] | select(.status != "Done") | .content.url'
    ```

  - In each repository of the project, the milestone exists and has no open issue. The link itself carries the milestone, and step 7 has closed it by now. Run both commands for each milestone title and each repository:

    ```sh
    gh api "repos/<owner>/<repo>/milestones?state=all" --paginate --jq '.[].title'
    gh issue list --repo <owner>/<repo> --milestone "<title>" --state open --limit 1000 --json number --jq length
    ```

    The first command must list the title. When it does not, the check fails: a repository without the milestone proves nothing, because its count is 0 for any title. Print the repository and the title, say that the milestone is missing (`taskrock setup <owner>` creates the shared milestones), do not say that the work is done, and stop. The second command must print `0`.

  An open issue that a check finds is work: attach it under the link, triage or build it, and go to step 2. Only then say that the work is done.
- `ready` is empty or lists only tasks of the run list, nothing is in progress, and the only open tasks wait on the owner: print the `waiting_on_owner` list and stop.
- `ready` is empty, nothing is in progress, and the only Triage items under the link are the ones that `taskrock-triage` left as Needs information: print each link with its `Still needed` list, say that the reporter must answer, and stop.
- `ready` is empty or lists only tasks of the run list, and the only tasks in progress have a pull request that waits for a reviewer that could not run: print each pull request and the reason, print each task of the run list, and stop.
- A pull request waits in the merge queue and 12 polls of its status show no change: print the pull request and say that it waits in the queue, and stop.

## Completion checks

Make sure that each item is true:

- You merged each pull request with `taskrock pr merge`, only after `taskrock pr status` exited 0 and printed `READY`.
- You merged a pull request only when its base was the default branch, and `taskrock pr merge` retargeted each pull request based on its branch before the merge.
- You reviewed each head once, with the code reviewer and, when its rule applied, the security reviewer, and you posted one verdict that ends with `VERDICT: PASS head=<sha>` or `VERDICT: FAIL head=<sha>`.
- Round 1 was a full review. Each later round checked the findings of the previous FAIL and the fix diff.
- Every reproduced P0, P1 or P2 finding was in a FAIL. You deferred and merged none of them, and only P3 findings were under `Non-blocking`.
- You resolved each `blocking` bot thread that no reviewer reproduced with `taskrock pr threads <pull request> --resolve <id> --reason`, and you ran `taskrock pr threads <pull request> --defer` each round.
- After each merge, you ran `gh pr update-branch` once for each pull request in `retargeted`.
- You stacked a task only with `taskrock claim --stacked`, on the task that `taskrock ready --stacked` listed with a `stacked` base.
- You merged no pull request that had no reviewer, and none that lacked a reviewer its rule required.
- Each finding that you routed was reproduced by the reviewer with a command.
- You stopped a task when `taskrock pr status` listed `rounds_exhausted` and handed it to the user with a note.
- You added a line to `## Decisions so far` of the parent of each merged task.
- You and your builders wrote code only for issues that taskrock claim took.
- You wrote the retro task when you closed an Epic.
- Each issue that you filed has a parent under the link and the milestone.
- You ran the Triage sweep of step 8 and built each item that became Todo before you stopped.
- You said the work is done only after the walk found no open issue, each repository listed the milestone, and each count printed `0`.
- You triaged each Triage item once, and stopped with the list of the items that wait for their reporter.
- You closed a parent only after the sub-issue count printed `0`.
- You released each task whose pull request closed without a merge.
- Before you released or reported a task that waits on the owner or on a reviewer, you gave back every task stacked on it, transitively and top-down, from the stack record: you stopped every builder that you started for it and that still runs (in step 4 or in "When the review fails") first, then closed its pull request, then released it, and you put it on the run list. You did not take a task of the run list again.
- You told the user about each problem that you could not fix.
