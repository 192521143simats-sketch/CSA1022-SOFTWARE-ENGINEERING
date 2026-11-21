# EXP10

**Aim:** Work with Git branches and resolve merge conflicts.

**Tools used:** Git (local bare repo standing in for GitHub)

## Steps performed
1. Cloned the shared repo
2. Created and switched to a feature branch
3. Edited README and committed
4. Pushed to the remote
5. Pulled latest main (teammate had changed the same line)
6. Merged main into the feature branch -> conflict
7. Edited the file to resolve it
8. Marked resolved with `git add`, committed the merge
9. Pushed the branch

## Outcome
Conflict was detected, fixed by hand and the merged branch was pushed. See `CONFLICT_SUMMARY.md`.

## Screenshots
1. `screenshots/01_clone.png` - Clone the shared repository
2. `screenshots/02_branch_commit_push.png` - Create branch, edit README, commit and push
3. `screenshots/03_teammate_push.png` - Teammate pushes a change to main
4. `screenshots/04_pull_main.png` - Pull the latest main and switch back to feature branch
5. `screenshots/05_conflict.png` - Merge conflict detected
6. `screenshots/06_resolve.png` - Resolve the conflict manually and mark it resolved
7. `screenshots/07_commit_push.png` - Commit the resolved merge and push (ready for pull request)

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
The teammate and the 'GitHub' remote are local simulations on this computer, so no real pull request page exists. All git output shown is genuine.

## To repeat this on real GitHub (to get your own link)
```bash
git clone https://github.com/<owner>/<repo>.git && cd <repo>
git checkout -b feature/readme-update
git commit -am "Update README" && git push -u origin feature/readme-update
git checkout main && git pull origin main
git checkout feature/readme-update && git merge main    # conflict appears
# edit file, remove markers
git add README.md && git commit -m "Resolve conflict" && git push
```
