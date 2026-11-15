"""Rebuild the single-image group briefing from the exported EDA tables."""
from pathlib import Path
import json
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'output/citibike_eda'
OUT = ROOT / 'output/pdf'
TMP = ROOT / 'tmp/pdfs/citibike_poster'
OUT.mkdir(parents=True, exist_ok=True)
TMP.mkdir(parents=True, exist_ok=True)
M = json.loads((DATA / 'analysis_manifest.json').read_text())
def read(name):
    return pd.read_csv(DATA / f'{name}.csv')

INK, MUTED, BLUE, ORANGE, TEAL = '#132e43', '#50677a', '#2568ad', '#e59a37', '#008c86'
plt.rcParams.update({'font.size': 17, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.spines.left': False, 'axes.labelcolor': MUTED, 'xtick.color': MUTED,
                     'ytick.color': MUTED, 'text.color': INK, 'axes.titlecolor': INK,
                     'figure.facecolor': 'white', 'axes.facecolor': 'white'})

def chart(num, fn, height=3.15):
    fig, ax = plt.subplots(figsize=(10.5, height), dpi=110)
    fn(ax)
    ax.tick_params(length=0, pad=8)
    fig.tight_layout(pad=1)
    path = TMP / f'chart_{num:02}.png'
    fig.savefig(path, facecolor='white')
    plt.close(fig)
    return path

cards = []
def add(num, question, fn, finding, implication, height=3.15):
    cards.append((num, question, chart(num, fn, height), finding, implication))

def missing(ax):
    ax.barh(['End station ID', 'End latitude', 'End longitude', 'End station name'],
            [333,333,333,284], color=[BLUE,BLUE,BLUE,ORANGE])
    ax.invert_yaxis(); ax.set_xlim(0,400); ax.set_xlabel('Blank fields in 106,628 source rows')
    for i,v in enumerate([333,333,333,284]): ax.text(v+5,i,str(v),va='center')
add(1, 'Can we trust the records?', missing,
    'No exact duplicates or invalid trip times. 49 missing end IDs recovered by exact name; 284 remain unresolved (0.27%).',
    'Keep valid departures even when destinations are missing. Recovery is an explicit assumption.')

hour = read('hourly_usage_profile')
daily = read('daily_trips')
def usage(ax):
    for kind,color in [('Weekday',BLUE),('Weekend',ORANGE)]:
        p=hour[hour.day_type.eq(kind)]; ax.plot(p.hour,p.average_trips_per_day,color=color,lw=4,label=kind)
    ax.legend(frameon=False,ncol=2,loc='upper left'); ax.set_xticks([0,4,8,12,16,20,23])
    ax.set_xlabel('Departure hour (recorded local time)'); ax.set_ylabel('Trips / day')
add(2, 'When is usage highest?', usage,
    'Top weekday hours: 17:00, 18:00 and 08:00. Daily trips range from 652 (27 Sep) to 4,817 (12 Sep).',
    'Schedule peak-period resources. Low-usage days need investigation before assigning a cause.')

sh = read('station_hourly_observed_flows')
sh['hour_start']=pd.to_datetime(sh.hour_start)
sh['date']=pd.to_datetime(sh.date)
wd=sh[sh.day_type.eq('Weekday')]
trips=pd.read_csv(DATA/'cleaned_september_trips.csv',dtype={'start_station_id_resolved':'string','end_station_id_resolved':'string'})
trips['started_at_parsed']=pd.to_datetime(trips.started_at_parsed)
days=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
occ=pd.Series(pd.date_range('2026-09-01','2026-09-30').day_name()).value_counts()
heat=pd.crosstab(trips.started_at_parsed.dt.day_name(),trips.hour).reindex(days).div(occ.reindex(days),axis=0)
def weekheat(ax):
    im=ax.imshow(heat,aspect='auto',cmap='YlGnBu'); ax.set_yticks(range(7),['Mon','Tue','Wed','Thu','Fri','Sat','Sun'])
    ax.set_xticks([0,4,8,12,16,20,23]); ax.set_xlabel('Departure hour; darker = more trips per day')
add(3, 'Does the weekly pattern change?', weekheat,
    'Weekdays show morning and evening bands; weekends shift toward daytime use. Each weekday is normalized by its calendar frequency.',
    'Use separate weekday/weekend profiles. A calendar weekday does not prove a commuting trip.')

def mix(ax):
    for i,(label,share) in enumerate([('Members',M['member_share_pct']),('Electric bikes',M['electric_share_pct'])]):
        ax.barh(i,100,color='#e8eef3',height=.55); ax.barh(i,share,color=[BLUE,TEAL][i],height=.55)
        ax.text(share-2,i,f'{share:.1f}%',ha='right',va='center',color='white',weight='bold',fontsize=23)
    ax.set_yticks([0,1],['Member rides','Electric rides']); ax.invert_yaxis(); ax.set_xlim(0,100)
    ax.set_xlabel('Share of valid September-start trips (%)')
add(4, 'Who rides, and which bikes?', mix,
    'Members make 73.9% of trips; electric bikes make 59.7%. These are ride shares, not unique customer or fleet counts.',
    'Test bike-type operating costs separately. Member usage alone cannot tell us subscription revenue.')

def duration(ax):
    vals=trips.duration_min
    ax.hist(vals,bins=np.geomspace(vals.min(),vals.max(),45),color=BLUE)
    ax.set_xscale('log'); ax.axvline(vals.median(),color=ORANGE,lw=3)
    ax.set_xlabel('Trip minutes (log scale; full tail retained)'); ax.set_ylabel('Trips')
add(5, 'How long are rides?', duration,
    'Median ride: 6.40 min. Of 36 September-start rides over 24 hours, 35 have unresolved end IDs. Missingness and long durations overlap.',
    'Retain and flag the tail; test sensitivity. Endpoint distance is straight-line separation, not road distance.')

stats=read('station_summary').set_index('station_id')
def balance(ax):
    ids=list(stats.net_inflow.nsmallest(2).index)+list(stats.net_inflow.nlargest(2).index)
    s=stats.loc[ids].sort_values('net_inflow')
    ax.barh(s.station_name,s.net_inflow,color=[BLUE if x<0 else ORANGE for x in s.net_inflow])
    ax.axvline(0,color=INK,lw=1); ax.set_xlim(-300,400); ax.set_xlabel('Monthly arrivals - departures (bikes)')
    for i,v in enumerate(s.net_inflow): ax.text(v+(6 if v>0 else -6),i,f'{v:+,}',va='center',ha='left' if v>0 else 'right')
add(6, 'Which stations gain or lose bikes?', balance,
    'Oakland Ave has the largest monthly net outflow (-216); River St & 1 St has the largest net inflow (+316).',
    'Prioritize directional imbalances, alongside total station activity. A balanced month can hide busy peaks.')

raw=pd.read_csv(ROOT/'JC-202609-citibike-tripdata.csv/JC-202609-citibike-tripdata.csv')
coords=raw.groupby('end_station_id')[['end_lat','end_lng']].median().dropna()
def geography(ax):
    ax.figure.set_size_inches(6.8,4.0)
    ax.scatter(coords.end_lng,coords.end_lat,c='#b8c5cf',s=35,label='Observed destinations')
    ax.scatter(stats.lng,stats.lat,c=TEAL,s=25,label='108 JC/HB origin stations')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.legend(frameon=False,fontsize=13,loc='lower center',bbox_to_anchor=(.5,1.01))
    ax.set_aspect(1/np.cos(np.radians(40.73)))
add(7, 'Is this a closed local network?', geography,
    '108 origin stations, 222 destination IDs and 274 known September arrivals outside the local service domain. Some trips cross the boundary.',
    'Include boundary flows. This extract does not establish complete inbound coverage from other areas.')

am=read('morning_evening_reversal').set_index('station_id')
amcol=next(c for c in am if c.startswith('Morning')); pmcol=next(c for c in am if c.startswith('Evening'))
def reversal(ax):
    p=am.nlargest(3,'reversal_magnitude').iloc[::-1]; y=np.arange(len(p))
    ax.barh(y-.17,p[amcol],height=.32,color=BLUE,label='07:00-09:59')
    ax.barh(y+.17,p[pmcol],height=.32,color=ORANGE,label='16:00-18:59')
    ax.set_yticks(y,p.station_name); ax.axvline(0,color=INK,lw=1)
    ax.set_xlabel('Average net inflow per weekday (bikes)')
    ax.legend(frameon=False,ncol=2,fontsize=15,loc='lower center',bbox_to_anchor=(.5,1.01))
add(8, 'Do stations reverse direction at peaks?', reversal,
    '96 of 108 stations reverse average AM/PM net-flow sign. Grove St PATH gains 72.8 bikes in the morning, then loses 63.9 in the evening.',
    'Time redistribution around direction changes. Tiny reversals also count; compare their magnitude.')

top=stats.nlargest(6,'total_activity').index
nh=wd.groupby(['station_id','hour']).net_inflow.mean().unstack().reindex(top)
def netheat(ax):
    lim=np.abs(nh.to_numpy()).max()
    ax.imshow(nh,aspect='auto',cmap='RdBu_r',vmin=-lim,vmax=lim)
    ax.set_yticks(range(len(top)),[stats.loc[i,'station_name'] for i in top],fontsize=14)
    ax.set_xticks([0,4,8,12,16,20,23]); ax.set_xlabel('Hour; blue = net loss, red = net gain')
add(9, 'Can a monthly total hide hourly pressure?', netheat,
    'Busy stations change between gaining and losing bikes across the day. This view shows the six busiest stations, averaged over weekdays.',
    'Use station-hour inventory balances rather than a single monthly redistribution target.')

sh=sh.sort_values(['station_id','hour_start'])
sh['cumulative']=sh.groupby(['station_id','date']).net_inflow.cumsum()
def cumulative(ax):
    for sid,color in [('JC115',BLUE),('HB609',ORANGE)]:
        p=sh[sh.station_id.eq(sid)&sh.day_type.eq('Weekday')].groupby('hour').cumulative.mean()
        ax.plot(np.r_[0,p.index+1],np.r_[0,p.values],lw=4,color=color,label=stats.loc[sid,'station_name'])
    ax.axhline(0,color=INK,lw=1); ax.set_xlabel('Hour boundary (0 = midnight)'); ax.set_ylabel('Net change')
    ax.legend(frameon=False,fontsize=15,loc='upper left')
pressure=read('station_pressure_summary').set_index('station_id')
add(10, 'Where is the intraday swing greatest?', cumulative,
    'Grove St PATH has the largest mean daily cumulative swing: 78.9 bikes. A small monthly balance can still require substantial daily handling.',
    'These are customer-flow changes from zero, not actual inventories or measured shortages.')

morning=wd[wd.hour.isin([7,8,9])].groupby(['station_id','date']).net_inflow.sum()
def variability(ax):
    ids=['JC115','HB609','JC109']
    ax.boxplot([morning.loc[i].to_numpy() for i in ids],orientation='horizontal',patch_artist=True,
               boxprops={'facecolor':'#b9d6ec'},medianprops={'color':BLUE,'linewidth':3})
    ax.set_yticks([1,2,3],[stats.loc[i,'station_name'] for i in ids]); ax.set_xlabel('Morning net inflow; 22 weekdays per station')
add(11, 'How consistent are peak flows?', variability,
    'Grove St PATH gains bikes in every one of the 22 weekday mornings. Its daily morning net inflow still varies (standard deviation: 23.9 bikes).',
    'Use day scenarios and safety buffers. An average-day plan may perform poorly on individual days.')

od=read('observed_od_counts').head(3)
def routes(ax):
    labels=[f'{r.origin_name}\nto {r.destination_name}' for r in od.itertuples()]
    ax.barh(range(3),od.trips,color=TEAL); ax.set_yticks(range(3),labels,fontsize=15); ax.invert_yaxis()
    ax.set_xlim(0,520); ax.set_xlabel('Completed trips on top directed customer routes')
    for i,v in enumerate(od.trips): ax.text(v+7,i,str(v),va='center')
add(12, 'Which customer routes are busiest?', routes,
    'McGinley Square to Bergen Ave & Sip Ave leads with 440 trips; the reverse has 420. Grove St PATH to Marin Light Rail follows with 416.',
    'Customer routes reveal corridors. A truck route needs road travel times, depots, loads and shift limits.')

fm=read('forecast_baseline_metrics')
improvement=100*(1-fm.iloc[1].station_hour_MAE/fm.iloc[0].station_hour_MAE)
def forecast(ax):
    ax.barh(['Station + hour','Station + day type + hour'],fm.station_hour_MAE,color=[BLUE,TEAL])
    ax.invert_yaxis(); ax.set_xlim(0,1.2); ax.set_xlabel('Mean absolute error: bikes / station-hour (lower is better)')
    for i,v in enumerate(fm.station_hour_MAE): ax.text(v+.02,i,f'{v:.3f}',va='center')
add(13, 'Can a simple forecast support planning?', forecast,
    f'Adding weekday/weekend profiles reduces holdout MAE by {improvement:.1f}% (0.969 to 0.899). Train: 1-20 Sep; test: 21-30 Sep.',
    'Start with transparent baselines. Zeros count; peak-hour MAE is higher (1.311). One month cannot establish seasonality.')

W=1200
FONTS=Path('C:/Windows/Fonts')
def font(size,bold=False): return ImageFont.truetype(str(FONTS/('arialbd.ttf' if bold else 'arial.ttf')),size)
img=Image.new('RGB',(W,18000),'#edf3f7'); d=ImageDraw.Draw(img)
y=0
def wrap(text,face,maxwidth):
    result=[]
    for paragraph in text.split('\n'):
        line=''
        for word in paragraph.split():
            test=(line+' '+word).strip()
            if d.textlength(test,font=face)>maxwidth and line: result.append(line); line=word
            else: line=test
        result.append(line)
    return result
def text(text,x,y,size=39,color=INK,bold=False,width=1056,gap=10):
    face=font(size,bold)
    for line in wrap(text,face,width):
        d.text((x,y),line,font=face,fill=color)
        y+=size+gap
    return y

d.rectangle((0,0,W,845),fill=INK)
y=text('CITI BIKE / GROUP BRIEFING',64,55,29,'#75dacf',True)
y=text('Where do the\nbikes need to go?',64,y+20,76,'white',True)
y=text('Jersey City + Hoboken | September 2026',64,y+20,38,'#c8d9e7')
y=text('13 chart topics. The questions they answer.\nThe decisions they could support.',64,y+22,39,'white')
for x,value,label in [(64,'106,617','September-start trips'),(635,'108','local origin stations')]:
    text(value,x,618,67,'#75dacf',True,width=500)
    text(label,x,702,30,'white',width=500)
y=885
y=text('THE MAIN INSIGHT',64,y,30,TEAL,True)
y=text('Bikes move in opposite directions at different times. Monthly totals alone hide the operating challenge.',64,y+16,45,INK,True)
y=text('Read each card: question > chart > finding > OR implication. Selected views are redrawn from all 13 original EDA figure topics.',64,y+15,34,MUTED)
y+=36
card_bounds=[]
for num,q,path,finding,implication in cards:
    start=y
    # Draw content first; paste a rounded background behind it afterward.
    title_lines=wrap(q,font(44,True),970)
    plot=Image.open(path).convert('RGB'); plot=plot.resize((1072,round(plot.height*1072/plot.width)),Image.Resampling.LANCZOS)
    body_h=len(wrap(finding,font(39),1040))*49
    or_h=len(wrap('OR: '+implication,font(35),1040))*45
    h=42+len(title_lines)*54+18+plot.height+20+body_h+18+or_h+35
    d.rounded_rectangle((36,y,1164,y+h),radius=26,fill='white')
    d.rounded_rectangle((64,y+34,142,y+100),radius=12,fill=TEAL)
    text(f'{num:02}',78,y+42,34,'white',True,width=70)
    ty=text(q,164,y+35,44,INK,True,width=970)
    py=ty+18
    img.paste(plot,(64,py)); d=ImageDraw.Draw(img)
    ty=text(finding,80,py+plot.height+20,39,width=1040)
    ty=text('OR: '+implication,80,ty+18,35,TEAL,width=1040)
    card_bounds.append((start,y+h))
    y+=h+24

start=y
footer_text=[
 ('WHAT THE DATA CANNOT TELL US',35,True),
 ('Completed trips are observed usage, not all potential demand. Empty/full stations, failed rentals, starting stocks and staff moves are unobserved. Cumulative flow is not actual inventory.',39,False),
 ('WHAT WE NEED FOR A BUSINESS CASE',35,True),
 ('Bike and dock purchase costs; useful life; staff, trucks and fuel; maintenance and parts; charging; insurance/security; technology/data costs; capacities, starting stocks and billing details.',39,False),
 ('Financial reports and fare schedules can supply benchmarks. Local September costs and profit still need evidence or clearly labeled assumptions.',36,False),
 ('A FOCUSED QUESTION FOR OUR MEETING',35,True),
 ('How should a limited budget be split between redistribution, extra bikes and docks to improve peak-period service?',43,True),
 ('Compare: no moves / greedy moves / optimized moves. Use LP or network flow for transfers; integer decisions for trucks and capacity; scenarios for daily variability.',36,False),
 ('SOURCE + SCOPE',29,True),
 ('Local September trip CSV + exported EDA tables; original figures 01-13. 106,628 source rows; 11 starts outside September retained only where relevant to September arrivals. All times are recorded local clock time. No financial data are merged. Prepared 13 Nov 2026.',30,False),
]
foot_h=sum(len(wrap(t,font(s,b),1040))*(s+10)+25 for t,s,b in footer_text)+70
d.rounded_rectangle((36,y,1164,y+foot_h),radius=26,fill=INK)
y+=35
for t,s,b in footer_text:
    y=text(t,80,y,s,'#75dacf' if b else 'white',b,width=1040)+25
y+=35
assert y<18000, y
img=img.crop((0,0,W,y))
png=OUT/'CitiBike_EDA_WhatsApp_Poster.png'
jpg=OUT/'CitiBike_EDA_WhatsApp_Poster.jpg'
pdf=OUT/'CitiBike_EDA_WhatsApp_Poster.pdf'
img.save(png,optimize=True)
img.save(jpg,quality=94,subsampling=0,optimize=True)
c=canvas.Canvas(str(pdf),pagesize=(W/2,y/2))
c.setTitle('Citi Bike EDA | Jersey City + Hoboken | September 2026')
c.setAuthor('Citi Bike OR project group')
c.drawImage(ImageReader(img),0,0,width=W/2,height=y/2)
c.showPage(); c.save()
# PDF rendering is independently inspected in readable slices.
import pypdfium2 as pdfium
doc=pdfium.PdfDocument(pdf)
page=doc[0]
assert len(doc)==1
rendered=page.render(scale=1.4).to_pil()
for i,(top,bottom) in enumerate([(0,card_bounds[1][0]),(card_bounds[5][0],card_bounds[7][0]),(card_bounds[11][0],y)]):
    rendered.crop((0,round(top*.7),round(W*.7),round(bottom*.7))).save(TMP/f'review_{i+1}.png')
preview=img.copy(); preview.thumbnail((300,4000)); preview.save(TMP/'overview.png')
print(json.dumps({'width':W,'height':y,'cards':len(cards),'outputs':[str(png),str(jpg),str(pdf)]},indent=2))
