"""개인 기준의 출처, 생성물의 독립성, 설정·기대 결과의 계약을 검사한다."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], cwd=ROOT,
                          capture_output=True, text=True)


class Workspace(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.workspace = self.folder / 'work'
        self.ok('scripts/workspace.py', 'init', self.workspace, '--name', 'team-voice')

    def ok(self, *args):
        result = run(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def propose(self):
        candidate = self.workspace / 'candidate.md'
        candidate.write_text('내일 각자 코드 한 줄을 고쳐보자.', encoding='utf-8')
        self.ok('scripts/record_rating.py', candidate, '--score', '2',
                '--reason', '내일 할 일이 바로 보인다', '--evidence', '코드 한 줄을 고쳐보자',
                '--output', self.workspace / 'ratings.jsonl')
        self.ok('scripts/workspace.py', 'propose', self.workspace, '--rating', '1',
                '--instruction', '다음에 할 일을 구체적으로 쓴다.', '--scope', '팀 작업 안내',
                '--exception', '회고와 묘사', '--question', '읽고 할 일이 보이는가?')

    def confirmed(self):
        self.propose()
        self.ok('scripts/workspace.py', 'confirm', self.workspace, '--rule', 'r001')

    def test_init_preserves_existing_data_and_rejects_reserved_name(self):
        brief = self.workspace / 'brief.md'
        brief.write_text('내 글', encoding='utf-8')
        self.assertNotEqual(run('scripts/workspace.py', 'init', self.workspace).returncode, 0)
        self.assertEqual(brief.read_text(), '내 글')
        self.assertNotEqual(run('scripts/workspace.py', 'init', self.folder / 'reserved',
                                '--name', 'my-writing-skill').returncode, 0)
        self.assertFalse((self.folder / 'reserved').exists())

    def test_unconfirmed_rule_cannot_be_exported(self):
        self.propose()
        result = run('scripts/workspace.py', 'build', self.workspace)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.workspace / 'skill').exists())
        rule = json.loads((self.workspace / 'profile.json').read_text())['rules'][0]
        self.assertEqual(rule['rating']['reason_verbatim'], '내일 할 일이 바로 보인다')
        self.assertEqual(rule['rating']['candidate_sha256'], hashlib.sha256(
            (self.workspace / 'candidate.md').read_bytes()).hexdigest())

    def test_model_score_cannot_be_used_as_author_rating(self):
        row = {'score': 2, 'source': 'model_generated', 'reason_verbatim': '좋다',
               'evidence': '문장', 'candidate_sha256': 'fake'}
        (self.workspace / 'ratings.jsonl').write_text(json.dumps(row) + '\n')
        result = run('scripts/workspace.py', 'propose', self.workspace, '--rating', '1',
                     '--instruction', '지침', '--scope', '문맥', '--question', '질문')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads((self.workspace / 'profile.json').read_text())['rules'], [])

    def test_build_only_confirmed_and_can_move_without_original_repo(self):
        self.confirmed()
        self.ok('scripts/workspace.py', 'propose', self.workspace, '--rating', '1',
                '--instruction', '미확인 지침', '--scope', '다른 문맥', '--question', '새 질문')
        self.ok('scripts/workspace.py', 'build', self.workspace)
        source = self.workspace / 'skill/team-voice'
        moved = self.folder / 'standalone'
        shutil.move(str(source), moved)
        skill = (moved / 'SKILL.md').read_text()
        self.assertNotIn('미확인 지침', skill)
        profile = json.loads((moved / 'references/author-profile.json').read_text())
        self.assertEqual([r['id'] for r in profile['rules']], ['r001'])
        metadata = json.loads((moved / 'build.json').read_text())
        self.assertEqual(metadata['human_ratings_count'], 1)
        self.assertEqual(metadata['new_passage_validation'], 'pending')
        self.assertFalse(metadata['model_fine_tuning'])
        for document in [moved / 'SKILL.md', moved / 'references/reader-review.md']:
            for target in re.findall(r'\]\(([^)]+)\)', document.read_text()):
                if not target.startswith('https://'):
                    self.assertTrue((document.parent / target).exists(), target)
        for tool in ['codex', 'claude']:
            for _ in range(2):
                self.ok(moved / 'install.py', tool, '--home', self.folder / 'home')
            config = '.codex' if tool == 'codex' else '.claude'
            self.assertEqual((self.folder / 'home' / config / 'skills/team-voice').resolve(), moved.resolve())
        output = self.folder / 'signals.json'
        self.ok(moved / 'scripts/analyze.py', self.workspace / 'candidate.md',
                '--config', moved / 'checks.json', '--output', output)
        self.assertEqual(json.loads(output.read_text())['custom_checks'], {'watch': [], 'preserve': []})

    def test_existing_output_is_never_overwritten(self):
        self.confirmed()
        self.ok('scripts/workspace.py', 'build', self.workspace)
        target = self.workspace / 'skill/team-voice/SKILL.md'
        before = target.read_bytes()
        self.assertNotEqual(run('scripts/workspace.py', 'build', self.workspace).returncode, 0)
        self.assertEqual(target.read_bytes(), before)

    def test_eval_case_uses_exact_spans_and_preserves_input(self):
        original = '매듭을 지었다. 그래서 다음 주에 시작한다.'
        source = self.workspace / 'input.md'
        source.write_text(original, encoding='utf-8')
        self.ok('scripts/workspace.py', 'eval-case', self.workspace, '--input', source,
                '--name', 'first', '--fix', '매듭을 지었다', '--preserve', '그래서')
        case = self.workspace / 'eval/cases/first'
        self.assertEqual((case / 'input.md').read_text(), original)
        expected = json.loads((case / 'expected.json').read_text())
        self.assertEqual(expected['planted'][0]['match'], '매듭을 지었다')
        self.assertEqual(expected['traps'][0]['match'], '그래서')
        for fix, preserve in [('없는 표현', '그래서'), ('매듭', '매듭을 지었다')]:
            result = run('scripts/workspace.py', 'eval-case', self.workspace, '--input', source,
                         '--name', 'invalid', '--fix', fix, '--preserve', preserve)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.workspace / 'eval/cases/invalid').exists())

    def test_custom_checks_replace_defaults_and_keep_preserve_signal(self):
        source = self.workspace / 'input.md'
        source.write_text('리듬이 있다. 매우 좋다. 그래서 다시 한다.', encoding='utf-8')
        config = self.workspace / 'checks.json'
        output = self.folder / 'report.json'
        config.write_text(json.dumps({'watch': ['매우'], 'preserve': ['그래서']}))
        self.ok('scripts/analyze.py', source, '--config', config, '--output', output)
        rows = json.loads(output.read_text())['sentences']
        self.assertEqual(rows[0]['expression_candidates'], [])
        self.assertEqual(rows[1]['expression_candidates'], ['매우'])
        self.assertEqual(rows[2]['preserve_candidates'], ['그래서'])
        config.write_text(json.dumps({'watch': []}))
        self.ok('scripts/analyze.py', source, '--config', config, '--output', output)
        self.assertEqual(json.loads(output.read_text())['summary']['expression_candidates'], 0)

    def test_invalid_checks_fail_before_creating_skill(self):
        self.confirmed()
        (self.workspace / 'checks.json').write_text('{"watch": "매우"}')
        self.assertNotEqual(run('scripts/workspace.py', 'build', self.workspace).returncode, 0)
        self.assertFalse((self.workspace / 'skill').exists())


if __name__ == '__main__':
    unittest.main()
