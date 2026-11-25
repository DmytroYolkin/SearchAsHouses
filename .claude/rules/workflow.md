# Workflow: issue -> branch -> PR
- All work starts from a GitHub issue. Each issue gets its own branch `<issue#>-<slug>` from main and its own PR with "Closes #<issue#>". Never mix two issues in one PR.
- New work found while solving an issue (a missing piece, a follow-up, a bug) becomes a new issue first, with its own branch and PR. Do not widen the current PR. Bugs follow bugs.md.
- A new issue gets: title "[<area>] <imperative>", one priority, urgency, area, type and status label, a milestone, and the body format below. Size 1-4 hours; split bigger work.
- Status labels: status:backlog -> status:ready (when all dependencies are closed) -> closed (Done). Refused: close as "not planned", add status:refused and one comment with the reason.
- CI must be green before merge. Every merged PR follows context-update.md and report.md.
- Claude opens the PR and stops there; I review and merge it. Never merge a PR without my review.
- No exceptions: even the first issue (#6) used a branch and a PR. main only got one empty "Initial commit" so the PR had a base.
- Attribution: Easy tasks (docs, chores, spikes, config, small fixes) get no Claude attribution. If unsure, ask.

Issue body format:
~~~markdown
## Goal
1-2 plain sentences.
## Tasks
- [ ] small concrete steps
## Acceptance criteria
- [ ] testable: a command that must succeed, a test that must pass, or a metric logged to MLflow
## Files
- paths from the layout in CLAUDE.md
## Depends on
- #<n> <title>   (or "None")
## Cost note
Only if it can spend Azure credit: what spends it and how to keep it low.
## Definition of done
- [ ] PR with "Closes #<this issue>" merged, CI green
- [ ] .claude/context.md updated in that PR
- [ ] worklog written: searchashouses/report/worklog/<issue#>-<slug>.md
~~~
