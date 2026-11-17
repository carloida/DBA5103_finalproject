"""Build an evidence-based WhatsApp poster and PDF from saved subset audits."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'output/sf_bikeshare/subset_assessment'
OUT=ROOT/'output/sf_bikeshare/whatsapp';OUT.mkdir(exist_ok=True)
PDF=ROOT/'output/pdf';PDF.mkdir(exist_ok=True)
TMP=ROOT/'tmp/subset_poster';TMP.mkdir(parents=True,exist_ok=True)
W,H=1440,3440
BG='#eef3f3';INK='#173438';TEAL='#007f79';BLUE='#456bb1';AMBER='#a35a1b';MUTED='#52686c'
im=Image.new('RGB',(W,H),BG);draw=ImageDraw.Draw(im)
FONTS=Path('C:/Windows/Fonts')
checks=[]

def face(size,bold=False):
    return ImageFont.truetype(str(FONTS/('arialbd.ttf' if bold else 'arial.ttf')),size)

def text(value,x,y,size=34,color=INK,bold=False,width=1280,spacing=10):
    font=face(size,bold);lines=[]
    for para in str(value).split('\n'):
        line=''
        for word in para.split():
            test=(line+' '+word).strip()
            if line and draw.textlength(test,font=font)>width:
                lines.append(line);line=word
            else:line=test
        lines.append(line)
    for line in lines:
        assert draw.textlength(line,font=font)<=width+1, ('text too wide',line)
        draw.text((x,y),line,font=font,fill=color)
        y+=size+spacing
    return y

def card(y,height,color='white'):
    draw.rounded_rectangle((48,y,W-48,y+height),radius=26,fill=color)

def label(n,title,y):
    draw.rounded_rectangle((76,y,120,y+44),radius=12,fill=TEAL)
    text(str(n),87,y+2,28,'white',True,width=34)
    text(title,140,y+1,34,INK,True,width=1220)

def fits(name,end,bottom):
    checks.append(dict(block=name,bottom=end,limit=bottom))
    assert end<=bottom,(name,end,bottom)

# Header + objective.
draw.rectangle((0,0,W,390),fill=INK)
text('DBA5103  /  TEAM SCOPE REVIEW  /  17 NOV 2026',76,32,27,'#9edcd1',True)
text('A smaller dataset. A clear decision.',76,95,59,'white',True)
text('SF Bike Share redistribution pilot',76,175,38,'#c8e0df')
end=text('Choose how many bikes to move, where and when, under bike inventory, dock and truck limits.',76,246,34,'white',width=1288)
fits('header problem',end,340)
end=text('Value vs no moves = extra trip contribution - extra redistribution cost',76,346,27,'#9edcd1',True,width=1288)
fits('header objective',end,383)

# Data provenance flow.
card(420,675)
label(1,'HOW THE KAGGLE DATA BECAME THE PILOT',447)
steps=[
 ('01','AUDIT THE ORIGINAL FILES','Trip + station + minute status + weather. Full source audit: 669,959 trips; 71.98 million status records; 70 stations in 5 cities.'),
 ('02','SELECT A DEFINED PILOT','34 San Francisco stations installed by 29 Aug 2013. Keep 9 Feb-19 Apr 2015: 10 complete calendar weeks.'),
 ('03','AGGREGATE AND LINK','Count pickups/returns by station-hour. Sum bounded empty/full and observed time; link weather by city and date. Keep boundary flows.'),
 ('04','SPLIT FOR ESTIMATION AND CHECKING','8 training weeks: 9 Feb-5 Apr. 2 validation weeks: 6-19 Apr. No random minute sampling; no extreme-usage days deleted.'),
]
y=516
for number,title,body in steps:
    draw.ellipse((78,y+2,136,y+60),fill='#e1f0ec')
    text(number,86,y+14,25,TEAL,True,width=52)
    text(title,158,y,29,INK,True,width=1170)
    end=text(body,158,y+45,31,MUTED,width=1160,spacing=7)
    fits(title,end,y+142)
    y+=142
fits('flow',y-5,1080)

# Count comparison table.
card(1120,460)
label(2,'WHAT IS IN THE CURRENT CANDIDATE?',1147)
cols=[82,610,1015]
y=1215
for x,t in zip(cols,['MEASURE','FULL SOURCE / PANEL','CANDIDATE']):text(t,x,y,25,MUTED,True,width=500 if x==82 else 370)
rows=[('Stations / geography','70 / 5 cities','34 / SF only'),
      ('Station-hour rows','1,209,456','57,120 (4.72%)'),
      ('File size, decimal','2,070.35 MB raw CSVs','0.247 MB Parquet'),
      ('Relevant completed trips*','669,959','63,974 (9.55%)')]
y=1264
for i,row in enumerate(rows):
    if i%2==0:draw.rounded_rectangle((70,y-5,1370,y+58),radius=10,fill='#f0f5f4')
    for x,t in zip(cols,row):text(t,x,y+4,29,INK,x==1015,width=510 if x==82 else 390)
    y+=60
end=text('*Trips touching selected stations/dates, counted once; stored as hourly counts. Storage reduction also reflects aggregation and compression.',82,1510,23,MUTED,width=1270,spacing=5)
fits('table note',end,1575)

# Honest profile comparison.
card(1605,745)
label(3,'DO THE PATTERNS REPEAT? SHAPE: YES. LEVELS: CHANGE.',1632)
text('Same 34 SF stations: candidate vs the other 94 complete weeks.',80,1693,29,MUTED)
p=pd.read_csv(DATA/'hourly_pattern_comparison.csv')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':15,'axes.spines.top':False,
                     'axes.spines.right':False,'axes.spines.left':False,'axes.labelcolor':MUTED,
                     'xtick.color':MUTED,'ytick.color':MUTED})
fig,ax=plt.subplots(figsize=(12.8,3.7),dpi=160)
for period,color,title in [('Reference',BLUE,'Other 94 weeks'),('Candidate',TEAL,'Candidate 10 weeks')]:
    q=p[(p.period==period)&(p.day_type=='Weekday')].sort_values('hour')
    ax.plot(q.hour,q.share_pct,color=color,lw=3.4,label=title)
ax.set_xticks([0,4,8,12,17,20,23]);ax.set_xlim(0,23);ax.set_ylim(bottom=0)
ax.set_xlabel('Recorded local hour');ax.set_ylabel('Share of weekday pickups (%)')
ax.grid(axis='y',alpha=.15);ax.tick_params(length=0,pad=7)
ax.legend(frameon=False,loc='upper left',fontsize=14)
fig.tight_layout(pad=.7)
chart=TMP/'weekday_shape.png';fig.savefig(chart,facecolor='white');plt.close(fig)
graph=Image.open(chart).convert('RGB');graph.thumbnail((1280,380))
im.paste(graph,(80,1738))
text('Same weekday peaks: 08:00 and 17:00  |  Shape correlation: 0.997',80,2128,30,TEAL,True)
draw.line((80,2184,1360,2184),fill='#dce6e4',width=2)
text('BUT THE OPERATING CONDITIONS DIFFER',80,2202,27,AMBER,True)
end=text('Weekday pickups/day: 985 reference vs 1,116 candidate.\nEmpty-time exposure: 1.16% reference vs 1.85% candidate.',80,2246,32,INK,width=1270,spacing=10)
fits('pattern graph',end,2337)

# Extremes + scope interpretation.
card(2375,455)
label(4,'OUTLIERS STAY IN THE DATA',2402)
end=text('Daily usage flags: 1 of 70 candidate days; 46 of 658 reference days. These are statistical flags, not automatic errors.',80,2464,33,width=1270)
end=text('The candidate includes 13 trips longer than 24 hours; they were retained with review flags. Only 6 of the reference top-10 empty/full-pressure stations also rank in the candidate top 10.',80,end+15,32,MUTED,width=1270)
end=text('This is a scoped pilot, not proof that all seasons, unusual days or station-level risks are interchangeable.',80,end+17,33,AMBER,True,width=1270)
fits('outliers',end,2817)

# Demand/model handoff and next decision.
card(2855,450,INK)
text('WHAT THIS MEANS FOR OUR PROJECT',80,2882,33,'#9edcd1',True)
end=text('Trips show served demand. Empty/full time helps estimate unrecorded requests; corrected demand is still to be fitted.',80,2942,33,'white',width=1270)
end=text('Optimization chooses bike movements. Advanced machine learning is optional; representative inputs and stress tests are still needed.',80,end+16,33,'white',width=1270)
end=text('NEXT: agree on pilot scope -> estimate demand and costs -> compare no moves, a simple rule and optimized moves -> test rain and extreme days.',80,end+18,31,'#c8e0df',width=1270)
fits('handoff',end,3290)

text('Source: Ben Hamner, SF Bay Area Bike Share (Kaggle); supplied local CSVs.',76,3330,24,MUTED,width=1290)
text('Checks: read-only full-data audits. Candidate remains proposed. Details and code accompany this poster.',76,3372,23,MUTED,width=1290)
png=OUT/'SF_Bikeshare_Subset_Poster.png';im.save(png,optimize=True)
preview=im.copy();preview.thumbnail((720,1720));preview.save(TMP/'poster_preview.png')
pdf=PDF/'SF_Bikeshare_Subset_Poster.pdf'
c=canvas.Canvas(str(pdf),pagesize=(504,504*H/W))
c.setTitle('SF Bike Share: pilot dataset, objective and pattern checks')
c.setAuthor('DBA5103 project data preparation')
c.drawImage(ImageReader(str(png)),0,0,width=504,height=504*H/W)
c.showPage();c.save()
(TMP/'layout_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print('Saved',png,'and',pdf)
