# EXP9

**Aim:** Work collaboratively with the fork-and-pull-request workflow.

**Tools used:** Git, GitHub (simulated locally with bare repositories), Python unittest

## Steps performed
1. Forked the upstream calculator repo
2. Cloned the fork and added `upstream` remote
3. Created branch `feature/power-function`
4. Added `power()` + unit test, all tests passed
5. Committed and pushed the branch
6. Viewed the PR diff (feature -> main)
7. Reviewer feedback recorded in `PR_REVIEW.md`
8. Addressed feedback with a second commit
9. Merged the approved PR into `main` and re-ran the tests
10. Wrote `PULL_REQUEST_SUMMARY.md`

## Outcome
The feature branch was developed, reviewed, fixed and merged. `main` now contains `power()` and 5 passing tests.

## Screenshots
1. `screenshots/01_fork.png` - Fork the repository (my copy: R-SARVESH-calculator-fork)
2. `screenshots/02_clone.png` - Clone the fork and add the original as 'upstream'
3. `screenshots/03_branch.png` - Create feature branch
4. `screenshots/04_modify_and_test.png` - Add power() function - all tests pass
5. `screenshots/05_commit_push.png` - Commit and push the feature branch
6. `screenshots/06_pull_request_diff_part1.png` - Pull request: feature/power-function into main
7. `screenshots/06_pull_request_diff_part2.png` - Pull request: feature/power-function into main
8. `screenshots/07_address_feedback.png` - Respond to review feedback with another commit
9. `screenshots/08_merge.png` - Approved PR merged into main

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
The fork, pull request and review were **simulated on this computer** using local bare repositories that act like GitHub. Every git command output in the screenshots is real, but there is no real GitHub PR page, so the PR link in `PULL_REQUEST_SUMMARY.md` is a placeholder for you to fill in after doing the same on github.com.

## To repeat this on real GitHub (to get your own link)
```bash
# 1. Click "Fork" on the original repo in GitHub, then:
git clone https://github.com/<your-username>/<repo>.git && cd <repo>
git remote add upstream https://github.com/<owner>/<repo>.git
git checkout -b feature/power-function
# edit files, then
git add . && git commit -m "Add power function with unit test"
git push -u origin feature/power-function
# 2. On GitHub press "Compare & pull request", get it reviewed, then "Merge pull request"
```
