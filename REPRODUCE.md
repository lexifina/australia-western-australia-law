# How this repository was made

Built by `scripts/australia-western-australia-law/` in the Lexifina repository (not public), by an AI coding
agent: Claude Opus 5.5 (claude-opus-5-5), run as a Claude Code agent. No model writes or edits legal text, and no model runs at build time; the build is deterministic
Python (standard library) and `git fast-import`.

## Steps

```
python fetch.py lists        # 26 requests: every Act, in force and ceased
python fetch.py versions     # 1 request per Act: its consolidated versions
python fetch.py texts        # 1 request per version: the version's HTML
python -X utf8 build.py --repo <folder> --today 2026-10-29
python -X utf8 check_repo.py --repo <folder> --today 2026-10-29     # byte check + independent letters-and-digits check
python -X utf8 <folder>/tools/test_repo.py --repo <folder>       # README commands, blame, on-date tool
```

## Fetch rate

One process, at most 4 parallel requests to www.legislation.wa.gov.au (robots.txt: none, so no Crawl-delay),
gzip (`curl --compressed`), about 40 versions a minute. Every answer is cached, errors too (as negative answers), so a
rebuild makes no requests. Data downloaded 28 October 2026 to 29 October 2026.

## Counts

- Acts: 1286 (811 in force, 475 repealed); Acts listed only as repealed, with no earlier
  version: 191 (not built).
- Consolidated versions used: 11218; versions not fetched: 0.
- Commits on main: 9398 law + 1 documentation. Repeals: 450 credited,
  25 not credited.
- Commits by kind (`act` and `enacted` are credited to a law):
- act: 1067
- annotation: 1432
- baseline: 979
- candidates: 77
- ceased: 25
- enacted: 307
- late: 41
- notes: 3286
- reprint: 746
- style: 985
- unexplained: 453
- Provision changes recorded: 190796 (changes.csv).

## Determinism

The commit stream is written with `git fast-import` from sorted inputs; author and committer dates are the in-force
day at noon in Perth; the documentation commit is dated the last download day. Two builds from the same cache give
the same `main` hash.
