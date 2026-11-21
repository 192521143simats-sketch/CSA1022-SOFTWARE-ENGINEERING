# EXP21

**Aim:** Clone an existing repository and make a small change to a file.

**Tools used:** Git

## Steps performed
1. Cloned the repository
2. Entered the directory and opened README.md
3. Edited one line and saved
4. Verified with `git status` and `git diff`

## Outcome
The working tree shows `README.md` modified (change not yet committed - that is EXP22).

## Screenshots
1. `screenshots/01_clone.png` - Clone the repository with git clone <repository_url>
2. `screenshots/02_open.png` - Navigate into the folder and open README.md
3. `screenshots/03_edit.png` - Small edit saved - git shows the change

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
Cloned from a local bare repo; identical to cloning from GitHub.

## To repeat this on real GitHub (to get your own link)
```bash
git clone https://github.com/<owner>/<repo>.git
cd <repo>
# edit a file and save
git status
git diff
```
