스킬 폴더의 분석 스크립트가 작업 디렉터리에 있는지 확인한 뒤, 원문과 후보에 같은 코드를 돌려 관찰값을 함께 제시하겠습니다.


<invoke name="Bash">
<parameter name="command">ls -la /private/tmp/saramnaemsae-eval-r62 2>/dev/null; echo "---"; find /private/tmp/saramnaemsae-eval-r62 -maxdepth 3 -name "analyze.py" 2>/dev/null</parameter>
<parameter name="description">작업 디렉터리와 analyze.py 존재 확인</parameter>
</invoke>