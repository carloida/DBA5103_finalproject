"""Create the team pipeline report and a 9:16 portrait poster from current manifests."""
from pathlib import Path
from datetime import datetime,timedelta
from html import escape
import csv
import json
import textwrap
from PIL import Image,ImageDraw,ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/sf_bikeshare'
SUITE=BASE/'robustness_testing'
PDFOUT=ROOT/'output/pdf'
VISUAL=BASE/'pipeline'
TMP=ROOT/'tmp/pdfs/pipeline'
for folder in [PDFOUT,VISUAL,TMP]:
    folder.mkdir(parents=True,exist_ok=True)
FONT=Path('C:/Windows/Fonts/segoeui.ttf')
BOLD=Path('C:/Windows/Fonts/segoeuib.ttf')
pdfmetrics.registerFont(TTFont('Segoe',str(FONT)))
pdfmetrics.registerFont(TTFont('SegoeBold',str(BOLD)))

def read_manifest(folder):
    return json.loads((folder/'manifest.json').read_text(encoding='utf-8'))

cases=[read_manifest(p.parent) for p in sorted(SUITE.glob('R*/manifest.json'))]
assert len(cases)==5
assert all(c['purpose']=='ROBUSTNESS TESTING ONLY' and c['validation_checks_passed']==65 for c in cases)

def date_label(interval):
    start,end=interval.strip('[]()').split(', ')
    a=datetime.fromisoformat(start)
    b=datetime.fromisoformat(end)-timedelta(days=1)
    return a.strftime('%d %b %Y')+' - '+b.strftime('%d %b %Y')

def make_package_guides():
    inventory=[]
    for case in cases:
        folder=SUITE/case['case_id']
        summary=case['summary']
        quality=summary['daily_opening_quality']
        bad=sum(r['station_days'] for r in quality if r['inventory_quality']!='valid_within_90_seconds')
        inventory.append([case['case_id'],case['city'],date_label(case['interval']),str(summary['stations']),
                          f"{summary['station_hours']:,}",str(bad)])
        text=f'''# {case['case_id']}

**ROBUSTNESS TESTING ONLY - retrospective observed-data subset**

This is a separate comparison case, not a replacement for the [main V3 SF dataset](../../model_inputs_v3/README.md).

- City: {case['city']}.
- Dates: {date_label(case['interval'])}; hourly recorded-local-clock grid.
- Stations: {summary['stations']}; station-hours: {summary['station_hours']:,}.
- First eight weeks: `training`. Final two weeks: `validation`, for retrospective policy evaluation after model/estimator choices are fixed. These dates are not a sealed holdout.
- Same 51 hourly columns and exact SQL types as V3; all 21 core table schemas match V3.
- All working physical units are metric. Currency remains USD.
- Build checks: 65 passed; portable table row-count readbacks: 18 passed.
- Unusable midnight stocks: {bad}. They remain NULL/flagged; no fallback or evaluation-day exclusion has been applied.

Use `station_hour_observed.csv.gz` as the main panel and join other exported tables at their documented keys. The original source database and local case DuckDB file are excluded from GitHub. No attempted-demand estimates, optimized policies, executable truck routes or financial gains have been produced.

## Economic inputs and limits

Historical tariffs and Jason's allocation scenarios are reference benchmarks, not measured case payments. The three fixed 2015 gasoline entries from V3 retain their reference identifiers, but their case values are deliberately NULL with the old reference values in notes. Agree a common price-year scenario or source period-matched values before economic evaluation. Truck/cost values remain unselected.

Road estimates use current default driving conditions and include snapping diagnostics. They do not establish historical congestion, truck restrictions, depot legs or route feasibility. OD/availability/initial-stock flags must be handled consistently by every evaluated policy.

See [suite instructions](../README.md), `data_dictionary.csv`, `table_inventory.csv`, `validation_checks.csv`, `case_definition.json` and `manifest.json`. The manifest records all exported-file hashes and the build rules.
'''
        (folder/'README.md').write_text(text,encoding='utf-8')
    md=['# Robustness testing datasets','','**ROBUSTNESS TESTING ONLY - separate from the main V3 SF pilot**','',
        'These five observed-data subsets implement the approved preparation request. Together with the unchanged main V3 SF pilot, they form a two-city by three-period comparison design. Preparing these files does not establish model performance or approval of every operating assumption.','',
        '| Case | City | Inclusive dates | Stations | Station-hours | Unusable midnight stocks |',
        '| --- | --- | --- | ---: | ---: | ---: |']
    for row in inventory:
        row[0]=f'[{row[0]}]({row[0]}/README.md)'
        md.append('| '+' | '.join(row)+' |')
    md += ['','The main case is [V3 SF, 9 February-19 April 2015](../model_inputs_v3/README.md): 34 stations and 57,120 rows. It is not copied into this folder.','',
           '## Same features and validation','',
           'Every case preserves the exact 51-column hourly schema and all 21 V3 core table schemas. Natural row counts differ because SF has 34 stations and San Jose has 16. Each case spans ten weeks at hourly resolution. No observations were duplicated or padded with fictional stations. All five cases passed 65 checks and 18 export row-count readbacks each: 325 build checks and 90 readbacks in total.','',
           'Missing/stale opening stocks, effective-capacity discrepancies, duration issues and DST flags are preserved. One unusable SF opening affects the later window\'s final two weeks. Agree a fallback or complete-day exclusion rule before evaluating any policy; no such exclusions have been silently applied.','',
           '## Load a case','',
           'Install `duckdb` and `pandas`, then run from the repository root:','',
           '```python','import duckdb',
           'path = "output/sf_bikeshare/robustness_testing/R1_san_jose_2015_feb_apr/station_hour_observed.csv.gz"',
           'panel = duckdb.sql(f"SELECT * FROM read_csv_auto(\'{path}\')").df()',
           'training = panel[panel["split"] == "training"].copy()',
           'evaluation = panel[panel["split"] == "validation"].copy()','```','',
           'The case DuckDB files and full source database stay local. All scoped CSV/GZIP tables needed for the observed-data handoff are included. Rebuilding from original sources requires the local source database and V3 reference schema/parameter exports.','',
           '```powershell','python sf_bikeshare/build_robustness_subsets.py --case all',
           '# If a matching road cache is absent, add --fetch-road-matrix.','```','',
           '## Intended evaluation','',
           'Fit demand using preceding training observations under one agreed method. Compare no moves, a resource-matched rule and optimized allocation with common initial stocks, demand scenarios, information and operating limits within each city-day. Check route feasibility and avoid future-information leakage. Report service, movements, km, estimated cost, solve time and failures.','',
           'The six cases provide up to 84 evaluation city-days and 252 policy-day evaluations for three policies, before exclusions, scenarios and replications. Shared dates, stations and source history make these dependent cases; they are not six independently collected systems.','',
           '## Economic scope','',
           'Historical tariffs and allocated-revenue assumptions are reference benchmarks. Case-matched gasoline values are unselected; the old V3 benchmark values remain in parameter notes. Agree a common explicit price-year scenario or obtain period-specific inputs. None of the tables establishes actual charges, marginal trip revenue or historical truck expenditure.','',
           '## Provenance and status','',
           'The original database was opened read-only. The main V3 files and producer were preserved. New San Jose road estimates were requested once and cached by station coordinates/order; the SF cache was reused. Current driving estimates do not establish historical truck operations.','',
           'Data preparation is complete. Demand estimation, final formulation, vehicle/depot decisions, policy simulation and results remain team work. See [the pipeline report](../../../docs/SF_Bikeshare_Project_Pipeline_Report.md) and the case manifests for exact build evidence.']
    (SUITE/'README.md').write_text('\n'.join(md)+'\n',encoding='utf-8')

PIPELINE=[
 ('1','Prepare and audit observations','Carlo','Main V3 plus five robustness cases; quality flags and metric units.','Prepared'),
 ('2','Estimate attempted demand','Fu Yan with Carlo','Pool matched counts/exposure; validate fallbacks and uncertainty.','Pending'),
 ('3','Agree parameters and assumptions','Jason with Joo Hee','Trip-value interpretation, vehicle inputs, costs and operating rules.','Pending'),
 ('4','Define the allocation model','Joo Hee','Inventory, bike conservation, dock bounds, transfer time and activation.','Pending'),
 ('5','Implement and compare policies','Hong Jin with Joo Hee','Start small, then compare no moves, a rule and optimized allocation.','Pending'),
 ('6','Check routes and estimated costs','Hong Jin with Joo Hee','Onboard load, handling/travel time, depot rules and cost reconciliation.','Pending'),
 ('7','Evaluate robustness','Team','Repeat the same method across cities/periods and selected scenarios.','Data prepared; experiments pending'),
 ('8','Interpret and finalize the paper','Carlo and section owners','Explain service/cost trade-offs, failures, limitations and recommendations.','Writing can start'),
]

PAGES=[
 ('Project pipeline and current status',[
  ('p','We can formally begin report writing now. The observed-data scope and a reproducible data handoff are available. We should write the background, literature, data preparation and planned methodology while the team finalizes demand, operating assumptions and formulation. Results and financial conclusions must follow actual model runs.'),
  ('h','Purpose and operational question'),
  ('p','Our main case remains 34 San Francisco stations over 9 February-19 April 2015, at hourly resolution. We ask where, when and how many bikes to redistribute to improve modeled service relative to no redistribution, within inventory, dock, timing and vehicle limits. Economic contribution is conditional on an explicitly agreed trip-value interpretation; allocated membership revenue is not automatically marginal cash revenue.'),
  ('h','Working sequence and responsibility'),
  ('table',(['Step','Work and output','Lead'],[[n,title+'. '+detail,owner] for n,title,owner,detail,status in PIPELINE],[36,329,134])),
  ('p','Demand estimation, parameter research and formulation (steps 2-4) can progress together using the fixed data schema. Hong Jin can begin small sanity instances before all empirical inputs are final. Do not present illustrative runs as observed performance.'),
 ]),
 ('Robustness design and separate datasets',[
  ('p','Five additional subsets have been prepared in a separate robustness_testing folder. With the unchanged main V3 case, they form two cities by three non-overlapping calendar windows. Every case is ten weeks long: eight weeks for estimation and two labeled validation for retrospective evaluation. Earlier EDA has examined the broader source, so these are not sealed holdouts.'),
  ('table',(['Case','City','Inclusive dates','Rows'],[
   ['D0 main','SF','9 Feb-19 Apr 2015','57,120'],
   ['R1','San Jose','9 Feb-19 Apr 2015','26,880'],
   ['R2','SF','2 Jun-10 Aug 2014','57,120'],
   ['R3','San Jose','2 Jun-10 Aug 2014','26,880'],
   ['R4','SF','20 Apr-28 Jun 2015','57,120'],
   ['R5','San Jose','20 Apr-28 Jun 2015','26,880'],],[60,78,245,116])),
  ('h','What is held consistent'),
  ('p','All five additions match the 51-column V3 hourly schema and all 21 core table schemas, including names, order and SQL types. Their station, day, OD, boundary, transit and distance tables retain the same meanings. Physical units are metric and currency is USD. SF has 34 stations and San Jose 16; natural row counts differ without changing duration or inventing observations.'),
  ('h','Build evidence and remaining data rules'),
  ('p','Each added case passed 65 checks and 18 export row-count readbacks: 325 checks and 90 readbacks overall. The original database was read-only and V3 was preserved. Current San Jose road estimates were fetched once and cached; the SF road cache was reused. These are driving proxies, not historical truck logs.'),
  ('p','Each additional SF window has four unusable midnight stocks, retained as NULL with flags; one affects the later window\'s evaluation period. San Jose midnight stocks are fresh throughout. Agree the same initialization fallback or complete-day exclusion rule before policy results are inspected. Capacity and long-trip diagnostics remain visible.'),
  ('h','What the design can establish'),
  ('p','Compare location effects within common dates and period effects within each city. The cases share dates, stations and source history, so they are dependent. Six cases is our practical design choice, not a universal minimum or proof of general validity. Demand intensity differs substantially across cities; little benefit from rebalancing can be a valid result.'),
 ]),
 ('Model construction and fair evaluation',[
  ('h','Stage 1 allocation'),
  ('p','Joo Hee defines an integer model on station-time nodes. It chooses relocations while conserving bikes, bounding station stock and docks, linking accepted customer trips to later arrivals/in-transit stock, respecting transfer timing and activating truck resources. Opening stock is a dated initial condition, not an hourly reset to the historical inventory path.'),
  ('p','The proposed allocation cost is activation plus bikes moved times handling and allocated distance cost: C1 = sum(F z) + sum[(h + k d / average_load) x]. Here h is USD per relocated bike including load/unload, k is variable USD per truck-km, and d is km. Average load is positive and distinct from onboard capacity and hourly throughput. The activation billing period must be defined.'),
  ('h','Stage 2 route checks'),
  ('p','Route the proposed movements and verify visit feasibility, onboard load, handling/setup/travel time, depot legs and end conditions. Evaluate C2 = F z + (W + V) H + P G + M D + A for consistent activated vehicle periods. Fuel litres may be approximated by G = D q / 100 with q in litres/100 km. Include each cost once; compare C2 with C1 rather than adding both as separate expenses.'),
  ('p','An infeasible route requires revised movements and reevaluation, or an explicit failure report. A TSP visit order alone is insufficient. Both costs remain estimates, and sequential optimization does not establish joint global optimality.'),
  ('h','Common comparison protocol'),
  ('p','Evaluate no redistribution, a resource-matched rule and optimized allocation on the same city-day starting stocks, in-transit bikes, request scenarios and operating limits. Moves use forecasts and information available before requests occur. Solving with the full realized future is a perfect-information benchmark, not normal operational performance. Unavailable external pickups/returns need explicit rules.'),
  ('p','Up to 14 evaluation city-days per case gives 84 city-days and 252 policy-day evaluations for three policies before exclusions, cost/demand scenarios or stochastic replications. Use paired policy differences and preserve day/week dependence. If simulations or heuristics are stochastic, choose repetitions from a variability pilot and use common scenarios/seeds where appropriate.'),
  ('p','After the base comparisons, test agreed low/base/high costs and rider values, demand stress factors and truck/handling resources. These are explicit scenario choices. Start with a small experiment budget and selected adverse combinations rather than every possible factor combination.'),
  ('h','Results to report'),
  ('p','Report additional served trips, unmet estimated requests, bikes moved, km and operating hours, estimated redistribution cost, conditional contribution, executable-route share, solve time, solver status and gaps. Normalize across city sizes and report failures. Neither stockouts nor observed trips alone measure attempted demand, and allocated fares do not establish actual profit.'),
 ]),
 ('Report writing and completion gates',[
  ('p','Yes, start formal writing now. A finished data handoff is a foundation for the paper; it does not require waiting for every experiment. Keep factual completed work separate from the methodology proposed and results still pending. There is no basis to promise that no further correction will ever be needed, but the main observed-data package can serve as the reference release.'),
  ('table',(['Paper section','Owner','Write now or finalize later'],[
    ['1 Introduction','Jason','Write the problem, motivation and observed evidence now.'],
    ['2 Literature','Jason','Write now; connect references to the actual model.'],
    ['3 Data and demand','Carlo + Fu Yan','Data/scope/QA now; complete demand method and validation after fitting.'],
    ['4 Formulation','Joo Hee','Draft now; finalize after inventory, timing, boundary and vehicle rules agree.'],
    ['5 Solution method','Joo Hee + Hong Jin','Outline now; report the solver, size, runtime and gaps actually used.'],
    ['6 Results','Hong Jin','Finalize only from reproducible baseline and optimization runs.'],
    ['7 Robustness and limits','Joo Hee + Hong Jin + Fu Yan','Write the protocol/known limits now; add measured robustness outcomes later.'],
    ['8 Conclusion','Carlo + Hong Jin','Finalize recommendations after results and sensitivity are available.'],
    ['Appendix and edit','All code owners; Carlo edits','Maintain data/model code, input register, citations and consistent notation.'],
  ],[105,105,289])),
  ('h','Decisions needed before empirical claims'),
  ('p','Fu Yan must validate the demand estimator and zero-exposure fallback. Jason/Joo Hee must agree the trip-value interpretation and numerical vehicle/cost scenarios. Joo Hee/Hong Jin must agree within-hour order, lead times, effective capacity, external-flow failures, depot/starting load, activation periods and terminal conditions. Case gasoline values are unselected; historical tariff/allocation tables remain benchmarks requiring date and geography review.'),
  ('p','The provided 10-13-page team outline fits the guideline\'s indicative 8-14 narrative pages; depth and clarity matter more than length. This brief is a coordination report, not the finished term paper. Shared Google Docs remain untouched; Carlo will relay the material manually.'),
  ('h','Evidence and reproducibility'),
  ('p','Course basis: project guideline pp. 1-4; Lecture 4 pp. 24-26 (sensitivity); Lecture 6 pp. 44-45 and 58 (time-expanded repositioning and scenario evaluation); Lecture 7 fixed-charge and routing constraints. Page references are PDF positions.'),
  ('link',('Optimization benchmarking guidance','https://arxiv.org/html/2007.03488v2')),
  ('link',('Good Laboratory Practice for Optimization Research','https://www.graham-kendall.com/papers/ketal2016.pdf')),
  ('link',('Chronological forecasting evaluation','https://otexts.com/fpp3/toolbox.html#time-series-cross-validation')),
  ('link',('GitHub data and scripts','https://github.com/carloida/DBA5103_finalproject')),
 ])
]

def make_report():
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyP',fontName='Segoe',fontSize=10.3,leading=14.1,spaceAfter=8,textColor=colors.HexColor('#182b39')))
    styles.add(ParagraphStyle(name='HeadP',fontName='SegoeBold',fontSize=18,leading=22,spaceAfter=12,textColor=colors.black))
    styles.add(ParagraphStyle(name='SubP',fontName='SegoeBold',fontSize=11.5,leading=15,spaceBefore=8,spaceAfter=6,textColor=colors.black))
    styles.add(ParagraphStyle(name='CellP',fontName='Segoe',fontSize=8.5,leading=11.1,spaceAfter=0))
    styles.add(ParagraphStyle(name='LinkP',fontName='Segoe',fontSize=8.5,leading=11,spaceAfter=3))
    story=[]
    markdown=['# Bike Share Project Pipeline and Robustness Plan','','Prepared by Carlo | 18 November 2026','']
    for page_number,(heading,items) in enumerate(PAGES):
        if page_number:
            story.append(PageBreak())
        story.append(Paragraph(escape(heading),styles['HeadP']))
        markdown += ['## '+heading,'']
        for kind,content in items:
            if kind=='p':
                story.append(Paragraph(escape(content),styles['BodyP']))
                markdown += [content,'']
            elif kind=='h':
                story.append(Paragraph(escape(content),styles['SubP']))
                markdown += ['### '+content,'']
            elif kind=='link':
                label,url=content
                story.append(Paragraph(f'<link href="{url}" color="#146c72">{escape(label)}</link>',styles['LinkP']))
                markdown += [f'[{label}]({url})','']
            elif kind=='table':
                headers,rows,widths=content
                entries=[[Paragraph(escape(str(v)),styles['CellP']) for v in row] for row in [headers]+rows]
                table=Table(entries,colWidths=widths,repeatRows=1,hAlign='LEFT')
                table.setStyle(TableStyle([
                  ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3edf0')),
                  ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#d9d9d9')),
                  ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                  ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
                  ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
                  ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7f8')])]))
                story += [table,Spacer(1,10)]
                markdown += ['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']
                markdown += ['| '+' | '.join(str(v) for v in row)+' |' for row in rows]+['']
    def footer(c,doc):
        c.saveState()
        c.setFont('Segoe',8)
        c.setFillColor(colors.HexColor('#5b6c77'))
        c.drawString(48,25,'DBA5103 | Team pipeline and robustness plan | 18 November 2026')
        c.drawRightString(A4[0]-48,25,str(doc.page))
        c.restoreState()
    dest=PDFOUT/'SF_Bikeshare_Project_Pipeline_Report.pdf'
    SimpleDocTemplate(str(dest),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=42,bottomMargin=43,
      title='Bike Share Project Pipeline and Robustness Plan',author='Carlo').build(story,onFirstPage=footer,onLaterPages=footer)
    (ROOT/'docs/SF_Bikeshare_Project_Pipeline_Report.md').write_text('\n'.join(markdown).rstrip()+'\n',encoding='utf-8')
    return dest

def make_poster():
    W,H=1800,3200
    ink='#112d40'; teal='#087f83'; muted='#4e6878'; bg='#f1f5f5'; orange='#bd6438'
    img=Image.new('RGB',(W,H),bg)
    draw=ImageDraw.Draw(img)
    def font(size,bold=False): return ImageFont.truetype(str(BOLD if bold else FONT),size)
    def wrap(text,f,maxwidth):
        lines=[];current=''
        for word in text.split():
            test=(current+' '+word).strip()
            if draw.textlength(test,font=f)<=maxwidth:
                current=test
            else:
                lines.append(current);current=word
        if current:lines.append(current)
        return lines
    def text(x,y,value,size=30,color=ink,bold=False,maxwidth=None,lineheight=None):
        f=font(size,bold)
        lines=wrap(value,f,maxwidth) if maxwidth else value.split('\n')
        for n,line in enumerate(lines):
            draw.text((x,y+n*(lineheight or int(size*1.32))),line,font=f,fill=color)
        return y+len(lines)*(lineheight or int(size*1.32))
    draw.rectangle((0,0,W,435),fill=ink)
    text(90,48,'DBA5103  /  TEAM WORKFLOW',30,'#b9dfe1',True)
    text(85,103,'Bike redistribution\nProject pipeline',88,'white',True,lineheight=105)
    text(90,337,'Main SF case + five robustness subsets',36,'#d8e9eb')
    chips=['34 SF stations','10-week windows','51-column schema','Metric + USD']
    for i,label in enumerate(chips):
        x=90+i*410
        draw.rounded_rectangle((x,458,x+390,526),radius=15,fill='white')
        text(x+18,472,label,29,teal,True)
    text(90,544,'Steps 2-4 can progress in parallel. Data is prepared; modeling is next.',27,muted)
    labels=[
      ('01  DATA - CARLO','Audit and enrich the observations','V3 SF reference plus five separate robustness cases; preserve quality flags.'),
      ('02  DEMAND - FU YAN + CARLO','Estimate requests from past data','Match trips to availability exposure. Fit on the first eight weeks.'),
      ('03  PARAMETERS - JASON + JOO HEE','Agree costs and operating assumptions','Rider value, truck resources, timing, capacity and activation; label proxies.'),
      ('04  FORMULATION - JOO HEE','Build the hourly allocation model','Conserve bikes; enforce docks, transfer lead times and truck activation.'),
      ('05  IMPLEMENTATION - HONG JIN + JOO HEE','Compare three policies fairly','No moves, a simple rule and optimized allocation; common information/resources.'),
      ('06  ROUTING - HONG JIN + JOO HEE','Check whether moves can be executed','Check loads, visit order, handling/travel time and depot legs; compare costs.'),
      ('07  ROBUSTNESS - TEAM','Repeat across cities and periods','Six total cases. Re-estimate local inputs; retain the same model and features.'),
      ('08  INTERPRETATION - CARLO + TEAM','Explain outcomes and limitations','Report service, cost, movement, feasibility and sensitivity; finalize conclusions.'),
    ]
    for n,(owner,title,body) in enumerate(labels):
        y=590+n*179
        draw.rounded_rectangle((90,y,1710,y+163),radius=20,fill='white')
        draw.rounded_rectangle((90,y,102,y+163),radius=5,fill=teal if n in [0,6] else '#b9ccd1')
        text(125,y+12,owner,25,teal,True)
        text(125,y+48,title,40,ink,True)
        end=text(125,y+102,body,29,muted,maxwidth=1535,lineheight=36)
        assert end<=y+169,(owner,end,y)
        if n<7:
            draw.line((900,y+164,900,y+178),fill='#a8bec6',width=4)
    y=2055
    draw.rounded_rectangle((90,y,1710,y+465),radius=22,fill=ink)
    text(125,y+23,'ROBUSTNESS DATA  /  FIVE ADDITIONS',34,'white',True)
    text(125,y+78,'Separate from V3. Same features; natural city sizes.',29,'#c5dcdf')
    columns=[125,910,1340]
    for x,label in zip(columns,['Inclusive dates','SF - 34 stations','SJ - 16 stations']):
        text(x,y+137,label,28,'#b2d7d9',True)
    table=[('2 Jun-10 Aug 2014','57,120','26,880'),('9 Feb-19 Apr 2015','57,120 MAIN','26,880'),('20 Apr-28 Jun 2015','57,120','26,880')]
    for i,row in enumerate(table):
        yy=y+196+i*68
        draw.line((125,yy-10,1670,yy-10),fill='#3c5668',width=1)
        for x,label in zip(columns,row):
            text(x,yy,label,31,'white',i==1)
    text(125,y+408,'Values are station-hour rows. 8 weeks estimation + 2 weeks evaluation.',27,'#c5dcdf')
    draw.rounded_rectangle((90,2560,1710,2930),radius=22,fill='#e0eeeb')
    text(125,2586,'YES - START REPORT WRITING NOW',38,teal,True)
    text(125,2657,'Write now: background, literature, data preparation and the planned methodology.',33,ink,maxwidth=1535,lineheight=43)
    text(125,2764,'Finalize later: fitted demand, agreed model/cost assumptions, results and conclusions.',33,ink,maxwidth=1535,lineheight=43)
    text(125,2870,'Do not turn prepared inputs into claims of service or profit gains.',28,muted)
    text(90,2970,'Prepared data: 5 cases, 325 checks and 90 export readbacks.',29,teal,True)
    text(90,3020,'Route feasibility, demand validation and policy experiments are still pending.',27,muted)
    text(90,3072,'github.com/carloida/DBA5103_finalproject',28,ink,True)
    text(90,3130,'Prepared 18 November 2026  /  Carlo  /  Portrait 9:16',25,muted)
    png=VISUAL/'SF_Bikeshare_Project_Pipeline_Poster.png'
    img.save(png,optimize=True)
    pdf=PDFOUT/'SF_Bikeshare_Project_Pipeline_Poster.pdf'
    c=canvas.Canvas(str(pdf),pagesize=(540,960))
    c.setTitle('SF Bike Share Project Pipeline Portrait Poster')
    c.setAuthor('Carlo')
    c.drawImage(str(png),0,0,width=540,height=960)
    c.showPage();c.save()
    return png,pdf

if __name__=='__main__':
    make_package_guides()
    report=make_report()
    poster,poster_pdf=make_poster()
    print(json.dumps(dict(report=str(report),poster=str(poster),poster_pdf=str(poster_pdf)),indent=2))
