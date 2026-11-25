# Bugs get their own issue, branch and PR
A bug is wrong behaviour in code that is already on main, found while working on another issue, in CI or by a test.
Never fix it inside the current branch or PR. Instead:
1. Open an issue "[<area>] Fix <what is wrong>" with labels type:bug, the area, the priority of the feature it breaks, urgency:high if it blocks work, status:ready, and the current milestone. Body: what happened, steps to reproduce, expected vs actual, logs, where it was found (#issue or PR).
2. Add it under "Open bugs and risks" in .claude/context.md.
3. Create branch `fix/<bug#>-<slug>` from main. First add a test that fails because of the bug, then fix it.
4. Open a new PR with "Fixes #<bug#>"; remove the bug from "Open bugs and risks" in that PR. Link the bug from the issue or PR where it was found.
