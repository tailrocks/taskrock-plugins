---
name: taskrock-issue
description: >-
  Work on one GitHub issue that was planned with taskrock. Read the task, take it, build it by its Steps, prove it by its Done when, and open the pull request. Use when the user says "Do" with the link of one issue, or when a manager hands you one task. Do not use it to plan work or to run a whole initiative, epic or project: use taskrock-plan or taskrock-goal.
license: Apache-2.0
---

# Work on one issue

## Use this skill

You get one issue link. The issue is the whole task. Build only what it says.

Use this skill when the user gives you the link of one issue that taskrock planned. Use it also when a manager hands you one task.
Use `taskrock-plan` to plan work. Use `taskrock-goal` to build everything under an initiative, an epic, or a project.

## Before you start

This skill needs the `taskrock` command-line tool, version 0.1.0, on PATH. It also needs the `gh` command with a signed-in GitHub account and the `git` command.
The input is one issue link. The issue holds the Steps, the Done when list, and the Out of scope list.

This skill changes GitHub. Step 2 takes the task for you. Step 4 pushes commits to the task branch. Step 6 opens a pull request.
The skill never merges. The manager merges.

## Procedure

### 0. Check the taskrock version

```sh
taskrock --version
```

It must print `taskrock 0.1.0` or a newer version. If the command is missing or prints an older version, stop and tell the user to install taskrock 0.1.0 or newer. Do not go on.

### 1. Read

```sh
gh issue view <link>
gh api repos/<owner>/<repo>/issues/<number> --jq '[.issue_field_values[] | "\(.issue_field_name)=\(.single_select_option.name)"] | join("; ")'
```

The second command prints who builds and who reviews. Read `AGENTS.md` in the repository too.

### 2. Take the task

Skip this step when the manager told you that the task is already taken for you.

```sh
taskrock claim <link>
```

- Exit status 0: the task is yours. Its branch `feat/issue-<number>` exists on GitHub.
- Exit status 3: the answer is no. Another agent has it, or it is not ready. Stop and say so.

### 3. Switch to the branch

```sh
git fetch origin feat/issue-<number>
git switch feat/issue-<number>
```

When other agents work in the same checkout, use your own folder:

```sh
git worktree add ../<repo>-issue-<number> feat/issue-<number>
```

Never create another branch.

### 4. Build

- Follow `Steps` in order.
- Use the names in `Decisions already made` exactly: files, types, functions, commands, messages.
- Make no design decision.
- Stay inside `Out of scope`.
- Commit often, with `git commit -s`. Push often.

### 5. Prove

Run every command under `Done when`. Keep each command and the output you saw. A box is done only after you saw the result yourself.

### 6. Open the pull request

Write the body to a file. It has four sections and one line:

```markdown
## Why
## What
## Proof
## Done when

Closes #<number>
```

`Proof` holds each `Done when` command with its output. `Done when` repeats the checklist with every box ticked.

```sh
GH_PR_CREATE_DRAFT=0 gh pr create --base <default branch> --head feat/issue-<number> --title "<type>: <summary>" --body-file <file>
```

The title follows Conventional Commits.

### When the task is wrong

The task can name a file that moved, or a step that no longer fits. Do not guess and do not push on.

```sh
gh issue comment <link> --body-file <file>
taskrock release <link>
```

Write in the comment what you found and why you cannot go on. Then stop.

## Result

Report the link of the pull request and stop. Do not merge.

When the task is wrong, the result is the comment on the issue and the released task.

## Completion checks

Make sure that each item is true:

- `taskrock claim` exited with status 0, or the manager had taken the task for you.
- You ran every command under `Done when` and saw its result yourself.
- The pull request body has the sections `Why`, `What`, `Proof`, and `Done when`, and the line `Closes #<number>`.
- You did not merge the pull request.
