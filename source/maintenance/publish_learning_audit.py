"""Publish the review and its evidence beside the local learning workbook."""
from pathlib import Path
import shutil
import subprocess
import sys
import json

ROOT=Path(__file__).resolve().parent
BOOK=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')

def main():
    assert (ROOT/'research/learning-redesign.json').exists(),'Design report must be complete before publication'
    subprocess.run([sys.executable,str(ROOT/'build_learning_audit.py')],check=True)
    evidence=BOOK/'学习审查资料'
    shutil.copytree(ROOT/'research',evidence,dirs_exist_ok=True,ignore=shutil.ignore_patterns('学习架构审查台.html','__pycache__','*draft*','*live-extract*'))
    qa=BOOK/'architecture-audit-qa'
    qa.mkdir(exist_ok=True)
    for name in ['reliability-tests.json','reliability-patch.json','reliability-reapplied.json','learning-review-integration.json','final-static-validation.json','dashboard-browser-validation.json']:
        source=ROOT/'architecture-audit-qa'/name
        if source.exists():shutil.copy2(source,qa/name)
    output=BOOK/'学习架构审查台.html'
    subprocess.run([sys.executable,str(ROOT/'build_learning_audit.py'),'--output',str(output),'--base-research-url','学习审查资料/','--main-book-url','开始学习.html'],check=True)
    print(json.dumps({'report':str(output),'evidence':str(evidence),'main_book':'开始学习.html','copied_evidence_files':sum(1 for p in evidence.rglob('*') if p.is_file())},ensure_ascii=False))

if __name__=='__main__':main()
