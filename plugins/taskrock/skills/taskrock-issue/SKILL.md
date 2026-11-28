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

This skill needs the `taskrock` command-line tool, version 0.5.2, on PATH. It also needs the `gh` command with a signed-in GitHub account and the `git` command.
The input is one issue link. The issue holds the Steps, the Done when list, and the Out of scope list.

This skill changes GitHub. Step 3 takes the task for you. Step 5 pushes commits to the task branch. Step 8 opens a draft pull request. Step 9 marks it ready.
The skill never merges. The manager merges.

## Procedure

### 0. Check the taskrock version

```sh
taskrock --version
```

It must print `taskrock 0.5.` followed by a patch number of 2 or more, such as `taskrock 0.5.2`. If the command is missing or prints an older version, stop and tell the user to install taskrock 0.5.2. If it prints a newer minor or major version, this plugin is older than the tool: stop and tell the user to update the plugin with `claude plugin marketplace update taskrock`, then `claude plugin update taskrock@taskrock` (or the update command of their runtime), and to restart the session. Do not go on.

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

### 8. Open the pull request as a draft

Look for a pull request of the branch first. A rerun of the same task finds its own:

```sh
gh pr list --repo <owner>/<repo> --head feat/issue-<number> --state open --json url,isCrossRepository --jq '.[] | select(.isCrossRepository | not) | .url'
```

The filter skips a pull request from a fork, because `--head` matches the branch name alone and a fork can use the same name. When it prints more than one link, stop and tell the user: only one pull request of the task branch may be open. When it prints one link, reuse that pull request: do not run `gh pr create`. Write the body below with the output of step 7 and set it with `gh pr edit <pull request> --body-file <file>`. When it prints nothing, create the pull request.

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
gh pr create --draft --base <base branch> --head feat/issue-<number> --title "<type>: <summary>" --body-file <file>
```

`<base branch>` is `feat/issue-<base>` for a stacked task whose base pull request still prints `OPEN`, and the default branch for any other task.

The title follows Conventional Commits.

Codex reviews a pull request that is ready, on every push, and skips a draft. Push as often as you need while the pull request is a draft.

### 9. Mark the pull request ready

Run every command under `Done when` again when you pushed code after step 8. Then read the state of the pull request:

```sh
taskrock pr status <pull request>
```

Each finding is a line `[blocker] <code> (<owner>): <message>`. The finding `draft` is printed while the pull request is a draft. A status with no `draft` finding means the pull request is ready.

When the pull request is ready and a `builder` finding other than `verdict_failed` is left, take it out of review before the first fix, because each push to a ready pull request starts another Codex review:

```sh
gh pr ready --undo <pull request>
```

Fix every finding whose owner is `builder`, except `draft`:

- `closes_missing`: add the line `Closes #<number>` to the body, and set it with `gh pr edit <pull request> --body-file <file>`.
- `conflict`: merge the base branch, as step 7 does, and push.
- `check_failed`: fix the code, and push.

Run `taskrock pr status <pull request>` again after each fix. When you pushed code in this step, run every command under `Done when` again after the last push, write the new output into `Proof` of the pull request body, and set it with `gh pr edit <pull request> --body-file <file>`. Go on when no `builder` finding is left except `draft`. Then run one command:

```sh
gh pr ready <pull request>
```

Run it once for each round. It starts the Codex code and security review. Each push after it starts another Codex review.

Run `taskrock pr status <pull request>` once more. When no `builder` finding is left, the last line of your report is `DONE <pull request link>`. When a `builder` finding is left, follow "When a review fails" if it is `verdict_failed`. If it is not, the pull request is ready: run `gh pr ready --undo <pull request>` first, fix it as above, push, and run `gh pr ready <pull request>` once.

### When a review fails

The manager hands you the task again after a review that posted `VERDICT: FAIL`. `taskrock pr status <pull request>` then prints a `verdict_failed (builder)` finding. A round has these steps, in this order:

1. Take the pull request out of review:

   ```sh
   gh pr ready --undo <pull request>
   ```

2. Fix every finding of the FAIL verdict that the manager routed to you as Fix. The manager files a finding routed as Decision or Follow-up as its own issue: do not fix it here. When no manager routed the findings, fix every finding. Run every command under `Done when` again.
3. Push to `feat/issue-<number>`.
4. Resolve each bot thread that you fixed. `taskrock pr status --json <pull request>` lists each unresolved thread under `threads`, with its `id`, `severity` and `url`:

   ```sh
   taskrock pr threads <pull request> --resolve <id> --reason "Fixed in <sha>"
   ```

   `<sha>` is the commit that holds the fix.
5. Do step 9 again: it runs `taskrock pr status`, fixes each `builder` finding, and runs `gh pr ready <pull request>` once.

### When the base of a stacked task merged

The manager hands you the task again after the base merged and it retargeted your pull request to the default branch. The pull request is ready, and each push to a ready pull request starts a Codex review. Take it out of review before you push. The steps, in this order:

1. Take the pull request out of review. Run `taskrock pr status <pull request>`: when it prints a `draft` finding, the pull request is already a draft, so skip this command. Otherwise run:

   ```sh
   gh pr ready --undo <pull request>
   ```

2. Bring the default branch in:

   ```sh
   git fetch origin
   git switch feat/issue-<number>
   git merge origin/<default branch>
   ```

   Run every command under `Done when` again and keep the new output.
3. Push:

   ```sh
   git push origin feat/issue-<number>
   ```

4. Read the state of the pull request:

   ```sh
   taskrock pr status <pull request>
   ```

   Fix every finding whose owner is `builder`, except `draft`, as step 9 says, and run the command again after each fix. Go on when no `builder` finding is left except `draft`.
5. Run every command under `Done when` again after the last push (step 3, or a fix of step 4) and keep that output. Write it into `Proof` of the pull request body, and set it with `gh pr edit <pull request> --body-file <file>`.
6. Mark the pull request ready, once:

   ```sh
   gh pr ready <pull request>
   ```

   Then run `taskrock pr status <pull request>` once more and end the report as step 9 says. The pull request is ready now, so when a `builder` finding other than `verdict_failed` is left, take it out of review first with `gh pr ready --undo <pull request>`, fix it as step 9 says, run step 5 again after the last push, and run `gh pr ready <pull request>` once.

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

When it prints `HTTP 404` and exits 1, your task has no parent: file nothing, and put the text of the Bug in your final report. Then go on with your task.

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

(c) Write `<folder>/plan.toml` as its own `toml` block, with `id`, `repo` and `project` only. Never put `parent` in `plan.toml`. The `id` is new for each filing, `friction-<task number>-<what>`, where `<what>` is a short new word for this Bug, because `apply` skips a key that it has already created under that id. The `project` is the delivery project of your task. Its title is in `gh issue view <link> --json projectItems`, and its URL is:

```sh
gh project list --owner <owner> --format json --jq '.projects[] | select(.title == "<project title>") | .url'
```

```toml
id = "friction-<task number>-<what>"
repo = "<owner>/<repo>"
project = "https://github.com/orgs/<owner>/projects/<project number>"
```

(d) Check the folder and file the Bug:

```sh
taskrock check <folder>
taskrock apply <folder>
```

The Bug lands in Triage under the parent of your task, with the milestone of that parent, which `apply` sets. When `taskrock apply` stops with `<link> has <n> sub-issues and GitHub allows 100: file under a child Epic of it`, file nothing and put the text of the Bug in your final report, as for a task with no parent: the manager files it. When `apply` stops with `no milestone <title> in <repo>. Run taskrock setup`, file nothing. Tell the user in your final report which milestone the repository lacks, and go on with your task.

(e) Put the link of the Bug in your final report, above the last line, only when you filed one. Then go on with your task.

## Result

The last line of your report is exactly one of these:

- `DONE <pull request link>`: the pull request is ready for review and `taskrock pr status` shows no `builder` finding. Do not merge.
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
- You reused the open pull request of `feat/issue-<number>` when there was one, and opened a new pull request as a draft with `gh pr create --draft` when there was none.
- You ran `gh pr ready <pull request>` once for the round, after `taskrock pr status` showed no `builder` finding except `draft`.
- In a fix round, you ran `gh pr ready --undo <pull request>` first, and resolved each fixed bot thread with `taskrock pr threads <pull request> --resolve <id> --reason "Fixed in <sha>"`.
- When you stopped before the pull request, the note has the sections `Done`, `Verified`, `State` and `Next step`, and `taskrock release <link> --note <file>` ran.
- When you filed a friction Bug, it has the parent of your task as its parent, and apply gave it that parent's milestone, and your report names its link.
- The last line of your report is `DONE`, `BLOCKED` or `TASK_WRONG`, as described under "Result".
- You did not merge the pull request.
