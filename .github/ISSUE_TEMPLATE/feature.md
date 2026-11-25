---
name: Feature or task
about: New work (feature, test, docs, spike or chore) in the format from .claude/rules/workflow.md
title: "[<area>] <imperative>"
---
<!-- Add exactly one priority, urgency, area, type and status label, and a milestone.
status:ready if all dependencies are closed, otherwise status:backlog. Size 1-4 hours; split bigger work.
This repo is public: never paste secrets, keys or subscription IDs. -->

## Goal
<!-- 1-2 plain sentences. -->


## Tasks
- [ ]

## Acceptance criteria
<!-- Testable: a command that must succeed, a test that must pass, or a metric logged to MLflow. -->
- [ ]

## Files
<!-- Paths from the layout in CLAUDE.md. -->
-

## Depends on
<!-- One line per dependency: "- #<n> <title>", or "- None". -->
- None

## Cost note
<!-- Only if it can spend Azure credit: what spends it and how to keep it low. Delete this section otherwise. -->


## Definition of done
- [ ] PR with "Closes #<this issue>" merged, CI green
- [ ] .claude/context.md updated in that PR
- [ ] worklog written: searchashouses/report/worklog/<issue#>-<slug>.md
