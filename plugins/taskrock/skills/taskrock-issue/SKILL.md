---
name: taskrock-issue
description: >-
  Build exactly one GitHub issue of type Task, Bug or Feature that has no sub-issues, and open its pull request. Call it with /taskrock:taskrock-issue <link> (Claude Code), $taskrock:taskrock-issue <link> (Codex), /taskrock-issue <link> (Grok Build, Muse Code, Antigravity), or "use the skill taskrock-issue with <link>". If the link is a project, an Initiative, an Epic or any issue with sub-issues, use taskrock-goal instead.
license: Apache-2.0
---

# Work on one issue

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

You get one issue link. The issue is the whole task. Build only what it says.

Use this skill when the user gives you the link of one issue of type Task, Bug or Feature that has no sub-issues. The user names it: "use the skill taskrock-issue with <link>", or `/taskrock:taskrock-issue <link>` in Claude Code. Use it also when a manager hands you one task.

## Before you start

This skill needs the `taskrock` command-line tool, version 0.3.0, on PATH. It also needs the `gh` command with a signed-in GitHub account and the `git` command.
The input is one issue link. The issue holds the Steps, the Done when list, and the Out of scope list.

This skill changes GitHub. Step 3 takes the task for you. Step 5 pushes commits to the task branch. Step 8 opens a pull request.
The skill never merges. The manager merges.

## Procedure

### 0. Check the taskrock version

```sh
taskrock --version
```

It must print `taskrock 0.3.0` or a newer version. If the command is missing or prints an older version, stop and tell the user to install taskrock 0.3.0 or newer. Do not go on.

### 1. Route

Skip this step when the user gave no link, for example when a manager hands you a task that is already taken for you.

```sh
gh issue view <link> --json issueType,subIssuesSummary --jq '"\(.issueType.name) \(.subIssuesSummary.total)"'
```

Compare the answer with the routing table in "Use this skill". If the link belongs to another skill, load that skill and stop this one.

### 2. Read

```sh
gh issue view <link>
gh issue view <link> --comments
gh api repos/<owner>/<repo>/issues/<number> --jq '[.issue_field_values[] | "\(.issue_field_name)=\(.single_select_option.name)"] | join("; ")'
```

Read every comment. Triage notes and handoff notes are part of the task. A handoff note says what an earlier agent did, what it verified, the state, and the next step.
The last command prints who builds and who reviews. Read `AGENTS.md` in the repository too.

### 3. Take the task

When the manager told you that the task is already taken for you, do not claim it again. Check the claim yourself before you build:

```sh
gh issue view <link> --json projectItems --jq '.projectItems[] | "\(.title): \(.status.name)"'
gh api repos/<owner>/<repo>/branches/feat/issue-<number> --jq .name
```

The line of the delivery project must say `In Progress`, and the second command must print `feat/issue-<number>`. When either differs, write no code and stop: say that the task is not claimed.

Then find out whether the manager stacked the task on the branch of a blocker:

```sh
gh api repos/<owner>/<repo>/issues/<number>/comments --paginate --jq '.[].body | capture("<!-- taskrock:stacked-on (?<base>feat/issue-[0-9]+) -->") | .base'
```

When it prints nothing, the task starts from the default branch. When it prints a branch, the task is stacked: the last line is its base, `feat/issue-<base>`. Check the pull request of the base:

```sh
gh pr list --repo <owner>/<repo> --head feat/issue-<base> --state all --json state --jq '.[0].state'
```

It must print `OPEN` or `MERGED`. When it prints anything else, write no code and stop: say that the base of the stacked task is gone.

Otherwise claim it:

```sh
taskrock claim <link>
```

- Exit status 0: the task is yours. Its branch `feat/issue-<number>` exists on GitHub.
- Exit status 3: the answer is no. Another agent has it, its status is not Todo, or a blocker is still open. Stop and say so. When the issue is a Bug or a Feature in Triage, load the skill `taskrock-triage` with it instead, and stop this one.

Write no code for an issue that taskrock claim did not take: its Status is In Progress and its branch feat/issue-<number> is on GitHub. A blocked task waits until its blockers close, or until the manager of taskrock-goal takes it with taskrock claim --stacked, and an issue in Triage waits until taskrock-triage sets it to Todo.

### 4. Switch to the branch

```sh
git fetch origin feat/issue-<number>
git switch feat/issue-<number>
```

When other agents work in the same checkout, use your own folder:

```sh
git worktree add ../<repo>-issue-<number> feat/issue-<number>
```

Never create another branch.

### 5. Build

- Follow `Steps` in order.
- Use the names in `Decisions already made` exactly: files, types, functions, commands, messages.
- Make no design decision.
- Stay inside `Out of scope`.
- Commit often, with `git commit -s`. Push often.

### 6. Prove

Run every command under `Done when`. Keep each command and the output you saw. A box is done only after you saw the result yourself.

### 7. Merge the default branch

Other tasks may have merged while you built. Bring their work in, then prove again. A task that is not stacked, or whose base pull request prints `MERGED` now, merges the default branch:

```sh
git fetch origin
git merge origin/<default branch>
```

A stacked task whose base pull request still prints `OPEN` merges its base instead, so the review fixes of the blocker are in. Run the check of the base pull request of step 3 again first: it may have merged while you built.

```sh
git fetch origin
git merge origin/feat/issue-<base>
```

Fix any conflict. Then run every command under `Done when` again and keep the new output. Open the pull request only after every box passes on the merged branch.

### 8. Open the pull request

Write the body to a file. It has four sections and one line:

```markdown
## Why
## What
## Proof
## Done when

Closes #<number>
```

`Proof` holds each `Done when` command with its output from step 7. `Done when` repeats the checklist with every box ticked.

```sh
GH_PR_CREATE_DRAFT=0 gh pr create --base <base branch> --head feat/issue-<number> --title "<type>: <summary>" --body-file <file>
```

`<base branch>` is `feat/issue-<base>` for a stacked task whose base pull request still prints `OPEN`, and the default branch for any other task.

The title follows Conventional Commits.

### When the base of a stacked task merged

The manager hands you the task again after the base merged and it retargeted your pull request to the default branch. Bring the default branch in, prove again and push:

```sh
git fetch origin
git switch feat/issue-<number>
git merge origin/<default branch>
git push origin feat/issue-<number>
```

Run every command under `Done when` again before the push. Write the new output into `Proof` of the pull request body with `gh pr edit <pull request> --body-file <file>`. The last line of your report is `DONE <pull request link>`.

### When you stop before the pull request

The task can name a file that moved, a step that no longer fits, or a blocker that you cannot remove. Do not guess and do not push on.

Write a note file with these sections:

```markdown
## Done
## Verified
## State
## Next step
```

`Done` lists what you built. `Verified` lists each command you ran and what it printed. `State` says where the work is: the branch, the last commit, and what is wrong or what blocks. `Next step` says what the next agent should do first.

```sh
taskrock release <link> --note <file>
```

The command posts the note as a comment on the issue and gives the task back. Then stop.

### When taskrock gets in your way

When taskrock itself is the problem (a command fails for a good input, a skill step does not work, a message misleads), file a Bug, then go on with your task. Do these steps in this order.

(a) Read the parent of your task:

```sh
gh api repos/<owner>/<repo>/issues/<number>/parent --jq .html_url
```

When it prints `HTTP 404` and exits 1, your task has no parent: file nothing, and put the text of the Bug in your final report. Then go on with your task. When `taskrock apply` stops with `<link> has <n> sub-issues and GitHub allows 100: file under a child Epic of it`, file nothing and put the text of the Bug in your final report, as for a task with no parent: the manager files it.

(b) Make a folder outside the repository, and write `<folder>/B1.md` from `taskrock template Bug`, with every section filled. Its front matter is a `+++` block with `key`, `title`, `type = "Bug"` and `parent`, and no routing key. The `<number>` of `parent` is the number of the parent from step (a), never a bare number:

```text
+++
key = "B1"
title = "<what is wrong>"
type = "Bug"
parent = "https://github.com/<owner>/<repo>/issues/<number>"
+++
```

A title starts with a capital letter, a digit or a code span in backticks. A lowercase letter is allowed only for the name of the repository, as in "taskrock 0.2.1: …".

(c) Write `<folder>/plan.toml` as its own `toml` block, with `id`, `repo` and `project` only. Never put `parent` in `plan.toml`. The `project` is the delivery project of your task. Its title is in `gh issue view <link> --json projectItems`, and its URL is:

```sh
gh project list --owner <owner> --format json --jq '.projects[] | select(.title == "<project title>") | .url'
```

```toml
id = "friction-<number>"
repo = "<owner>/<repo>"
project = "https://github.com/orgs/<owner>/projects/<project number>"
```

(d) Check the folder and file the Bug:

```sh
taskrock check <folder>
taskrock apply <folder>
```

The Bug lands in Triage under the parent of your task, with the milestone of that parent, which `apply` sets. When `apply` stops with `no milestone <title> in <repo>. Run taskrock setup`, file nothing. Tell the user in your final report which milestone the repository lacks, and go on with your task.

(e) Put the link of the Bug in your final report, above the last line, only when you filed one. Then go on with your task.

## Result

The last line of your report is exactly one of these:

- `DONE <pull request link>`: the pull request is open. Do not merge.
- `BLOCKED <what blocks, and the link of the blocker>`: you stopped, wrote the note and released the task.
- `TASK_WRONG <what is wrong>`: the task is wrong, you wrote the note and released the task.

## Completion checks

Make sure that each item is true:

- You checked that the link belongs to this skill.
- You read the issue and every comment.
- `taskrock claim` exited with status 0, or the manager had taken the task for you.
- You wrote code only after taskrock claim exited with 0, or after the manager told you that it took the task for you.
- You merged the default branch into the task branch and ran every command under `Done when` again, and saw its result yourself.
- For a stacked task, you merged `origin/feat/issue-<base>` while its base pull request was open, or the default branch after it merged, and the base of the pull request was `feat/issue-<base>` or the default branch.
- The pull request body has the sections `Why`, `What`, `Proof`, and `Done when`, and the line `Closes #<number>`.
- When you stopped before the pull request, the note has the sections `Done`, `Verified`, `State` and `Next step`, and `taskrock release <link> --note <file>` ran.
- When you filed a friction Bug, it has the parent of your task as its parent, and apply gave it that parent's milestone, and your report names its link.
- The last line of your report is `DONE`, `BLOCKED` or `TASK_WRONG`, as described under "Result".
- You did not merge the pull request.
