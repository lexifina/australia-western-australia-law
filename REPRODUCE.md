# How this repository was made

Built by `scripts/australia-western-australia-law/` in the Lexifina repository (not public), by an AI coding
agent: Claude Opus 5.5 (claude-opus-5-5), run as a Claude Code agent. No model writes or edits legal text, and no model runs at build time; the build is deterministic
Python (standard library) and `git fast-import`.

## Steps

From the retrieved files (the lists, each law's versions page and each version's HTML, retrieved 28 October 2026 to 29 October 2026):

```
python -X utf8 build.py --repo <folder> --today 2026-10-29
python -X utf8 check_repo.py --repo <folder> --today 2026-10-29     # byte check + independent letters-and-digits check
python -X utf8 <folder>/tools/test_repo.py --repo <folder>       # README commands, blame, on-date tool
```

## Counts

- Acts: 1286 (811 in force, 475 repealed); Acts listed only as repealed, with no earlier
  version: 191 (not built).
- Consolidated versions used: 11218; versions missing from the retrieved files: 0.
- Commits on main: 21643 law + 1 documentation. Acts' repeals: 450 credited,
  25 not credited.
- Commits by kind (`act` and `enacted` are credited to a law):
- act: 6803
- annotation: 2435
- baseline: 1806
- candidates: 237
- ceased: 205
- enacted: 1018
- late: 86
- notes: 5091
- reprint: 1374
- style: 1825
- unexplained: 763
- Subsidiary legislation: 1538 instruments (765 in force, 773 ceased) of 1542
  listed; listed only as repealed, with no earlier version: 4 (not built). Versions used:
  12007. Commits: 12245 (included in the law commits above). Repeals: 593
  credited, 180 not credited.
- Provision changes recorded: 359993 (changes.csv).

## Determinism

The commit stream is written with `git fast-import` from sorted inputs; author and committer dates are the in-force
day at noon in Perth; the documentation commit is dated the last download day. Two builds from the same retrieved files
give the same `main` hash.
