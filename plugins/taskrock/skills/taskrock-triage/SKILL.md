---
name: taskrock-triage
description: >-
  Triage a Bug or Feature whose status is Triage: check it, reproduce it, then make it ready (Todo) or close it with a reason. Use when the user asks to triage, or gives the link of an issue in Triage.
license: Apache-2.0
---

# Triage a Bug or Feature

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

You get a Bug or a Feature that someone reported. A report is incomplete on purpose. You check it against the code and decide: make it ready to build, ask for what is missing, or close it with the reason. A builder on a weaker model builds a ready issue later with no other context. So you make every design decision now and write it into the issue.

Use this skill when the user asks to triage, or gives the link of an issue or a project whose Bug or Feature has the status Triage.
Use `taskrock-plan` to plan work. Use `taskrock-issue` to build one ready issue. Use `taskrock-goal` to build a whole plan.

## Before you start

This skill needs the `taskrock` command-line tool, version 0.2.1, on PATH. It also needs the `gh` command with a signed-in GitHub account and the `git` command.
The input is the link of one issue, or the link of a delivery project. The status of each issue it triages is Triage.

This skill changes GitHub. Step 5 edits the body, the routing fields and the status of an issue, can create sub-issues, posts comments and closes issues.
Every comment starts with the line `_Written by an agent._`.
The skill never builds the issue and never merges.

## Procedure

### 0. Check the taskrock version

```sh
taskrock --version
```

It must print `taskrock 0.2.1` or a newer version. If the command is missing or prints an older version, stop and tell the user to install taskrock 0.2.1 or newer. Do not go on.

### 1. Route the link

When the user gave the link of an issue, find its kind:

```sh
gh issue view <link> --json issueType,subIssuesSummary --jq '"\(.issueType.name) \(.subIssuesSummary.total)"'
```

A Bug or a Feature with no sub-issues stays here only when its status is Triage (step 3 shows the status). Any other issue goes to the skill that the table names: load it and stop.
A project link stays here when the user asks to triage. Use `taskrock-goal` for a project link when the user asks to build.

### 2. Read the config

```sh
gh api -H "Accept: application/vnd.github.raw" repos/<owner>/.github/contents/taskrock.toml
```

The file holds the formats of the issue types and the subagent and model blocks for routing. When it is missing, say so and use `taskrock template <type> --owner <owner>` for the formats.

### 3. List the Triage items

With an issue link, find its project. The title is the name of the project:

```sh
gh issue view <link> --json projectItems --jq '.projectItems[].title'
gh project list --owner <owner> --format json --jq '.projects[] | select(.title == "<title>") | .number'
```

List the items of the project:

```sh
gh project item-list <number> --owner <owner> --format json --limit 200
```

Keep the items whose `status` is `Triage`. With an issue link, keep only that issue.
Read the type of each issue. Triage only a `Bug` or a `Feature`:

```sh
gh api repos/<owner>/<repo>/issues/<number> --jq '.type.name'
```

Do steps 4 to 6 for one issue at a time.

### 4. Check the issue

Read the issue, its comments, and `AGENTS.md` of its repository:

```sh
gh issue view <link>
gh issue view <link> --comments
```

Then, before you decide anything:

1. Search the code for an existing implementation. Use the words of the report. Do it on the up-to-date default branch.

```sh
git fetch origin
git grep -n -i "<words>" origin/<default branch>
```

2. For a Bug, run the command under `## How to reproduce`. Keep its output. Read the code until you know the cause.
3. Search the closed issues that were rejected for the same request:

```sh
gh issue list --repo <owner>/<repo> --state closed --search "<words> reason:not-planned"
```

Open each hit that looks the same and read its reason.

Write down what you established. Each fact is a command and its output, or a file and a line.

### 5. Decide

The result is one of three outcomes.

#### Ready

Use it when the report is true, it is not built yet, and you can make every decision.

1. Get the sections of the type:

```sh
taskrock template <type> --owner <owner>
```

2. Write the whole body to a file, with no front matter. Keep the sections of the report and add the build sections. A Bug adds `## Cause`, `## Decisions already made`, `## Steps`, `## Done when` and `## Out of scope`. A Feature adds `## Decisions already made`, `## Steps`, `## Done when` and `## Out of scope`. A section that does not apply says `None.` and the reason.
   - **Decisions already made.** Every file, type, function, command and message the builder must use. The builder decides nothing.
   - **Done when.** A checklist. Each box is a command with the result it must show. The command can fail. It tests the highest public seam. A Bug's list includes its `How to reproduce` command passing and a regression test that failed before the fix.
3. Replace the body:

```sh
taskrock edit <link> <file>
```

4. Set the eight routing fields as `taskrock-plan` does. Read the allowed values and the field IDs from the account. Pick a subagent that can build, then a runtime from its list in the config, then a model that lists that runtime (use its `use` text to choose), then an effort from that model. The reviewer is a subagent that can review, on a different model.

```sh
gh api orgs/<owner>/issue-fields --jq '.[] | "\(.id) \(.name): \([(.options // [])[].name] | join(", "))"'
```

Write one JSON file with an entry for each of `Agent`, `Runtime`, `Model`, `Effort`, `Review agent`, `Review runtime`, `Review model` and `Review effort`. Each entry is `{"field_id": <ID of the field>, "value": "<option name>"}`:

```json
{"issue_field_values": [{"field_id": 123, "value": "<option name>"}]}
```

Then set them:

```sh
gh api -X POST repos/<owner>/<repo>/issues/<number>/issue-field-values --input <file>
```

5. Set the Status to Todo:

```sh
gh project view <number> --owner <owner> --format json --jq .id
gh project field-list <number> --owner <owner> --format json --jq '.fields[] | select(.name == "Status")'
gh project item-edit --project-id <project id> --id <item id> --field-id <Status field id> --single-select-option-id <Todo option id>
```

6. Check that the issue is ready. It must be listed with no problem:

```sh
taskrock ready <project link>
```

A Feature that is too big for one task gets sub-issues instead of Steps. Make a folder outside the repository with `plan.toml` (a new `id`, plus `repo` and `project`) and one file for each sub-issue, with no `parent` key. Write each sub-issue as `taskrock-plan` does. The folder holds the sub-issues only, never the Feature. Then:

```sh
taskrock check <folder>
taskrock apply <folder>
```

`apply` prints `created #<number> <key> <title>` for each sub-issue. Attach each one to the Feature:

```sh
gh issue edit <sub-issue number> --repo <owner>/<repo> --parent <link of the Feature>
```

Delete the folder. The Feature is now a parent: set its Status to Todo as in item 5. Do not set its routing fields.

#### Needs information

Use it when a fact is missing that nothing you can run or read settles. The issue stays in Triage. Add no label. Write the comment to a file and post it:

```markdown
_Written by an agent._

## Established
## Still needed
```

`Established` lists what you checked, each with its command and output. `Still needed` lists each question the reporter must answer.

```sh
gh issue comment <link> --body-file <file>
```

#### Rejected

Use it when the issue is a duplicate, cannot be reproduced on the default branch, is already built, or is out of scope. Write the reason to a file. It starts with the line `_Written by an agent._`, names the evidence (the link of the duplicate or the closed `reason:not-planned` issue, the command that passes, or the file that already has it) and says why the issue is rejected, so a later search finds it. Then:

```sh
gh issue comment <link> --body-file <file>
gh issue close <link> --reason "not planned"
```

### 6. Go on

Do step 4 and step 5 for the next issue of step 3. When the list is empty, stop.

## Result

Print one line for each issue: its link, and Ready, Needs information or Rejected with the reason in a few words.

Then give the next step for each Ready issue, and name the skill: in Claude Code `/taskrock:taskrock-issue <link>`, in the other agents "use the skill taskrock-issue with <link>". For a Feature that you split into sub-issues, name `taskrock-goal` the same way: `/taskrock:taskrock-goal <link>` or "use the skill taskrock-goal with <link>".

## Completion checks

Make sure that each item is true:

- Each issue you made ready has its build sections, the eight routing fields and the status Todo, and `taskrock ready` lists it with no problem.
- Each issue that needs information has a comment with `Established` and `Still needed`, and is still in Triage.
- Each rejected issue has a comment with the reason, and is closed as not planned.
- Every comment you posted starts with `_Written by an agent._`.
- You changed an issue body only with `taskrock edit`, and created sub-issues only with `taskrock apply`.
- You did not build the issue.
- The next step of each Ready issue names the skill `taskrock-issue` or `taskrock-goal`.
