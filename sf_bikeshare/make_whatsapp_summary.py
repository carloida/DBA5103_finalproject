"""Create four short, phone-readable SF EDA briefing pictures."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'output/sf_bikeshare'
OUT=DATA/'whatsapp';OUT.mkdir(exist_ok=True)
TMP=ROOT/'tmp/sf_whatsapp';TMP.mkdir(parents=True,exist_ok=True)
metrics=json.loads((DATA/'analysis_manifest.json').read_text())
W,H=1080,1640
INK,BG,BLUE,TEAL,ORANGE,MUTED='#132e43','#edf3f7','#2568ad','#008b81','#dc942c','#50677a'
FONTS=Path('C:/Windows/Fonts')
def font(size,bold=False):return ImageFont.truetype(str(FONTS/('arialbd.ttf' if bold else 'arial.ttf')),size)
plt.rcParams.update({'font.size':15,'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,
                     'xtick.labelsize':14,'ytick.labelsize':14,'axes.labelsize':15,'axes.titleweight':'bold'})
def chart(name,fn):
    fig,ax=plt.subplots(figsize=(6.3,2.9),dpi=160)
    fn(ax);ax.tick_params(length=0,pad=8)
    fig.tight_layout(pad=.7)
    p=TMP/f'{name}.png';fig.savefig(p,facecolor='white');plt.close(fig)
    im=Image.open(p).convert('RGB');return im.resize((960,round(im.height*960/im.width)),Image.Resampling.LANCZOS)
def wrap(draw,value,face,width):
    lines=[]
    for para in value.split('\n'):
        line=''
        for word in para.split():
            test=(line+' '+word).strip()
            if line and draw.textlength(test,font=face)>width:lines.append(line);line=word
            else:line=test
        lines.append(line)
    return lines
def write(im,value,x,y,size=37,color=INK,bold=False,width=960,gap=10):
    draw=ImageDraw.Draw(im);face=font(size,bold)
    for line in wrap(draw,value,face,width):
        draw.text((x,y),line,font=face,fill=color);y+=size+gap
    return y
def base(n,title,subtitle):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
    d.rectangle((0,0,W,300),fill=INK)
    write(im,f'SF BAY AREA BIKE SHARE  /  {n} OF 4',54,35,26,'#75dacf',True)
    y=write(im,title,54,92,56,'white',True)
    write(im,subtitle,54,y+17,30,'#c8d9e7')
    return im
def stats(im,left,right,y=336):
    for x,(value,label) in zip([60,560],[left,right]):
        write(im,value,x,y,58,TEAL,True,width=460)
        write(im,label,x,y+78,29,MUTED,width=460)
def plot(im,graph,y=490):
    im.paste(graph,(60,y));return y+graph.height
def callout(im,title,body,y,height):
    d=ImageDraw.Draw(im);d.rounded_rectangle((36,y,1044,y+height),radius=24,fill=INK)
    y=write(im,title,60,y+26,29,'#75dacf',True)
    end=write(im,body,60,y+14,35,'white',width=960)
    assert end<=y+height-20,(title,end,y+height)
def save(im,n):
    write(im,f'{n}/4  |  Local EDA tables  |  15 Nov 2026',54,H-56,25,MUTED)
    im.save(OUT/f'SF_Bikeshare_EDA_{n}_of_4.png',optimize=True)
    preview=im.copy();preview.thumbnail((540,820));preview.save(TMP/f'review_{n}.png')

hour=pd.read_csv(DATA/'hourly_usage_profile.csv')
def usage(ax):
    for label,color in [('Weekday',BLUE),('Weekend',ORANGE)]:
        p=hour[hour.day_type.eq(label)].sort_values('hour')
        ax.plot(p.hour,p.trips_per_calendar_day,lw=3,color=color,label=label)
    ax.set_xticks([0,6,12,18,23]);ax.set_xlabel('Departure hour');ax.set_ylabel('Trips / day')
    ax.legend(frameon=False,fontsize=13)
im=base(1,'Usage looks familiar','Historical data: August 2013-August 2015')
stats(im,('669,959','completed trips'),('70','stations across 5 cities'))
y=plot(im,chart('usage',usage))
y=write(im,'Peak weekday hours: 08:00, 17:00 and 09:00.',60,y+26,39,bold=True)
y=write(im,'The broad morning/evening pattern resembles Citi Bike. Weekends have a flatter daytime profile.',60,y+15,37)
callout(im,'KEEP THE COMPARISON FAIR','Different systems and time periods. Similar-looking peaks do not mean the demand levels or business conditions are the same.',1282,270)
save(im,1)

profile=pd.read_csv(DATA/'hourly_availability_profile.csv')
def exposure(ax):
    p=profile[profile.day_type.eq('Weekday')].sort_values('hour')
    ax.plot(p.hour,p.empty_pct,lw=3,color=BLUE,label='No bikes')
    ax.plot(p.hour,p.full_pct,lw=3,color=ORANGE,label='No free docks')
    ax.set_xticks([0,6,12,18,23]);ax.set_xlabel('Weekday hour');ax.set_ylabel('% observed time')
    ax.legend(frameon=False,fontsize=13)
im=base(2,'We can see availability','71.98 million station-status observations')
stats(im,('0.74%','empty: no available bikes'),('0.45%','full: no free docks'))
y=plot(im,chart('exposure',exposure))
y=write(im,'Availability pressure rises around weekday peaks.',60,y+26,39,bold=True)
write(im,'The percentages above use valid observed time across the whole system. Individual stations can have much higher exposure.',60,y+15,37)
callout(im,'THIS IS THE MAIN IMPROVEMENT','We can identify empty/full periods. We still cannot directly count the customers who arrived then and could not use the service.',1282,270)
save(im,2)

weekly=pd.read_csv(DATA/'weekly_paired_comparison.csv')
def comparison(ax):
    vals=[weekly.weekday_mean.mean(),weekly.weekend_mean.mean()]
    bars=ax.bar(['Weekdays','Weekends'],vals,color=[BLUE,ORANGE],width=.55)
    for bar,v in zip(bars,vals):ax.text(bar.get_x()+bar.get_width()/2,v+20,f'{v:,.0f}',ha='center',fontsize=18,weight='bold')
    ax.set_ylim(0,1200);ax.set_ylabel('Mean completed trips / day')
    ax.set_title('Fixed 34-station San Francisco cohort',fontsize=15)
im=base(3,'Weekdays are busier','Time-aware statistical comparisons')
stats(im,('+655 trips','weekday minus weekend / day'),('598-718','95% block-bootstrap interval'))
y=plot(im,chart('comparison',comparison))
y=write(im,'Weekday usage is higher even within a fixed station group.',60,y+26,39,bold=True)
write(im,'Adjusted rain association: about -22% (95% interval: -30% to -12%). The model uses log(1 + daily trips), with calendar and weather controls.',60,y+15,36)
callout(im,'HOW TO READ THESE RESULTS','These are historical associations, not proof of causation. The rain estimate changes when trace rain counts as a rainy day.',1320,232)
save(im,3)

im=base(4,'What is still missing?','Better inventory evidence; financial gaps remain')
d=ImageDraw.Draw(im)
rows=[('Station inventory','Observed, with gaps',TEAL),('Dock capacity','Static; needs review',ORANGE),
      ('Unfulfilled requests','Not directly counted',ORANGE),('Costs and revenue','Missing',BLUE)]
for i,(label,value,color) in enumerate(rows):
    y=345+i*123
    d.rounded_rectangle((36,y,1044,y+105),radius=18,fill='white')
    write(im,label,60,y+17,35,bold=True,width=480)
    write(im,value,565,y+20,31,color,True,width=440)
y=write(im,'4.7% of status snapshots differ from the listed dock count.',60,862,39,bold=True)
y=write(im,'We still need bike/dock purchase costs, maintenance and parts, staff and truck costs, and actual payments or suitable revenue assumptions.',60,y+18,37)
write(im,'The four CSVs are linked in a local DuckDB database. The large database file stays local.',60,y+20,35,MUTED)
callout(im,'FOR OUR MEETING','This dataset can support an inventory-aware redistribution model. We still need to agree on the demand estimates, cost assumptions and comparison policies.',1282,270)
save(im,4)
print('Saved four SF WhatsApp pictures, each 1080 x 1640.')
