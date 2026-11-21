# EXP15

**Aim:** Create a GitHub repository and implement version control for a team.

**Tools used:** Git, GitHub (simulated locally)

## Steps performed
1. Created the team repo with a skeleton
2. Created branches module/auth, module/payments, module/ui
3. Reviewed and merged them into main with merge commits
4. Hit and resolved a README merge conflict
5. Documented the workflow in README.md

## Outcome
`main` contains all three modules and a README that explains the workflow.

## Screenshots
1. `screenshots/01_setup.png` - Set up the team repository
2. `screenshots/02_branches_part1.png` - Branches created for individual modules
3. `screenshots/02_branches_part2.png` - Branches created for individual modules
4. `screenshots/03_merge.png` - Branches merged into main after review
5. `screenshots/04_conflict.png` - Conflict while merging the README branch
6. `screenshots/05_resolved.png` - Conflict resolved, README documents the workflow

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
Team members (Priya, Arun) and the remote are simulated locally; there is no real GitHub link yet. Use `REPOSITORY_LINK.md` after you push this to your own GitHub repo.

## To repeat this on real GitHub (to get your own link)
```bash
git init team-project && cd team-project
# copy the files from EXP15/project/ here
git add . && git commit -m "Initial commit"
git remote add origin https://github.com/<you>/team-project.git
git push -u origin main
```
