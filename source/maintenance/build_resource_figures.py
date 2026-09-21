from pathlib import Path
from html import escape
HERE=Path(__file__).resolve().parent
DEST=HERE/'resource-figures';DEST.mkdir(exist_ok=True)
def svg(w,h,body):return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="#fffaf8"/><g font-family="Arial,sans-serif" fill="#922331">{body}</g></svg>'
def txt(x,y,s,size=16,extra=''):return f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{escape(str(s))}</text>'
body=txt(35,38,'Library layout: 2010 and 2025',25)+txt(35,66,'Relative positions only; not to scale.',14)
grids=[['Book shelves','Book shelves','Storage room','Reading tables','Reading tables','Staff office','Reception','Entrance','Car park'],['Book shelves','Book shelves','Study room','Reading tables','Computer area','Staff office','Reception','Entrance','Garden']]
for j,cells in enumerate(grids):
    bx=35+j*505;body+=txt(bx,110,[2010,2025][j],22)
    for i,label in enumerate(cells):
        x=bx+(i%3)*148;y=137+(i//3)*92
        changed=j==1 and i in [2,4,8]
        body+=f'<rect x="{x}" y="{y}" width="148" height="92" fill="'+('#fbe1df' if changed else '#fffdf9')+'" stroke="#ad6970" stroke-width="1.5"/>'
        body+=txt(x+74,y+49,label,15,'text-anchor="middle"')
    body+=txt(bx+222,446,'South entrance',14,'text-anchor="middle"')
    body+=f'<path d="M{bx+222},433 v-15 m-5,5 l5,-5 l5,5" stroke="#922331" fill="none"/>'
body+=txt(996,101,'N',15,'text-anchor="middle"')+'<path d="M996 133V112m-5 6 5-6 5 6" stroke="#922331" stroke-width="2" fill="none"/>'
body+=txt(35,490,'Shaded cells identify changes in 2025. The remaining facilities retain their positions.',14)
(DEST/'library-maps.svg').write_text(svg(1030,525,body),encoding='utf8')
body=txt(35,36,'Main commuting mode in Cedarford, 2010–2025',24)+txt(35,63,'Percentage of adult residents · Each year totals 100%',14)
bx,by,width,height=80,100,740,330
for v in range(0,71,10):
    y=by+height-v/70*height;body+=f'<line x1="{bx}" y1="{y}" x2="{bx+width}" y2="{y}" stroke="#eadbdd"/>'+txt(bx-15,y+5,str(v)+'%',13,'text-anchor="end"')
for i,year in enumerate([2010,2015,2020,2025]):body+=txt(bx+i*width/3,by+height+28,year,15,'text-anchor="middle"')
styles=[('Car',[60,54,46,40],'#8e1423',''),('Bus',[25,28,31,35],'#bf3d49','9 4'),('Bicycle',[10,12,17,20],'#9b5860','3 4'),('On foot',[5,6,6,5],'#653940','12 4 2 4')]
for j,(name,values,color,dash) in enumerate(styles):
    points=' '.join(f'{bx+i*width/3},{by+height-v/70*height}' for i,v in enumerate(values))
    body+=f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>'
    for i,v in enumerate(values):body+=f'<circle cx="{bx+i*width/3}" cy="{by+height-v/70*height}" r="4" fill="{color}"/>'
    y=160+j*50;body+=f'<line x1="850" y1="{y}" x2="895" y2="{y}" stroke="{color}" stroke-width="3" stroke-dasharray="{dash}"/>'+txt(910,y+5,name,16)
body+=txt(35,502,'Shares are shown, not absolute numbers of commuters.',14)
(DEST/'commuting-trends.svg').write_text(svg(1030,530,body),encoding='utf8')
print('Created two original Task 1 figures')
