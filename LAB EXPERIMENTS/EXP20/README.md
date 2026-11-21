# EXP20

**Aim:** Create a repo, clone it, edit README.md and push the change.

**Tools used:** Git, GitHub (simulated locally)

## Steps performed
1. Created repo with README.md
2. Cloned it
3. Added a project description
4. Staged, committed and pushed

## Outcome
Remote `main` now has 2 commits and the updated README.

## Screenshots
1. `screenshots/01_create_repo.png` - Create the repository with an initial README.md
2. `screenshots/02_clone.png` - Clone the repository
3. `screenshots/03_edit.png` - Edit README.md
4. `screenshots/04_commit_push.png` - Stage, commit and push to GitHub

Full command output is saved in `terminal_transcript.txt`.

## Honest note (what was real and what was simulated)
The 'GitHub' remote is a local bare repository; commands are identical for real GitHub.

## To repeat this on real GitHub (to get your own link)
```bash
# create an empty repo on github.com (tick "Add a README"), then:
git clone https://github.com/<you>/my-personal-project.git && cd my-personal-project
# edit README.md
git add README.md && git commit -m "Add project description to README" && git push origin main
```
