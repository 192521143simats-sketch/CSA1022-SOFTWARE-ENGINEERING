# EXP23

**Aim:** Pull collaborator changes to keep the local copy up to date.

**Tools used:** Git

## Steps performed
1. Cloned the repo
2. Collaborator pushed `square()`
3. Used `git fetch`/`git status` to see I was behind
4. Ran `git pull origin main`
5. Verified the new commit and function

## Outcome
My local repo now contains `square()` from the collaborator.

## Screenshots
1. `screenshots/01_clone.png` - Clone the repository
2. `screenshots/02_collaborator.png` - Collaborator pushes a new commit
3. `screenshots/03_behind.png` - My local copy is behind origin/main
4. `screenshots/04_pull.png` - git pull origin main
5. `screenshots/05_verify.png` - Collaborator's change appears locally

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
The collaborator is simulated by a second local clone. For a real run ask a friend to push a change.

## To repeat this on real GitHub (to get your own link)
```bash
git pull origin main
git log --oneline
```
