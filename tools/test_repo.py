"""Functional test of the Western Australia law repository: the things a reader does with it work. Standard library.

    python -X utf8 tools/test_repo.py [--repo .] [--record <verification.json>]

It asserts that:
1. `git blame` on an amended section names an amending law as author of its lines;
2. tools/in_force_on.py gives the text before and after an amendment, each equal to the file at that commit;
3. `git log` on a file lists its changes in the order they took effect;
4. every law commit has an ISO `In-force:` trailer, the documentation commit has none, main is in in-force order and
   no day is after the build day;
5. only the documentation commit (the last) is authored by Lexifina; Lexifina commits every commit; no merges;
   no carriage returns in any message;
6. a repealed Act has no files after its repeal, and the tool says so;
7. every git or tool command in the README's table runs and prints something.
"""
import argparse
import csv
import datetime as dt
import io
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

PUBLISHER = "Parliamentary Counsel's Office, Western Australia"
# a law by its number; or (an instrument's repealing law that no table numbers) by its title alone
LAW = re.compile(r'\((No\. \d+ of \d{4}|SL \d{4}/\d+|Gazette \d{1,2} [A-Z][a-z]{2} \d{4}( p\. \d+)?|\d+ \w+.*No\. ?\d+)\)$'
                 r'|\b(Act|Regulations|Rules|By-laws|Code|Order|Notice|Determination|Scheme|Standard)\b.* (1[6-9]|20)\d\d$')


class Smoke:
    def __init__(self, repo):
        self.repo = repo
        self.results = []
        self.corpus = json.loads(self.git('show', 'main:corpus.json'))
        self.rows = list(csv.reader(io.StringIO(self.git('show', 'main:changes.csv'))))[1:]

    def git(self, *args):
        out = subprocess.run(['git', *args], cwd=self.repo, capture_output=True, encoding='utf-8', errors='replace')
        if out.returncode:
            raise AssertionError('git %s: %s' % (' '.join(args), out.stderr.strip()))
        return out.stdout

    def tool(self, *args, ok=True):
        out = subprocess.run([sys.executable, '-X', 'utf8', 'tools/in_force_on.py', *args], cwd=self.repo,
                             capture_output=True, encoding='utf-8', errors='replace')
        if ok and out.returncode:
            raise AssertionError('in_force_on %s: %s' % (' '.join(args), out.stderr.strip()))
        return out

    def check(self, name, fn):
        try:
            detail = fn() or ''
            self.results.append((name, True, detail))
            print('PASS %s: %s' % (name, detail))
        except AssertionError as exc:
            self.results.append((name, False, str(exc)))
            print('FAIL %s: %s' % (name, exc))

    def amended(self, n=3):
        """Sections with at least two changes credited to a law, most-changed first."""
        cnt = {}
        for day, act, f, kind, author in self.rows:
            if kind == 'act' and re.match(r'^s-\d', f):
                cnt[(act, f)] = cnt.get((act, f), 0) + 1
        best = sorted((k for k, v in cnt.items() if v >= 2), key=lambda k: (-cnt[k], k))
        pref = [k for k in best if k[0] == 'constitution-act-1889']
        return (pref + [k for k in best if k not in pref])[:n]

    def blame(self):
        live = set(self.git('ls-tree', '-r', '--name-only', 'main').splitlines())
        tried = []
        for act, f in self.amended(40):
            path = '%s/%s' % (act, f)
            if path not in live:
                continue
            out = self.git('blame', '--line-porcelain', 'main', '--', path)
            authors = {l[7:] for l in out.splitlines() if l.startswith('author ')}
            assert all(LAW.search(a) or a == PUBLISHER for a in authors), 'unexpected authors %s' % sorted(authors)
            if any(LAW.search(a) for a in authors):
                return '%s lines by %s' % (path, '; '.join(sorted(authors)))
            tried.append(path)
        raise AssertionError('no law among the line authors of %s' % tried[:5])

    def on_date(self):
        done = []
        for act, f in self.amended(3):
            path = '%s/%s' % (act, f)
            shas = self.git('log', '--format=%H', 'main', '--', path).split()
            days = [re.search(r'^In-force: (\S+)', self.git('log', '-1', '--format=%B', h), re.M).group(1)
                    for h in shas[:2]]
            after, prev = days[0], days[1]
            before = (dt.date.fromisoformat(after) - dt.timedelta(days=1)).isoformat()
            prov = re.sub(r'^s-0*', '', f[:-3])
            a, b = self.tool(before, act, prov).stdout, self.tool(after, act, prov).stdout
            assert a != b, '%s: same text on %s and %s' % (path, before, after)
            assert b == self.git('show', '%s:%s' % (shas[0], path)), '%s on %s is not the file at %s' % (
                path, after, shas[0][:7])
            if prev < after:
                assert a == self.git('show', '%s~1:%s' % (shas[0], path)), '%s on %s is not the file before' % (
                    path, before)
            whole = self.tool(after, act).stdout
            assert b in whole, '%s: whole Act on %s lacks the section' % (path, after)
            done.append('%s %s != %s' % (path, before, after))
        return '; '.join(done)

    def follow(self):
        checked = []
        for act, f in self.amended(3):
            out = self.git('log', '--format=%an%x09%(trailers:key=In-force,valueonly,separator=)', 'main', '--',
                           '%s/%s' % (act, f))
            rows = [l.split('\t') for l in out.splitlines() if l]
            days = [d.strip() for _, d in rows]
            assert days == sorted(days, reverse=True), '%s: not in date order %s' % (f, days)
            assert sum(1 for a, _ in rows if LAW.search(a)) >= 2, '%s: fewer than two laws' % f
            checked.append('%s/%s %d commits' % (act, f, len(rows)))
        return '; '.join(checked)

    def trailers(self):
        rows = self.git('log', '--reverse', '--format=%H%x09%an%x09%(trailers:key=In-force,valueonly,separator=)',
                        'main').splitlines()
        law = rows[:-1]
        assert not rows[-1].split('\t')[2].strip(), 'documentation commit carries In-force'
        bad = [r for r in law if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', r.split('\t')[2].strip())]
        assert not bad, '%d law commits without an ISO In-force, e.g. %s' % (len(bad), bad[:2])
        days = [r.split('\t')[2].strip() for r in law]
        back = [i for i in range(1, len(days)) if days[i] < days[i - 1]]
        assert not back, 'in-force order goes backwards at %s' % [law[i][:10] for i in back[:3]]
        built = self.corpus['built']
        assert days[-1] <= built, 'last In-force %s after the build day %s' % (days[-1], built)
        return '%d law commits, In-force %s to %s, in order' % (len(law), days[0], days[-1])

    def lexifina(self):
        rows = self.git('log', '--format=%H%x09%an%x09%cn%x09%P', 'main').splitlines()
        by_lex = [r for r in rows if r.split('\t')[1] == 'Lexifina']
        assert len(by_lex) == 1 and by_lex[0] == rows[0], '%d commits by Lexifina' % len(by_lex)
        assert all(r.split('\t')[2] == 'Lexifina' for r in rows), 'a committer other than Lexifina'
        merges = [r for r in rows if len(r.split('\t')[3].split()) > 1]
        assert not merges, '%d merge commits' % len(merges)
        raw = subprocess.run(['git', 'log', '--format=%B%x00', 'main'], cwd=self.repo, capture_output=True).stdout
        assert b'\r' not in raw, 'a carriage return in a commit message'
        authors = {r.split('\t')[1] for r in rows[1:]}
        # a law named by title alone (an instrument's repealing law) has a law-<title>@ address
        titled = {l.split('\t')[0] for l in self.git('log', '--format=%an%x09%ae', 'main').splitlines()
                  if l.split('\t')[1].startswith('law-') and l.split('\t')[1].endswith('@legislation.wa.invalid')}
        odd = {a for a in authors if not LAW.search(a) and a != PUBLISHER and a not in titled}
        assert not odd, 'unexpected authors %s' % sorted(odd)[:5]
        return 'only %s is by Lexifina; %d authors; 0 merges; 0 CRs' % (rows[0][:10], len(authors))

    def repealed(self):
        rows = [r for r in self.rows if r[3] in ('repeal', 'ceased')]
        assert rows, 'no repeal recorded'
        day, act = rows[-1][0], rows[-1][1]
        assert not self.git('ls-tree', 'main', '--', act + '/').strip(), '%s still has files on main' % act
        out = self.tool(day, act, ok=False)
        assert out.returncode and 'not in force' in out.stderr, '%s on %s: %r' % (act, day, out.stderr[:200])
        before = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
        assert self.tool(before, act).stdout.strip(), '%s on %s: no text' % (act, before)
        return '%s: text on %s, none from %s' % (act, before, day)

    def readme(self):
        text = (self.repo / 'README.md').read_text(encoding='utf-8')
        table = text[text.index('## The questions'):text.index('## The dates')]
        cmds = [c for c in re.findall(r'`([^`]+)`', table) if c.startswith(('git ', 'python '))]
        assert len(cmds) >= 8, 'only %d commands found' % len(cmds)
        for c in cmds:
            args = shlex.split(c)
            if args[0] == 'python':
                args[0] = sys.executable
            out = subprocess.run(args, cwd=self.repo, capture_output=True, encoding='utf-8', errors='replace')
            assert out.returncode == 0, '%s: exit %d %s' % (c, out.returncode, out.stderr.strip()[:200])
            assert out.stdout.strip(), '%s: printed nothing' % c
        return '%d README commands ran and printed output' % len(cmds)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument('--record')
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    s = Smoke(Path(args.repo))
    s.check('blame names a law', s.blame)
    s.check('text before and after an amendment', s.on_date)
    s.check('log in date order', s.follow)
    s.check('In-force on every law commit, in order', s.trailers)
    s.check('only the documentation commit is by Lexifina', s.lexifina)
    s.check('a repealed Act has no text after its repeal', s.repealed)
    s.check('README commands run', s.readme)
    ok = all(r[1] for r in s.results)
    print('%d/%d passed' % (sum(r[1] for r in s.results), len(s.results)))
    if args.record:
        p = Path(args.record)
        rec = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
        rec['smoke'] = {'passed': sum(r[1] for r in s.results), 'total': len(s.results),
                        'results': [{'test': n, 'ok': o, 'detail': d} for n, o, d in s.results]}
        p.write_text(json.dumps(rec, indent=1, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8',
                     newline='\n')
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
