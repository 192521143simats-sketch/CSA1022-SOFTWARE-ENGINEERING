# Merge Conflict Summary - EXP10

## Steps performed
1. Cloned the shared repository.
2. Created `feature/readme-update` and changed the *Status* line of `README.md`.
3. Committed and pushed it.
4. A teammate changed the **same line** on `main` and pushed first.
5. Pulled the latest `main`, switched back to my branch and ran `git merge main`.

## Conflict encountered
Git stopped with `CONFLICT (content): Merge conflict in README.md` because both of us edited the
same line. Git cannot choose between two edits of one line, so it inserted markers
(`<<<<<<<`, `=======`, `>>>>>>>`).

## How I resolved it
- Opened `README.md`, read both versions.
- Wrote one final line that keeps the teammate's information and my addition.
- Deleted the three marker lines.
- `git add README.md` (marks the conflict resolved) and `git commit` to finish the merge.
- Pushed the branch and it is ready for a pull request.
