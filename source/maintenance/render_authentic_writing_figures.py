from pathlib import Path
import pypdfium2 as pdf
import json
B=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册')
S=[
 ('8ee8170c*.pdf',30,'writing-c21-30.png',(0.165,0.415,0.927,0.780)),
 ('8ee8170c*.pdf',52,'writing-c21-52.png',(0.338,0.417,0.783,0.913)),
 ('8ee8170c*.pdf',73,'writing-c21-73.png',(0.073,0.425,0.853,0.895)),
 ('8ee8170c*.pdf',95,'writing-c21-95.png',(0.173,0.430,0.773,0.913)),
 ('writing-official-sample-tasks-2023.pdf',3,'writing-official-3.png',(0.110,0.359,0.848,0.872)),
 ('writing-official-sample-tasks-2023.pdf',4,'writing-official-4.png',(0.110,0.375,0.949,0.795)),
 ('writing-official-sample-tasks-2023.pdf',5,'writing-official-5.png',(0.117,0.405,0.926,0.886)),
 ('writing-official-large-print.pdf',4,'writing-bicycle-4.png',(0.060,0.438,0.960,0.815)),
]
results=[]
for pat,page,name,rect in S:
 source=next(B.rglob(pat)); doc=pdf.PdfDocument(str(source));p=doc[page-1]; w,h=p.get_size();l,t,r,b=rect
 crop=(l*w,(1-b)*h,(1-r)*w,t*h)
 scale=max(2.4,1400/((r-l)*w))
 im=p.render(scale=scale,crop=crop).to_pil(); dest=B/'case-assets'/name; im.save(dest)
 results.append(dict(source=source.relative_to(B).as_posix(),page=page,rectNormalizedTopLeft=list(rect),width=im.width,height=im.height,image=dest.relative_to(B).as_posix()))
Path('writing-source-cache/figure-clips.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),'utf-8')
print(json.dumps(results,ensure_ascii=False))
