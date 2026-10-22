#!/usr/bin/env python3
"""선택한 도구의 사용자 스킬 폴더에 이 저장소를 심볼릭 링크한다."""
import argparse
import re
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('target',choices=['codex','claude'])
    p.add_argument('--home',type=Path,default=Path.home(),help=argparse.SUPPRESS)
    p.add_argument('--uninstall',action='store_true')
    a=p.parse_args();source=Path(__file__).resolve().parent
    skills=a.home/('.codex'if a.target=='codex'else'.claude')/'skills'
    match=re.search(r'^name:\s*([a-z0-9-]+)\s*$',(source/'SKILL.md').read_text(encoding='utf-8'),re.M)
    if not match:sys.exit('SKILL.md의 name을 확인할 수 없습니다.')
    name=match.group(1)
    target=skills/name
    legacy=skills/'saramnaemsae'
    exists=target.exists()or target.is_symlink()
    same=target.is_symlink()and target.resolve()==source
    if a.uninstall:
        if same:target.unlink();print('이 저장소의 설치 링크를 해제했습니다. 원고와 평가는 유지합니다.')
        elif exists:sys.exit('이 저장소의 링크가 아니므로 삭제하지 않았습니다: '+str(target))
        else:print('설치 링크가 없습니다.')
    else:
        if exists and not same:sys.exit('기존 스킬을 덮어쓰지 않았습니다: '+str(target))
        target.parent.mkdir(parents=True,exist_ok=True)
        if not same:target.symlink_to(source,target_is_directory=True)
        if name=='my-writing-skill' and legacy.is_symlink() and legacy.resolve()==source:
            legacy.unlink()
            print('이 저장소의 이전 설치 링크를 새 이름으로 옮겼습니다.')
        print('설치됨: '+str(target))
        print(f'새 대화에서 ${name} 로 요청하세요.'if a.target=='codex'else f'새 대화에서 /{name} 로 요청하세요.')


if __name__=='__main__':main()
