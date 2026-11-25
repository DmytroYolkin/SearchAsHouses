# Keep .claude/context.md up to date
Every PR that closes an issue also updates .claude/context.md in the same PR:
- Status: current milestone, what is done, in progress and next up (status:ready issues).
- Decisions: the outcome of every spike and every design choice made.
- Versions: new data asset, bundle, index or image versions.
- Latest metrics: the newest evaluate results when a pipeline ran.
- Azure credit: the amount left whenever it was checked.
- Open bugs and risks: add or remove.
- Change log: one line "date | PR # | issue # | what changed".
If a stable fact in CLAUDE.md changes (hand-in date, LLM choice, a constraint), update CLAUDE.md in the same PR. Keep context.md short: facts and links, no long text.
