# Western Australia law, change by change

Every Western Australian Act with a consolidated version on the WA Legislation website, 1286 Acts
(811 in force and 475 repealed), and
1538 instruments of subsidiary legislation (765 in force and 773 ceased: regulations, rules, by-laws, codes, orders and others),
as a git repository, version by version. Each change is one commit, credited to the law that made it and dated the day it took effect, at noon in Perth. The text is the
Parliamentary Counsel's Office's consolidation of each law (each version's HTML), from
[WA Legislation](https://www.legislation.wa.gov.au).

## The questions, as git commands

| Question | Command |
| --- | --- |
| What did section 71 of the Constitution Act 1889 say on 10 September 2010? | `python tools/in_force_on.py 2010-09-10 constitution-act-1889 71` |
| The whole Act as it stood that day | `python tools/in_force_on.py 2010-09-10 constitution-act-1889` |
| The commit that holds that day's text, and why it was made | `python tools/in_force_on.py 2010-09-10 constitution-act-1889 --commit` |
| Which law wrote each line of a section? | `git blame constitution-act-1889/s-071.md` |
| Every change to a section, with the law and the day | `git log --format="%(trailers:key=In-force,valueonly,separator=) %an" -- constitution-act-1889/s-071.md` |
| The words that changed, not just the lines | `git log -p --word-diff -1 -- constitution-act-1889/s-071.md` |
| Everything one amending law changed | `git log --author="No. 19 of 2010" --stat --format="%s"` |
| Changes no single law explains | `git log --grep="^Kind: .*(not credited)" --format="%s"` |
| What did regulation 27 of the Liquor Control Regulations 1989 say on 30 June 2026? | `python tools/in_force_on.py 2026-06-30 subsidiary/liquor-control-regulations-1989 27` |
| Which law wrote each line of it? | `git blame subsidiary/liquor-control-regulations-1989/r-027.md` |
| The Acts' history alone, without the instruments | `git log --format="%s" -- . ":!subsidiary"` |
| Every change with its law and day | [`changes.csv`](changes.csv) |

## The dates

**Commits are dated the day the change took effect**, at noon in Perth: AWST (UTC+8), or UTC+9 during the
daylight-saving trials of 1974-75, 1983-84, 1991-92 and 2006-09 (hard-coded). The day is the currency start of the
consolidated version the change first appears in, which is the day the amending law's provisions commenced. Every
law commit carries `In-force: YYYY-MM-DD`; the amending Act's assent day, where its Compilation table row gives one,
is in `Assented:`. Git cannot store a date before 1970: such commits are dated 1 January 1970 (one second apart, in
order) and the real day is in `In-force:`. To ask what the law was on a day, use `tools/in_force_on.py`, which reads
the trailer, not the git date. No version on the website takes effect after 2026-10-29, so there is no `future` branch.

The record of each Act and instrument starts at its first consolidated version on the website (for most Acts in
2003-2006, when the website's consolidations begin). That first commit already holds every earlier amendment; they
are not replayed. The earliest version is from 1886-09-02, the latest from 2026-10-29.

## How it is checked

- Every version, read back from git on its first day with `tools/in_force_on.py`, must be the files the parser
  makes from that version's HTML, byte for byte; and the letters and digits of all its files, in the order of the
  source, must be those of the version's raw HTML read by an independent extractor (every text node, except the
  cover page, the table of contents and note-reference numbers). The last check (2026-10-29) read back every one of 23225 versions from git on its first day and compared it with the source: 0 file mismatches, and 0 versions whose letters and digits differ from the raw HTML (2,029,677,321 words checked).
- `scripts/global-law/check_corpus.py`, `test_corpus.py` and `test_noon.py` (Lexifina's shared checks) and
  `tools/test_repo.py` (the commands in this README) pass; a rebuild from the same data gives the same hashes.

## What "author" means

The author of a commit is the law that made the change, with an address ending `@legislation.wa.invalid` that cannot
exist, so `git blame` names it: `Aboriginal Cultural Heritage Act 2021 (No. 27 of 2021)`. Subsidiary legislation
is named by its SL number (`SL 2023/192`, from 2021) or, before that, by the Gazette page it was published on
(`Gazette 11 Dec 1998 p. 6597`), as its Compilation table gives it. A version is compared with the one before it,
provision by provision, and each changed provision is credited:

- to the one law that the version's own Compilation table says commenced on the version's first day and that the
  provision's amendment note cites (`[Section 2 amended: No. 59 of 1978 s. 4.]`; in an instrument a Gazette page
  inside the law's page range counts, `[Regulation 5 amended: Gazette 11 Dec 1998 p. 6604.]`); else
- to the one law in that table commencing that day, when only one does.

A repeal is credited to the law that the last version names ("This Act was repealed by ... on 1 Jul 2023"),
when that day is the version's first day; a repealing instrument that no Compilation table numbers (it is spent at
once) is named by the title the note gives, with no number. Anything else is labelled and committed by
`Parliamentary Counsel's Office, Western Australia`, never guessed, with a `Kind:` trailer ending "(not credited)":
the first consolidated version of each Act or instrument, two or more candidate laws (`Candidate:` trailers), a law listed with
another commencement day, a reprint, changes of style only (case, punctuation, spacing), changes to amendment notes
only, changes no law explains, changes to the notes only, repeals whose law is not identified, and Acts that expired under their own terms. 7,821 of
21,643 law commits are credited to a law (7,019 laws).

## Files

One folder per Act (`constitution-act-1889/`), one file per section (`s-073.md`), schedule heading
(`sch-1/heading.md`) and schedule clause (`sch-1/cl-002.md`), plus `intro.md` (title, long title, preamble) and
`notes.md` (the Compilation table and other notes). An Act printed inside another (the Criminal Code in the Criminal
Code Act Compilation Act 1913) has its own folder inside it. Part and Division headings sit at the top of the next
section's file. One paragraph per line; table rows are one line, cells separated by ` | `; headings are marked `##`
and `###`. A repealed Act has no folder after the day it ceased.

Subsidiary legislation is under `subsidiary/`, one folder per instrument
(`subsidiary/liquor-control-regulations-1989/`), laid out like the Acts: one file per numbered provision,
named for what the instrument calls it: a regulation or rule `r-005.md`, a by-law `bl-005.md`, a clause of a code,
order, notice or other instrument `cl-005.md`; schedules, `intro.md` and `notes.md` as for an Act. Its commits are
separate from the Acts' commits (an amending law that changes Acts and instruments on one day has one commit for
each), so the Acts' history reads the same with or without them: `git log -- . ':!subsidiary'`.

## What it does not show

- Amendments made before an Act's first consolidated version on the website (they are inside that first text).
- Local laws (published by local governments in the Government Gazette, not on the website), Acts as passed,
  subsidiary legislation as made, and Bills.
- Note-reference numbers, page layout, images and the table of contents.
- Versions published on the same day: only the last of them is kept.
- 191 Acts whose only consolidated version on the website is the one published when
  they were repealed (so no day in force is on record); they are left out, and 4
  instruments likewise.

## How it is built

From the retrieved version texts by deterministic Python (`git fast-import`); see [REPRODUCE.md](REPRODUCE.md). This record
is not an official version.

## Licence

Based on content from the Western Australian Legislation website at 28 October 2026 to 29 October 2026. For the latest information on Western Australian legislation, visit www.legislation.wa.gov.au. The legislation is Copyright State of Western Australia, licensed under CC BY 4.0
([LICENSE](LICENSE), [SOURCES.md](SOURCES.md)). The files are adapted from it: split into one file per provision,
with note-reference numbers, the cover page and the table of contents removed.
