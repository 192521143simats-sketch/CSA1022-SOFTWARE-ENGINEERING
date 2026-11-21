# EXP25

**Aim:** Fork a repository, sync it with upstream, build a feature on a new branch and send a pull request.

**Tools used:** Git, GitHub (simulated locally)

## Steps performed
1. Forked and cloned
2. Added `upstream` remote
3. Teammate pushed a feature to the original
4. Fetched and merged upstream, pushed to my fork
5. Created branch `feature/modulo` and implemented it
6. Pushed to my fork and prepared the pull request

## Outcome
My fork is in sync with the original and contains the new `modulo()` branch ready for a PR.

## Screenshots
1. `screenshots/01_fork_clone.png` - Fork, clone, and add the 'upstream' remote
2. `screenshots/02_teammate.png` - Team member adds a feature to the original repo
3. `screenshots/03_sync.png` - Fetch upstream and sync my fork
4. `screenshots/04_feature.png` - Implement my feature on its own branch and push to my fork
5. `screenshots/05_pr.png` - Pull request content: fork/feature-modulo -> original/main

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
The fork, teammate and PR are simulated locally with bare repos. Real PR link must be added by you after doing it on github.com.

## To repeat this on real GitHub (to get your own link)
```bash
# Fork on github.com, then
git clone https://github.com/<you>/<repo>.git && cd <repo>
git remote add upstream https://github.com/<owner>/<repo>.git
git fetch upstream && git merge upstream/main
git checkout -b feature/modulo
git commit -am "Add modulo() feature" && git push -u origin feature/modulo
# GitHub: Compare & pull request
```
