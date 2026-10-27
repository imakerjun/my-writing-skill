"""생성물의 독립성, 평가 맥락, 캐시·프로필 계약을 검사한다. 점수와 인물은 테스트 입력이다."""
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
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze
import expression_preferences as expressions
import personas
import suite


class Creator(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.work = self.root / 'work'

    def test_three_starters_can_move_and_install_without_the_creator(self):
        suite.initialize(self.work, 'my-writing')
        built = suite.build(self.work)
        moved = self.root / 'moved'
        shutil.move(built, moved)
        for target in ('codex', 'claude'):
            result = subprocess.run([sys.executable, str(moved / 'install.py'), target, '--home', str(self.root / 'home')], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            tool_folder = '.codex' if target == 'codex' else '.claude'
            installed = self.root / 'home' / tool_folder / 'skills'
            self.assertEqual(len(list(installed.iterdir())), 3)
            for mode in suite.MODES:
                self.assertEqual((installed / ('my-writing-' + mode)).resolve(), (moved / ('my-writing-' + mode)).resolve())
        for path in moved.rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if '://' not in link and not link.startswith('#'):
                    self.assertTrue((path.parent / link.split('#')[0]).exists(), (path, link))
        # The expression helper remains runnable after relocation, with the generated config.
        expression = moved / 'my-writing-expressions'
        new_work = self.root / 'independent-expression'
        result = subprocess.run([sys.executable, str(expression / 'scripts/expression_preferences.py'), 'init', str(new_work), '--base-config', str(expression / 'checks.json')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('여정', json.loads((new_work / 'checks.json').read_text())['watch'])

    def test_existing_inputs_and_outputs_are_preserved_and_invalid_settings_do_not_publish(self):
        suite.initialize(self.work, 'my-writing')
        with self.assertRaises(ValueError):
            suite.initialize(self.work, 'other')
        built = suite.build(self.work)
        sentinel = built / 'keep.txt'; sentinel.write_text('keep')
        with self.assertRaises(ValueError):
            suite.build(self.work)
        self.assertEqual(sentinel.read_text(), 'keep')
        (self.work / 'expressions/checks.json').write_text('{"watch": "not a list"}')
        output = self.root / 'invalid'
        with self.assertRaises(ValueError):
            suite.build(self.work, output)
        self.assertFalse(output.exists())

    def test_example_scores_keep_context_and_pending_is_not_a_bad_word(self):
        work = self.root / 'expressions'
        expressions.initialize(work)
        candidate = self.root / 'candidate.md'
        candidate.write_text('회고는 성장을 확인하는 자리다. 의자는 제자리에 놓는다.')
        expressions.record(work, candidate, '자리', 0, '설명만 추상적이다', '성장을 확인하는 자리', '회고 소개')
        expressions.record(work, candidate, '자리', 2, '실제 위치다', '제자리에 놓는다', '회의실 안내')
        expressions.record(work, candidate, '성장', 1, '판단을 미룬다', '성장을 확인', '회고 소개')
        checks = json.loads((work / 'checks.json').read_text())
        self.assertIn('자리', checks['watch']); self.assertIn('자리', checks['preserve'])
        self.assertNotIn('성장', checks['watch'])
        self.assertEqual(len(checks['calibrations']), 3)
        before = (work / 'ratings.jsonl').read_bytes()
        with self.assertRaises(ValueError):
            expressions.record(work, candidate, '여정', 0, '싫다', '없는 구절', '소개')
        self.assertEqual((work / 'ratings.jsonl').read_bytes(), before)
        report = analyze.analyze('자리 자리. 제자리.', checks)
        self.assertEqual(report['expression_occurrences'], 3)
        self.assertEqual(report['sentences'][0]['expression_occurrences'][0]['offsets'], [0, 3])

    def test_selected_readers_require_provenance_and_profiles_cannot_silently_change(self):
        profile = {field: 'test fixture' for field in personas.FIELDS}
        profile.update(uuid='a' * 32, age=30)
        reader = {'row_id': profile['uuid'], 'profile': profile,
                  'profile_sha256': hashlib.sha256(json.dumps(profile, ensure_ascii=False, sort_keys=True).encode()).hexdigest()}
        data = {'source_kind': 'synthetic_persona_dataset', 'dataset': personas.DATASET,
                'dataset_revision': 'fixture', 'used_fields': personas.FIELDS, 'readers': [reader]}
        selected = personas.select(data, ['a' * 32])
        prompt = personas.prompt(selected, 'a' * 32, '원고에 실제로 있는 문장입니다.')
        self.assertIn('원고에 실제로 있는 문장입니다.', prompt)
        with self.assertRaises(ValueError):
            personas.select(data, ['b' * 32])
        profile['age'] = 31
        with self.assertRaises(ValueError):
            personas.validate_profiles(data)
        with self.assertRaises(ValueError):
            personas.validate_profiles({'source_kind': 'role_assumption', 'readers': []})

    def test_imported_expression_judgments_survive_further_calibration(self):
        old = self.root / 'old'
        expressions.initialize(old)
        candidate = self.root / 'candidate.md'; candidate.write_text('서로 배우는 여정이다. 의자는 제자리에 둔다.')
        expressions.record(old, candidate, '여정', 0, '추상적이다', '배우는 여정', '소개')
        new = self.root / 'new'
        expressions.initialize(new, old / 'checks.json')
        expressions.record(new, candidate, '자리', 2, '실제 위치', '제자리에 둔다', '안내')
        checks = json.loads((new / 'checks.json').read_text())
        self.assertEqual(len(checks['calibrations']), 2)
        self.assertIn('여정', checks['watch'])
        self.assertEqual(checks['calibrations'][0]['reason_verbatim'], '추상적이다')

    def test_missing_shards_are_not_a_complete_cache_and_prepare_never_downloads_implicitly(self):
        home = self.root / 'hf'
        shard_dir = home / 'hub/datasets--nvidia--Nemotron-Personas-Korea/snapshots/fixture/data'
        shard_dir.mkdir(parents=True)
        (shard_dir / 'train-00000-of-00002.parquet').write_bytes(b'PAR1fixturePAR1')
        self.assertFalse(personas.inspect_cache(home)['complete'])
        with self.assertRaises(ValueError):
            personas.prepare(home)
        (shard_dir / 'train-00001-of-00002.parquet').write_bytes(b'PAR1fixturePAR1')
        self.assertTrue(personas.inspect_cache(home)['complete'])
        with self.assertRaises(FileExistsError):
            personas.write_new(shard_dir / 'train-00000-of-00002.parquet', 'do not replace')
        self.assertEqual((shard_dir / 'train-00000-of-00002.parquet').read_bytes(), b'PAR1fixturePAR1')


if __name__ == '__main__':
    unittest.main()
