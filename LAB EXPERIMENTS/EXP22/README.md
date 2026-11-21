# EXP22

**Aim:** Commit local changes and push them to GitHub.

**Tools used:** Git

## Steps performed
1. Cloned the repo
2. Modified README.md
3. Staged with `git add`
4. Committed with `git commit -m "Updated README"`
5. Pushed with `git push`

## Outcome
Local and remote `main` are identical (`Your branch is up to date with 'origin/main'`).

## Screenshots
1. `screenshots/01_modify.png` - Clone and modify README.md
2. `screenshots/02_stage_commit.png` - git add and git commit -m "Updated README"
3. `screenshots/03_push.png` - git push origin main

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
Remote is a local bare repo standing in for GitHub; command output is genuine.

## To repeat this on real GitHub (to get your own link)
```bash
git add README.md
git commit -m "Updated README"
git push origin main
```
