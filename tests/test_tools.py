"""공개 도구의 프로그램 계약 검사. 모델 응답 품질 평가가 아니다."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run([sys.executable,*map(str,args)],cwd=ROOT,capture_output=True,text=True)


class Tools(unittest.TestCase):
    def test_analyzer_counts_and_keeps_signal_boundary(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d);(p/'input.txt').write_text('상품을 골랐다. 그래서 금액이 바뀌었다.\n\n다시 확인했다.')
            r=run('scripts/analyze.py',p/'input.txt','--output',p/'out.json');self.assertEqual(r.returncode,0,r.stderr)
            v=json.loads((p/'out.json').read_text());self.assertEqual(v['summary']['sentences'],3);self.assertEqual(v['summary']['leading_connectives'],1);self.assertEqual(v['definitions']['policy'],'signals_only_no_quality_score')

    def test_program_format_examples(self):
        for case in sorted((ROOT/'eval/cases').iterdir()):
            with self.subTest(case=case.name):
                r=run('scripts/grade.py',case,ROOT/'eval/program-fixtures'/(case.name+'.md'));self.assertEqual(r.returncode,0,r.stdout+r.stderr)

    def test_incomplete_or_error_response_cannot_pass(self):
        for response in ['Not logged in · Please run /login', '<invoke name="Bash">ls</invoke>', '먼저 파일을 확인하겠습니다.']:
            with self.subTest(response=response),tempfile.TemporaryDirectory() as d:
                p=Path(d)/'response.md';p.write_text(response)
                r=run('scripts/grade.py','eval/cases/03-causality',p)
                self.assertNotEqual(r.returncode,0)
                self.assertIn('format',r.stdout)

    def test_trap_in_log_is_not_preserved_in_body(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'response.md';p.write_text('## 수정본\n\n식물과 도구가 있다.\n\n## 변경 기록\n\n| 유형 | before | after | 이유 | 상태 |\n|---|---|---|---|---|\n| 위치 | 그 자리에는 | 식물과 도구 | 삭제 | 적용 |\n')
            r=run('scripts/grade.py','eval/cases/02-preserve',p);self.assertNotEqual(r.returncode,0);self.assertIn('trap 훼손',r.stdout)

    def test_silent_change_with_empty_table_fails(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d)/'response.md';p.write_text('## 수정본\n\n그 자리에는 다른 물건이 있다.\n\n## 변경 기록\n\n| 유형 | before | after | 이유 | 상태 |\n|---|---|---|---|---|\n\n적용 0건, 보류 0건\n')
            r=run('scripts/grade.py','eval/cases/02-preserve',p);self.assertNotEqual(r.returncode,0);self.assertIn('format',r.stdout)

    def test_installer_idempotence_and_uninstall(self):
        for target,config in [('codex','.codex'),('claude','.claude')]:
            with self.subTest(target=target),tempfile.TemporaryDirectory()as d:
                dest=Path(d)/config/'skills/my-writing-skill'
                self.assertEqual(run('install.py',target,'--home',d).returncode,0)
                self.assertTrue(dest.is_symlink());self.assertEqual(dest.resolve(),ROOT)
                self.assertEqual(run('install.py',target,'--home',d).returncode,0)
                self.assertEqual(run('install.py',target,'--home',d,'--uninstall').returncode,0)
                self.assertFalse(dest.is_symlink())

    def test_installer_preserves_existing_skill(self):
        with tempfile.TemporaryDirectory()as d:
            dest=Path(d)/'.codex/skills/my-writing-skill';dest.mkdir(parents=True);(dest/'keep.md').write_text('keep')
            self.assertNotEqual(run('install.py','codex','--home',d).returncode,0)
            self.assertEqual((dest/'keep.md').read_text(),'keep')
            self.assertNotEqual(run('install.py','codex','--home',d,'--uninstall').returncode,0)
            self.assertTrue((dest/'keep.md').exists())

    def test_installer_migrates_only_own_legacy_link(self):
        with tempfile.TemporaryDirectory() as d:
            skills=Path(d)/'.codex/skills';skills.mkdir(parents=True)
            legacy=skills/'saramnaemsae';legacy.symlink_to(ROOT,target_is_directory=True)
            self.assertEqual(run('install.py','codex','--home',d).returncode,0)
            self.assertFalse(legacy.is_symlink())
            self.assertEqual((skills/'my-writing-skill').resolve(),ROOT)

    def test_installer_keeps_foreign_legacy_skill(self):
        with tempfile.TemporaryDirectory() as d:
            legacy=Path(d)/'.codex/skills/saramnaemsae';legacy.mkdir(parents=True)
            (legacy/'keep.md').write_text('keep')
            self.assertEqual(run('install.py','codex','--home',d).returncode,0)
            self.assertEqual((legacy/'keep.md').read_text(),'keep')

    def test_rating_requires_real_span_and_preserves_reason(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d);(p/'candidate.md').write_text('나는 이 문장을 다시 읽었다.')
            args=['scripts/record_rating.py',p/'candidate.md','--score','1','--reason','말이 길게 느껴진다','--evidence','이 문장을','--output',p/'ratings.jsonl']
            self.assertEqual(run(*args).returncode,0)
            v=json.loads((p/'ratings.jsonl').read_text());self.assertEqual(v['score'],1);self.assertEqual(v['reason_verbatim'],'말이 길게 느껴진다');self.assertIsNone(v['adopted'])
            args[args.index('이 문장을')]='없는 구절';self.assertNotEqual(run(*args).returncode,0)
            self.assertEqual(len((p/'ratings.jsonl').read_text().splitlines()),1)

    def test_out_of_range_score_is_rejected(self):
        with tempfile.TemporaryDirectory()as d:
            p=Path(d);(p/'candidate.md').write_text('예문')
            r=run('scripts/record_rating.py',p/'candidate.md','--score','3','--reason','좋다','--evidence','예문','--output',p/'out.jsonl');self.assertNotEqual(r.returncode,0);self.assertFalse((p/'out.jsonl').exists())


if __name__=='__main__':unittest.main()
