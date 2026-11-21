# EXP24

**Aim:** Create a feature branch with a login function and merge it into main via pull request.

**Tools used:** Git, GitHub (simulated locally), Python

## Steps performed
1. Created branch `feature-login`
2. Added `login.py` and `test_login.py`
3. Committed and pushed
4. Opened PR (diff) feature-login -> main and merged it

## Outcome
`login.py` is now on `main`; tests pass.

## Screenshots
1. `screenshots/01_branch.png` - Create branch feature-login
2. `screenshots/02_login_py.png` - login.py works and its tests pass
3. `screenshots/03_commit_push.png` - Commit and push feature-login
4. `screenshots/04_merge.png` - Pull request merged into main

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
The PR page itself cannot be created here, so the PR is represented by `git diff` plus a `--no-ff` merge commit.

## To repeat this on real GitHub (to get your own link)
```bash
git checkout -b feature-login
# add login.py
git add login.py && git commit -m "Add simple login function"
git push -u origin feature-login
# GitHub: Compare & pull request -> Merge pull request
```
