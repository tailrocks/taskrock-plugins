---
name: taskrock-plan
description: >-
  Turn the work discussed in this conversation into a taskrock plan on GitHub: an initiative, epics and tasks with blockers and routing. Use when the user asks to plan work. Call it with /taskrock:taskrock-plan (Claude Code), $taskrock:taskrock-plan (Codex), /taskrock-plan (Grok Build, Muse Code, Antigravity), or "use the skill taskrock-plan". It never builds: a link of an issue or project goes to taskrock-goal or taskrock-issue.
license: Apache-2.0
---

# Plan work on GitHub

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

You turn what the user explained into issues on GitHub. Another agent, on a weaker model, builds each task later with no other context. So you make every design decision now and write it into the task.

Use this skill when the user asks to plan work on GitHub, says "use the skill taskrock-plan", or types `/taskrock:taskrock-plan` (Claude Code), `$taskrock:taskrock-plan` (Codex) or `/taskrock-plan` (Grok Build, Muse Code, Antigravity).
This skill only plans. Use `taskrock-issue` to build one task. Use `taskrock-goal` to build a whole plan.

## Before you start

This skill needs the `taskrock` command-line tool, version 0.3.0, on PATH. It also needs the `gh` command with a signed-in GitHub account.
The organization must be set up with `taskrock setup`. Its file `taskrock.toml` in the repository `<owner>/.github` describes the subagents, runtimes, models, issue types and projects. Step 2 reads it.

Step 9 creates the issues on GitHub. The skill writes nothing else to GitHub.
Do not run step 9 before the user approves the tree in step 8.

## Procedure

### 0. Check the taskrock version

```sh
taskrock --version
```

It must print `taskrock 0.3.0` or a newer version. If the command is missing or prints an older version, stop and tell the user to install taskrock 0.3.0 or newer. Do not go on.

### 1. Check the link

Skip this step when the user gave no link.

When the user gave the link of an issue, run:

```sh
gh issue view <link> --json issueType,subIssuesSummary --jq '"\(.issueType.name) \(.subIssuesSummary.total)"'
```

Find the skill of the table in "Use this skill" for the kind it prints. When the kind of the link belongs to another skill, load that skill and stop. A link of a project belongs to `taskrock-goal`: load it without the command.

### 2. Read the config

```sh
gh api -H "Accept: application/vnd.github.raw" repos/<owner>/.github/contents/taskrock.toml
```

The `<owner>` is the owner of the repository that the work changes.

Keep these blocks of the file:

- `[[project]]`: the projects, each with its `key`, `kind` and `repos`.
- `[[routing.subagent]]`: each subagent with its `runtimes` and `can`.
- `[[routing.model]]`: each model with its `runtimes`, `efforts` and `use`.
- `[[issue_type]]`: the sections of each type.

When the file is missing, tell the user so and ask them to run `taskrock setup <owner>` or the `taskrock-setup` skill. Do not route from any other source. Stop here until the config exists.

### 3. Find the project

```sh
gh project list --owner <owner> --format json
```

- Pick the delivery project from the `[[project]]` blocks of the config: the block with `kind = "delivery"` whose `repos` hold the repository of the work. Match it to a project of the list by its title.
- Never use a portfolio project as the project of the plan. Never create a project.
- When no delivery project fits, or two fit, make it a question in step 4.
- When the config has a portfolio project and the user wants the initiative on it, write `portfolio = "<key>"` in `plan.toml`. The key is the `key` of the portfolio block.

Tell the user which project you will use.

### 4. Understand first, ask last

1. Read what the user said in this conversation. Read the code and the docs it touches.
2. Find every fact by running a command. Never ask the user a fact.
3. Decide everything you can decide. Keep each choice as an assumption.
4. Ask the user a question only when both are true: a wrong guess would change the breakdown, and nothing settles it. Not the user's words, not the code, not the docs.
5. Ask in rounds. A round holds every question whose prerequisites are settled. Do not ask a question that depends on an answer you do not have yet: it goes to the next round.
6. Each question is multiple choice. The recommended answer is the first choice and says why. Write each round like this:

```text
Round 1
1. <question>
   a. <recommended answer> (recommended): <why>
   b. <other answer>
2. <question>
   a. <recommended answer> (recommended): <why>
   b. <other answer>
Reply "yes" to accept every recommended answer.
```

"yes" accepts the recommended answer of every question of the round. With no open question, ask nothing.

### 5. Break down the work

- One initiative. Under it, epics. Under an epic, tasks. More levels are allowed.
- Only an issue with no children is built. A parent is an `Initiative` or an `Epic`. An issue with no children is a `Task` or a `Bug`.
- A task is one session of work, one branch and one pull request. It is a narrow path through every layer that can be proven alone. It has at most 10 steps.
- Two tasks that change the same file get a blocker between them.
- Work only the user can do is an owner task: its agent is `Owner`. It blocks the tasks that wait on it.
- Settle every decision now. A decision is never an issue. A decision only the user can make is an owner task.
- A change that touches many callers is not one task. Plan a prefactor task first. Then a task that expands: it adds the new form next to the old one. Then tasks that migrate the callers, in batches. Then a task that contracts: it deletes the old form.

Route each task from the blocks of the config. Choose in this order:

1. A subagent whose `can` has `build`.
2. A runtime from the `runtimes` of that subagent.
3. A model whose `runtimes` list that runtime. Read its `use` text to choose.
4. An effort from the `efforts` of that model.

The reviewer is a subagent whose `can` has `review`. Its model is not the model of the builder. Choose its runtime, model and effort in the same order.

### 6. Write the draft

Make a new folder outside the repository. Write `plan.toml`:

```toml
id = "holla-csv"
repo = "<owner>/holla"
project = "https://github.com/orgs/<owner>/projects/7"
portfolio = "<portfolio key>"

[[milestones]]
title = "M1 Export"
```

Leave out `portfolio` when the plan has no portfolio project.

Write one `.md` file per issue. A task:

```text
+++
key = "T02"
title = "Add `--format csv` to the report command"
type = "Task"
parent = "E1"
blocked_by = ["T01"]
milestone = "M1 Export"
agent = "<builder subagent>"
runtime = "muse"
model = "muse-spark-1.3"
effort = "high"
review_agent = "<review subagent>"
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

For any other type, run `taskrock template <type> --owner <owner>` and write the sections that it prints. The types are `Initiative`, `Epic`, `Task`, `Bug`, `Feature` and `owner`.

- `parent` and `blocked_by` name the `key` of other files. Never write a bare issue number.
- Every section that does not apply says `None.` and the reason. Never leave a section out.
- An `Initiative` or `Epic` has no routing key.
- An Initiative has the sections Outcome, Why, Not yet specified, Out of scope and Done when.
- Every issue of the plan, the Initiative and the Epics too, has a `milestone`. Its title is listed under `[[milestones]]` in `plan.toml`.
- The Done when of an Initiative starts with this line: `Friction: a Bug that an agent files while it builds this initiative is filed under this initiative, with its milestone. It counts. The initiative is not done while it is open.` Never write that such Bugs are left out of the count.
- The last box of the Done when of an Initiative counts the open issues of its milestone in every repository of the project, and the open issues under it. The Initiative has the milestone itself and is open while its box is checked, so in the repository of the Initiative the count leaves the Initiative out, by its number. In every other repository the count is plain:

```text
- [ ] For each repository of the project: `gh api "repos/<owner>/<repo>/milestones?state=all" --paginate --jq '.[].title'` lists `<milestone>` (a repository without the milestone fails this box). In each repository except the one of the Initiative: `gh issue list --repo <owner>/<repo> --milestone "<milestone>" --state open --json number --jq length` prints `0`. In the repository of the Initiative: `gh issue list --repo <owner>/<repo> --milestone "<milestone>" --state open --json number --jq '[.[] | select(.number != <initiative number>)] | length'` prints `0`. For the initiative and for each Epic, open or closed: `gh api repos/<owner>/<repo>/issues/<number>/sub_issues --paginate --jq '[.[] | select(.state == "open")] | length'` prints `0`
```
- An Epic has the sections Outcome, Decisions already made, Not yet specified, Out of scope and Done when.
- Do not write "Decisions so far" in a parent. The manager appends it later: one line for each closed child.
- An owner task has `agent = "Owner"` and no other routing key. Its sections are Outcome, Question, Why it matters, Recommended answer and Done when. Run `taskrock template owner --owner <owner>` for them.

How to write a task:

- **Title.** A title starts with a capital letter, a digit or a code span in backticks. A lowercase letter is allowed only for the name of the repository, as in "taskrock 0.2.1: …".
- **Outcome.** What works when the task is finished.
- **Decisions already made.** Every file, type, function, command and message the builder must use. The builder decides nothing.
- **Steps.** The order of work.
- **Done when.** A checklist. Each box is a command with the result it must show.
- **Out of scope.** What the builder must not touch.

Rules for Done when:

- Each box is a command in backticks and the result it must show.
- The command can fail. A command that always exits with 0 proves nothing.
- The command tests the highest public seam: the command a user runs, the endpoint a client calls.
- A Bug's box reruns the command of its How to reproduce and shows it passing. Another box names a regression test that failed before the fix.

### 7. Review the draft

Review your own draft before you show it. Fix each problem in the files.

1. Each item of the Outcome of a parent is covered by a child.
2. No step only decides something. A decision goes into Decisions already made.
3. Each name is the same in every issue: files, types, functions, commands, keys.
4. No task has more than 10 steps.
5. Each Done when box can fail.

Then run the read-only report on the draft:

```sh
taskrock check <folder> --coverage
```

Fix each note. When a note stays, write the reason under the assumptions of step 8.

### 8. Show the tree and wait

Show a short tree: each title, what blocks it, who builds, who reviews. Under it, list your assumptions and the notes that stay. Then wait for the user to approve or change it. Show the full text of a task when the user asks for it. After a change, edit the files and repeat step 7.

### 9. Check and create

```sh
taskrock check <folder>
taskrock apply <folder> --dry-run
taskrock apply <folder>
```

Fix the files until `check` prints `OK`. If `apply` stops, run it again. It creates nothing twice.

To change the body of an issue that exists, write the new body to a plain Markdown file: the sections only, with no `+++` front matter. Then run:

```sh
taskrock edit <link> <file>
```

Once a task is In Progress, `taskrock edit` refuses to change its Outcome, Decisions already made and Out of scope. Add `--replan` only when the user asked to change the plan.

## Result

Print the link of the initiative and the link of the project. Delete the draft folder. Then tell the user how to build it, and name the skill each time:

- To build the whole plan with `taskrock-goal`:
  - Claude Code: `/taskrock:taskrock-goal <initiative link>`, or `/goal /taskrock:taskrock-goal <initiative link>` for a long build.
  - Codex: `$taskrock:taskrock-goal <initiative link>`.
  - Grok Build, Muse Code and Antigravity: `/taskrock-goal <initiative link>`.
  - Any agent: "use the skill taskrock-goal with <initiative link>".
- To build one task with `taskrock-issue`: Claude Code `/taskrock:taskrock-issue <task link>`, Codex `$taskrock:taskrock-issue <task link>`, Grok Build, Muse Code and Antigravity `/taskrock-issue <task link>`, any agent "use the skill taskrock-issue with <task link>".

## Completion checks

Make sure that each item is true:

- You read the config, or told the user to set up the organization and stopped.
- The project is a delivery project of the config, never a portfolio project.
- You asked only questions that no command could answer, in rounds with a recommended answer.
- You ran `taskrock check <folder> --coverage` and fixed each note or gave the reason it stays.
- The user approved the tree.
- `taskrock check` printed `OK` for the draft folder.
- `taskrock apply` finished without an error.
- Each issue has a milestone, and the Initiative's Done when has the Friction line and the last box that counts open issues.
- You printed the link of the initiative and the link of the project, and the lines that name `taskrock-goal` and `taskrock-issue`.
- You deleted the draft folder.
