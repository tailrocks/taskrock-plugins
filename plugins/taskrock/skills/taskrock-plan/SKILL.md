---
name: taskrock-plan
description: >-
  Turn the work discussed in this conversation into a plan on GitHub with taskrock. An initiative, epics and tasks, with blockers and with who builds and who reviews each task. Use when the user asks to plan work on GitHub or types /taskrock-plan. Do not use it to build a task: use taskrock-issue for one task and taskrock-goal for a whole plan.
license: Apache-2.0
---

# Plan work on GitHub

## Use this skill

You turn what the user explained into issues on GitHub. Another agent, on a weaker model, builds each task later with no other context. So you make every design decision now and write it into the task.

Use this skill when the user asks to plan work on GitHub or types `/taskrock-plan`.
This skill only plans. Use `taskrock-issue` to build one task. Use `taskrock-goal` to build a whole plan.

## Before you start

This skill needs the `taskrock` command-line tool, version 0.1.0, on PATH. It also needs the `gh` command with a signed-in GitHub account.
The GitHub organization must have the taskrock issue types and routing fields. The README of the taskrock repository gives the setup script.

Step 6 creates the issues on GitHub. The skill writes nothing else to GitHub.
Do not run step 6 before the user approves the breakdown in step 4.

## Procedure

### 0. Check the taskrock version

```sh
taskrock --version
```

It must print `taskrock 0.1.0` or a newer version. If the command is missing or prints an older version, stop and tell the user to install taskrock 0.1.0 or newer. Do not go on.

### 1. Understand first, ask last

1. Read what the user said in this conversation. Read the code and the docs it touches. Finding facts is your job.
2. Decide everything you can decide. Keep each choice as an assumption.
3. Ask the user a question only when both are true: a wrong guess would change the breakdown, and nothing settles it. Not the user's words, not the code, not the docs.
4. Ask all open questions once, in one batch, each with your suggested answer. With no open question, ask nothing.

### 2. Find the project

List the projects of the owner:

```sh
gh project list --owner <owner> --format json
```

If the work fits a project that exists, use it. If none fits, ask the user for the link of the project to use. Never create a project.

Tell the user which project you will use.

### 3. Break the work down

- One initiative. Under it, epics. Under an epic, tasks. More levels are allowed.
- Only an issue with no children is built. A parent is an `Initiative` or an `Epic`. An issue with no children is a `Task` or a `Bug`.
- A task is one session of work, one branch and one pull request. It is a narrow path through every layer that can be proven alone.
- Two tasks that change the same file get a blocker between them.
- Work only the user can do is a task whose agent is `Owner`. It blocks the tasks that wait on it.
- Settle every decision now. A decision is never an issue.

Every task names who builds it and who reviews it. Read the allowed values from the account:

```sh
gh api orgs/<owner>/issue-fields --jq '.[] | "\(.name): \([.options[].name] | join(", "))"'
```

The reviewer uses a different model than the builder.

### 4. Show the breakdown and wait

Show a short tree: each title, what blocks it, who builds, who reviews. Under it, list your assumptions. Then wait for the user to approve or change it. Show the full text of a task when the user asks for it.

### 5. Write the draft

Make a new folder outside the repository. Write `plan.toml`:

```toml
id = "holla-csv"
repo = "<owner>/holla"
project = "https://github.com/orgs/<owner>/projects/7"

[[milestones]]
title = "M1 Export"
```

Write one `.md` file per issue:

```text
+++
key = "T02"
title = "Add `--format csv` to the report command"
type = "Task"
parent = "E1"
blocked_by = ["T01"]
milestone = "M1 Export"
agent = "<builder role>"
runtime = "muse"
model = "muse-spark-1.3"
effort = "high"
review_agent = "<review role>"
review_runtime = "muse"
review_model = "muse-wonder-1.0"
review_effort = "medium"
+++
## Outcome
## Decisions already made
## Steps
## Done when
## Out of scope
```

- `parent` and `blocked_by` name the `key` of other files.
- An `Initiative` or `Epic` has no routing key. Its body has `## Outcome` and `## Done when`.
- An owner task has `agent = "Owner"` and no other routing key.

How to write a task:

- **Outcome.** What works when the task is finished.
- **Decisions already made.** Every file, type, function, command and message the builder must use. The builder decides nothing.
- **Steps.** The order of work.
- **Done when.** A checklist. Each box is a command with the result it must show.
- **Out of scope.** What the builder must not touch.

### 6. Check and create

```sh
taskrock check <folder>
taskrock apply <folder> --dry-run
taskrock apply <folder>
```

Fix the files until `check` prints `OK`. If `apply` stops, run it again. It creates nothing twice.

## Result

Print the link of the initiative and the link of the project. Delete the draft folder.

## Completion checks

Make sure that each item is true:

- `taskrock check` printed `OK` for the draft folder.
- `taskrock apply` finished without an error.
- You printed the link of the initiative and the link of the project.
- You deleted the draft folder.
