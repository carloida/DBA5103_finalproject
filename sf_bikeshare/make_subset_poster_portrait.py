"""Render the concise, plain-language WhatsApp poster as one 9:16 PNG."""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'output/sf_bikeshare/subset_assessment'
OUT=ROOT/'output/sf_bikeshare/whatsapp'
TMP=ROOT/'tmp/subset_poster_portrait'
OUT.mkdir(exist_ok=True);TMP.mkdir(parents=True,exist_ok=True)
W,H=1800,3200
INK='#23333f';MUTED='#5b6873';BLUE='#5a76a4';GREEN='#168375';LINE='#dce2e6';BG='#ffffff'
im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
FONTS=Path('C:/Windows/Fonts')
blocks=[]

def font(size,bold=False):
    return ImageFont.truetype(str(FONTS/('arialbd.ttf' if bold else 'arial.ttf')),size)

def text(value,x,y,size=36,color=INK,bold=False,width=1620,gap=9):
    f=font(size,bold);lines=[]
    for para in str(value).split('\n'):
        line=''
        for word in para.split():
            attempt=(line+' '+word).strip()
            if line and d.textlength(attempt,font=f)>width:
                lines.append(line);line=word
            else:line=attempt
        lines.append(line)
    for line in lines:
        assert d.textlength(line,font=f)<=width+1, line
        d.text((x,y),line,font=f,fill=color)
        y+=size+gap
    return y

def check(name,end,limit):
    blocks.append(dict(block=name,bottom=end,limit=limit))
    assert end<=limit,(name,end,limit)

def section(title,y):
    d.line((85,y-23,1715,y-23),fill=LINE,width=3)
    text(title,85,y,43,bold=True)

def chart_image(name,fig,box):
    fig.savefig(TMP/(name+'.png'),dpi=170,facecolor='white')
    plt.close(fig)
    g=Image.open(TMP/(name+'.png')).convert('RGB')
    x,y,w,h=box
    g=g.resize((w,h),Image.Resampling.LANCZOS)
    im.paste(g,(x,y))

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':18,'axes.spines.top':False,
    'axes.spines.right':False,'axes.spines.left':False,'axes.spines.bottom':False,
    'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,
    'axes.titlecolor':INK,'text.color':INK,'axes.titleweight':'bold'})

text('SF Bike Share: data subset',85,48,72,bold=True)
text('For team review | 17 Nov 2026',87,145,30,MUTED)
end=text('I kept one city and 10 weeks of data for our first model.',85,201,42,width=1620)
end=text('Goal: decide where and when to move bikes to earn the most extra trip income after moving costs, within station and truck limits.',85,271,36,width=1620)
check('intro',end,376)

section('How I reduced the files',410)
steps=[('Original files','70 stations, 5 cities\nAug 2013-Aug 2015'),
       ('San Francisco','34 stations installed\nby 29 Aug 2013'),
       ('10 complete weeks','9 Feb-19 Apr 2015\n8 weeks + 2 to check'),
       ('Hourly summary','57,120 rows\n4.72% of hourly rows')]
for i,(title,body) in enumerate(steps):
    x=85+i*415
    d.rounded_rectangle((x,487,x+385,675),radius=10,fill='#f0f4f6' if i<3 else '#e9f3ef')
    text(title,x+20,510,34,bold=True,width=350)
    end=text(body,x+20,565,30,MUTED,width=350,gap=10)
    check('process '+str(i),end,668)
    if i<3:
        d.line((x+390,578,x+410,578),fill=MUTED,width=3)
        d.polygon([(x+410,578),(x+401,572),(x+401,584)],fill=MUTED)
end=text('I kept full weeks, including unusual-usage days.',85,701,32,MUTED)
check('process note',end,752)

section('File size: original vs subset',799)
fig,ax=plt.subplots(figsize=(15.8,2.5))
sizes=[2070.348941,.247473]
ax.barh([1,0],sizes,color=[BLUE,GREEN],height=.46)
ax.set_yticks([1,0],['Original CSV files','Subset (Parquet)'])
ax.set_xlim(0,2300);ax.set_xticks([0,500,1000,1500,2000])
ax.set_xlabel('File size in MB',labelpad=8);ax.tick_params(length=0,pad=10)
for y,value,label in zip([1,0],sizes,['2,070.35 MB','0.247 MB']):
    ax.text(value-34 if y else value+34,y,label,va='center',
            ha='right' if y else 'left',fontsize=20,weight='bold',color='white' if y else GREEN)
ax.grid(axis='x',alpha=.13);ax.set_axisbelow(True)
fig.subplots_adjust(left=.18,right=.99,top=.96,bottom=.30)
chart_image('file_size',fig,(85,858,1630,275))
end=text('99.988% less file space. The subset bar is almost invisible on this scale.',85,1138,35,GREEN,True)
end=text('The reduction includes fewer stations/dates, hourly summaries and file compression.',85,1190,31,MUTED)
check('size chart',end,1241)

section('Do the daily patterns still look similar?',1283)
p=pd.read_csv(DATA/'hourly_pattern_comparison.csv')
fig,ax=plt.subplots(figsize=(15.8,4.0))
for period,color,label in [('Reference',BLUE,'Other 94 weeks'),('Candidate',GREEN,'Selected 10 weeks')]:
    q=p[(p.period==period)&(p.day_type=='Weekday')].sort_values('hour')
    # The saved profile is the mean count per station-hour; keep 34 stations on both sides.
    ax.plot(q.hour,q.departures*34,lw=3.5,color=color,label=label)
ax.set_xlim(0,23);ax.set_ylim(0,200)
ax.set_xticks([0,4,8,12,17,20,23],['12 am','4 am','8 am','12 pm','5 pm','8 pm','11 pm'])
ax.set_yticks([0,50,100,150,200]);ax.set_ylabel('Pickups per hour')
ax.grid(axis='y',alpha=.16);ax.tick_params(length=0,pad=10)
ax.legend(frameon=False,loc='upper left',fontsize=18)
fig.subplots_adjust(left=.095,right=.965,top=.96,bottom=.16)
chart_image('weekday_pickups',fig,(85,1347,1630,420))
end=text('Both peak around 8 am and 5 pm. The selected period is busier on weekdays.',85,1786,34,bold=True)
end=text('Both lines use the same 34 SF stations. The other 94 weeks exclude the selected dates.',85,1837,30,MUTED)
check('hourly chart',end,1890)

section('Some conditions are different',1930)
s=pd.read_csv(DATA/'pattern_period_summary.csv').set_index('period')
a=s.loc['Other 94 weeks (reference)'];b=s.loc['Candidate 10 weeks']
fig,axes=plt.subplots(1,3,figsize=(15.8,3.7))
specs=[('Weekday pickups / day',[a.weekday_departures_per_day,b.weekday_departures_per_day],['985','1,116'],1450,''),
       ('Time with no bikes',[a.empty_pct,b.empty_pct],['1.16%','1.85%'],2.5,'%'),
       ('Unusual days*',[100*a.iqr_flagged_days/a.days,100*b.iqr_flagged_days/b.days],['7.0%','1.4%'],9.5,'%')]
for ax,(title,values,labels,top,unit) in zip(axes,specs):
    ax.bar([0,1],values,color=[BLUE,GREEN],width=.52)
    ax.set_xticks([0,1],['Other weeks','Subset']);ax.set_ylim(0,top)
    ax.set_title(title,fontsize=18,pad=13)
    for i,(value,label) in enumerate(zip(values,labels)):
        ax.text(i,value+top*.035,label,ha='center',fontsize=21,weight='bold')
    ax.tick_params(length=0,pad=8);ax.grid(axis='y',alpha=.12);ax.set_axisbelow(True)
    if unit:
        from matplotlib.ticker import FuncFormatter
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value,pos:f'{value:g}%'))
fig.subplots_adjust(left=.065,right=.99,top=.85,bottom=.18,wspace=.40)
chart_image('operating_differences',fig,(85,1990,1630,385))
end=text('*Unusual daily totals: 46 of 658 other days, and 1 of 70 selected days. All were kept.',85,2388,29,MUTED)
end=text('No-bike figures measure time, not the number of customers who missed a ride.',85,2431,29,MUTED)
check('comparison chart',end,2480)

section('What the subset contains',2524)
cols=[85,920]
text('IN THE SUBSET',cols[0]+15,2592,28,MUTED,True,width=780)
text('WHAT IT HELPS US DO',cols[1]+15,2592,28,MUTED,True,width=780)
rows=[('Hourly pickups and returns','See where bikes leave and arrive'),
      ('Time with no bikes / no free docks','Estimate requests we could not observe'),
      ('Weather, matched by date and city','Check dry-day and rainy-day scenarios')]
for i,(left,right) in enumerate(rows):
    y=2645+i*63
    if i%2==0:d.rectangle((85,y-3,1715,y+58),fill='#f1f4f6')
    text(left,100,y+9,32,width=795)
    text(right,935,y+9,32,width=770)
check('table',2645+3*63,2853)

end=text('Next: agree on the subset, estimate missed requests and moving costs, then compare no moves, a simple rule and an optimized plan.',85,2870,35,bold=True)
check('next steps',end,2990)
end=text('Advanced machine learning is optional. I suggest testing rainy and unusual days before we draw final conclusions.',85,3001,32,MUTED)
check('closing note',end,3100)
d.line((85,3122,1715,3122),fill=LINE,width=2)
text('Source: SF Bay Area Bike Share, Kaggle (Ben Hamner). Local audit and subset checks.',85,3140,25,MUTED)

path=OUT/'SF_Bikeshare_Subset_Poster.png'
im.save(path,optimize=True)
preview=im.copy();preview.thumbnail((900,1600));preview.save(TMP/'poster_preview.png')
assert W*16==H*9
metadata=dict(output=str(path.relative_to(ROOT)),pixels=[W,H],aspect_ratio='9:16 portrait',
              graph_count=5,layout_checks=blocks,source='Saved full-data and subset audit results',
              output_format='One PNG image; previous PDF not regenerated')
(DATA/'poster_validation.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
print('Saved',path,'at',W,'x',H)
