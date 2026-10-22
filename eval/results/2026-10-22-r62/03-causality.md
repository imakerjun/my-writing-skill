먼저 작업 폴더에 스킬 스크립트가 있는지 확인한 뒤, 원문을 신호 기준으로 검토하겠습니다.


<invoke name="Glob">
<invoke name="pattern">**/analyze.py</invoke>
<invoke name="path">/private/tmp/saramnaemsae-eval-r62</invoke>
</invoke>
<invoke name="Bash">
<invoke name="command">ls -la /private/tmp/saramnaemsae-eval-r62</invoke>
<invoke name="description">작업 폴더 내용 확인</invoke>
</invoke>
</invoke>