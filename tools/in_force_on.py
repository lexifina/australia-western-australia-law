"""What did a Western Australian Act say on a day?

    python tools/in_force_on.py 2010-01-01 constitution-act-1889            # the whole Act
    python tools/in_force_on.py 2010-01-01 constitution-act-1889 73         # section 73
    python tools/in_force_on.py 2010-01-01 constitution-act-1889 sch-1/cl-2 # a schedule clause (or any file name)
    python tools/in_force_on.py 2010-01-01 constitution-act-1889 --commit   # the commit and why it was made
    python tools/in_force_on.py 2010-01-01 subsidiary/<instrument> 5        # regulation, rule, by-law or clause 5

Reads the In-force trailers on main (main is in in-force order), so a commit counts from the day it took effect, not
from its git date. The record of each Act and instrument starts at its first consolidated version on the WA
Legislation website. An instrument's provisions are r-NNN.md (regulation or rule), bl-NNN.md (by-law) or cl-NNN.md
(clause); a bare number finds whichever the instrument has.
"""
import re
import subprocess
import sys


def git(*a):
    return subprocess.run(['git', *a], capture_output=True, encoding='utf-8', errors='replace').stdout


def key_of(p):
    """'73' -> s-073.md; '10A' -> s-010A.md; 'sch-1/cl-2' -> sch-1/cl-002.md; 'criminal-code/279' ->
    criminal-code/s-279.md; anything else is taken as a file name."""
    p = p.strip().removesuffix('.md')
    head, _, last = p.rpartition('/')
    m = re.fullmatch(r'(s-|cl-|r-|bl-)?(\d+)([A-Za-z]*)', last)
    if m:
        kind = m.group(1) or ('cl-' if head.startswith('sch') and '/' not in head else 's-')
        last = '%s%s%s' % (kind, m.group(2).zfill(3), m.group(3).upper())
    return (head + '/' if head else '') + last + '.md'


def commit_on(day, act):
    """The last commit on main touching the Act's folder that took effect on or before day, or None."""
    log = git('log', 'main', '--format=%H%x1f%(trailers:key=In-force,valueonly,separator=)', '--', act + '/')
    for line in log.splitlines():
        h, _, when = line.partition('\x1f')
        if when.strip() and when.strip() <= day:
            return h
    return None


def order(f):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', f)]


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    args = [a for a in sys.argv[1:] if a != '--commit']
    if len(args) < 2:
        print(__doc__)
        sys.exit(2)
    day, act = args[0], args[1].strip('/')
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', day):
        sys.exit('day must be YYYY-MM-DD')
    sha = commit_on(day, act)
    if not sha:
        sys.exit('%s: no version in force on %s in this record' % (act, day))
    if '--commit' in sys.argv:
        print(git('log', '-1', '--format=%H%n%an%n%n%B', sha))
        return
    files = [f for f in git('ls-tree', '-r', '--name-only', sha, '--', act + '/').splitlines() if f.endswith('.md')]
    if not files:
        sys.exit('%s: not in force on %s (repealed; see python tools/in_force_on.py %s %s --commit)'
                 % (act, day, day, act))
    if len(args) > 2:
        path = '%s/%s' % (act, key_of(args[2]))
        if path not in files and re.fullmatch(r'[0-9]+[A-Za-z]*', args[2].strip()):
            # an instrument numbers its provisions r-, bl- or cl-: take the one it has
            alt = [path.replace('/s-', '/' + k, 1) for k in ('r-', 'bl-', 'cl-')]
            path = next((q for q in alt if q in files), path)
        if path not in files:
            sys.exit('%s: not in force on %s (no such provision in that version)' % (path, day))
        sys.stdout.write(git('show', '%s:%s' % (sha, path)))
        return
    for f in sorted(files, key=order):
        sys.stdout.write('==> %s\n' % f + git('show', '%s:%s' % (sha, f)) + '\n')


if __name__ == '__main__':
    main()
