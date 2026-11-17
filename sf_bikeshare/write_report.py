"""Write matching Markdown and PDF reports from the verified EDA results."""
from pathlib import Path
from xml.sax.saxutils import escape
import json
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4

def write_report(m,figure_notes,out):
    out=Path(out)
    q=pd.read_csv(out/'status_quality.csv').iloc[0]
    key=pd.read_csv(out/'key_audit.csv')
    coverage=pd.read_csv(out/'coverage_sensitivity.csv')
    gap=pd.read_csv(out/'gap_tolerance_sensitivity.csv')
    weather=pd.read_csv(out/'weather_regression.csv')
    inference=m['weekday_inference']; rain=m['weather_regression']
    priority=pd.read_csv(out/'station_priority_evidence.csv').nlargest(5,'unavailable_pct')
    name_changes=pd.read_csv(out/'station_name_changes.csv')
    duplicate=pd.read_csv(out/'status_duplicate_keys.csv')
    bike_audit=pd.read_csv(out/'bike_sequence_audit.csv').iloc[0]
    availability_ci=pd.read_csv(out/'availability_block_intervals.csv')
    forecast=pd.read_csv(out/'forecast_metrics.csv')
    def compact(df,columns=None):
        df=df if columns is None else df[columns]
        return [[str(c).replace('_',' ') for c in df.columns]]+[[f'{v:,.0f}' if isinstance(v,float) and v.is_integer() else f'{v:,.2f}' if isinstance(v,float) else str(v) for v in row] for row in df.itertuples(index=False,name=None)]
    sections=[]
    def section(title,paragraphs,table=None,figure=None,caption=None):
        sections.append({'title':title,'paragraphs':paragraphs,'table':table,'figure':figure,'caption':caption})
    section('1. What this dataset lets the team study',[
        'Working project: compare no bicycle redistribution, a rule-based/greedy policy and an optimized policy under the same operating assumptions. This report assesses the data needed for that comparison; no optimization has been solved.',
        f'The supplied four CSV files contain {m["valid_trips"]:,} completed trips, {m["stations"]} stations, {m["bicycles"]} observed bicycle identifiers, {m["status_rows"]:,} status snapshots and {m["weather_rows"]:,} weather location-days. Trip starts run from {m["start"]} to {m["end"]}.',
        'Compared with the Jersey City Citi Bike file, this is a material improvement: it supplies historical available-bike/free-dock observations, a static station-capacity field, bicycle IDs and daily weather. It does not directly supply unsuccessful customer requests, staff movements, procurement, maintenance, fare transactions, revenue or profit.',
        f'Subscriber rides account for {m["subscriber_share_pct"]:.1f}% of completed trips. Median reported duration is {m["median_duration_minutes"]:.2f} minutes. Stations are empty for {m["empty_pct"]:.2f}% and full for {m["full_pct"]:.2f}% of valid observed time under the bounded interval rule.',
        'Recommended direction: retain the redistribution topic and use one city or a small station subset for an initial model, subject to the coverage and capacity audit. Use observed availability to diagnose service exposure; estimate latent demand separately. Present economics as a transparent scenario study until system- and period-matched financial inputs are available.',
    ],table=[['Question','Assessment'],['Can files be linked?','Yes, using audited IDs and an explicit weather mapping.'],['Can stock constraints be studied?','Yes, with coverage and capacity qualifications.'],['Are unfulfilled orders observed?','No. Only availability and completed trips are observed.'],['Are costs, revenue and profit observed?','No. These financial gaps remain.']])
    section('2. Database design and safe joins',[
        'station_id identifies station rows. trip_id identifies rides; start_station_id and end_station_id separately reference station. bike_id identifies the observed-bike dimension. The logical status key is (station_id, observed_at). Weather is keyed by (weather_zip_code, weather_date).',
        f'All {m["raw_trip_rows"]:,} trip IDs are unique and every trip endpoint matches station. The full status scan found {len(duplicate):,} repeated composite-key groups. Any identical copies are collapsed for exposure analysis; conflicting states sharing a key are quarantined. Inspect the saved audit rather than assuming a key from column names.',
        'The trip postal field is retained as rider_zip_code. It is not the station location and must not be joined to weather. An explicit analyst mapping links each city to one available weather location; this is a city-level proxy, not a source-provided station ZIP or proof of local microclimate.',
        'Aggregate trip events and status exposure to a shared station-hour before joining facts. Joining trips and snapshots on station alone would multiply rows. Weather joins use city mapping plus date and are checked as many-to-one.',
        'The delivered DuckDB database contains full raw status data, normalized small tables and derived panels. Small-table unique indexes enforce uniqueness; the raw status composite key is fully audited rather than indexed with a large primary-key structure. Foreign-key relationships are checked by anti-joins; they are logical/audited relationships rather than declared foreign-key constraints.',
    ],table=compact(key[['table_name','rows','distinct_keys']]),figure='02_database_relationships.png',caption='Logical relationships. Two trip endpoints refer to the same station dimension; weather requires a city/date proxy.')
    section('3. Data quality that changes the modeling assumptions',[
        f'The raw status table contains {int(q.parse_or_missing):,} missing/unparseable records, {int(q.unknown_stations):,} unknown station references and {int(q.negative_counts):,} negative-count records. States with no available bikes and no free docks occur in {int(q.both_zero):,} records; these are not classified as both rental stockouts and full-station return failures.',
        f'There are {int(q.static_capacity_mismatches):,} snapshots where available bikes plus free docks differs from static dock_count. Differences may reflect disabled docks/bikes, capacity changes, maintenance, inconsistent records or other operational effects. They do not uniquely reveal the cause. The static table is not a time-varying physical-capacity history.',
        f'Across the installation-based reference calendar, {m["status_coverage_pct"]:.2f}% of station-hours are covered by valid short-gap intervals. Absence can reflect missing capture, outages, installation/retirement or other causes. It is not evidence of either service availability or zero demand.',
        'The primary exposure calculation carries the previous state only to the next valid observation if the gap is positive and at most 90 seconds. Intervals are split at hour boundaries. Gaps over 90 seconds and final unpaired observations contribute no inferred duration. Long gaps are never forward-filled.',
        f'Trip duration is reported in seconds but endpoint timestamps have minute precision. {m["duration_clock_mismatches"]:,} rides differ by over 60 seconds between the two measures. {m["long_trips"]:,} rides exceed 24 hours and are retained with a review flag. {len(name_changes):,} station IDs have start-name aliases or a mismatch with the station display name. Identifier joins take precedence over name joins.',
        f'Bicycle sequences contain {int(bike_audit.overlap_over_1min):,} overlapping consecutive-trip pairs beyond one minute and {int(bike_audit.station_discontinuities):,} cases where the next origin differs from the previous destination. These suggest identifier/timing issues or unrecorded movement, but do not establish staff relocation counts, truck routes or maintenance events.',
        f'Weather contains {m["trace_weather_rows"]} trace-precipitation entries (T). The main measurable-rain rule treats T as below the measurement threshold, retains a trace flag and repeats the regression with trace counted as rain. Blank events is not automatically treated as a weather outage.',
    ],figure='08_status_coverage_and_capacity.png',caption='Coverage and capacity diagnostics use the entire status file. A recorded static dock count is not automatically a reliable historical constraint.')
    section('4. Usage patterns and operational implications',[
        'Daily/monthly counts show system usage over the observed period. Boundary dates are partial or potentially incomplete. Seasonality, station additions, holidays and changes in operation can all affect these counts; a trend plot does not identify their separate effects.',
        'Weekday and weekend profiles are normalized by calendar-day frequency. The three highest average weekday departure hours are '+', '.join(f'{h:02}:00' for h in m['top_weekday_hours'])+'. This supports explicit peak-period analysis while leaving trip purpose unobserved.',
        f'{m["reversal_stations"]} of {m["stations"]} stations reverse the sign of average morning versus evening customer net flow. Small reversals count. Net flow uses departures and arrivals at their own timestamps; it is not actual station inventory because staff actions and unavailable equipment also matter.',
        'City and OD patterns provide a practical way to choose a pilot region. Customer corridors do not determine a redistribution truck route: that decision still needs road travel times, depots, truck capacity and shifts. Cross-city operations may introduce substantial dead travel.',
        'Bicycle IDs support usage counts and follow-on sequence audits. They do not reveal the age of the fleet, maintenance intervals, the owner of a repair cost or how frequently the same customer rides. A large subscriber ride share cannot establish the number or value of paid memberships.',
    ],figure='06_station_activity_and_reversal.png',caption='Activity and directional reversals identify where time-dependent transfers may be useful. All quantities are based on completed customer movements.')
    section('5. Availability exposure and what it does not measure',[
        f'Primary results: {m["observed_station_hours"]:,.1f} valid observed station-hours; empty exposure {m["empty_pct"]:.3f}%; full exposure {m["full_pct"]:.3f}%. Rates weight time correctly rather than averaging station percentages or counting duplicate snapshots as additional independent evidence.',
        'A positive exposure share establishes that a station was recorded without a rentable bike or a return dock during valid observed intervals. It does not reveal whether any customer arrived then, whether a customer used a neighboring station, or how much money the operator lost.',
        'The exposure-only problem is identifiable from status; the number of failed orders is not. A later demand model can estimate lost rentals as expected attempted rentals during empty intervals and failed returns during full intervals. This requires assumptions about arrival rates, censoring, nearby substitution and operator interventions. Validate any such model using artificial censoring or other observable benchmarks.',
        'The reported block intervals resample complete seven-day blocks of system-day numerator/denominator totals. Stations remain together within days, preserving common shocks. These intervals characterize historical process variability under the block assumptions, not measurement errors or proof that missing status periods are representative.',
        'Repeat exposure analysis under 50%, 75% and 90% daily coverage screens and 60/75/90/120-second gap rules. Changes in results and denominators are substantive sensitivity findings, not reasons to select the most favorable policy outcome.',
    ],table=compact(availability_ci[['measure','pct','ci_low','ci_high']]),figure='09_empty_full_exposure.png',caption='Denominator: valid observed time. Empty/full exposure must not be relabeled lost-customer percentages.')
    section('6. Inferential findings and their limits',[
        f'Weekday comparison: use a fixed cohort of {inference["cohort_stations"]} SF stations installed by the first trip day. Exclude the file boundary dates and pair each complete week\'s mean weekday count with its mean weekend count. Across {inference["complete_weeks"]} full weeks, the mean difference is {inference["mean_difference"]:.1f} completed trips/day. A 2,000-replicate contiguous four-week moving-block bootstrap gives a 95% interval of {inference["ci_low"]:.1f} to {inference["ci_high"]:.1f}.',
        f'Weather model: OLS of log(1 + daily completed SF-cohort trips), using {int(rain["days"])} days and {int(rain["rain_days"])} measurable-rain days. Controls are weekday, calendar month, year, linear time trend, mean temperature and wind. A 28-lag Bartlett/Newey-West HAC covariance yields a rain association of {rain["rain_association_pct"]:+.1f}% in trips+1, with an asymptotic 95% interval of {rain["ci_low_pct"]:+.1f}% to {rain["ci_high_pct"]:+.1f}%.',
        'The transformed percentage describes the conditional geometric mean of trips+1. It is an approximate count comparison for large counts, not an estimated causal price/demand elasticity. Weekday schedules, rain and existing service are not randomized. Holiday effects, changes in travel behavior, outages and other omitted factors may remain.',
        'The block bootstrap does not assume individual trips or minute snapshots are independent. Nevertheless, finite-period nonstationarity and correlation longer than the chosen blocks can affect coverage. HAC results are also model- and lag-dependent; the saved 7- versus 28-day and trace-rain sensitivities expose some of this uncertainty.',
        'All comparisons are exploratory. No multiple-testing-adjusted confirmatory claim or p-value threshold is used. The data describe this historical system; transfer to present-day Citi Bike or other cities requires new evidence.',
    ],figure='13_weather_association.png',caption='Raw weather differences are confounded. Adjusted intervals and sensitivity checks help quantify an association without making it causal.')
    section('7. Financial gaps and the business-case boundary',[
        'Cost and revenue gaps from Citi Bike remain largely open. These four files have no purchase prices, useful lives, wages, labor schedules, loading times, truck costs, maintenance work orders, part replacements, theft/loss valuations, insurance/security or platform/connectivity expenses.',
        'subscription_type is a usage category, not a billing account. There are no actual charges, subscriber identifiers, passes, discounts, refunds, taxes, sponsorship or subsidy ledgers. Duration plus a public tariff cannot reconstruct realized revenue without account-level rules and applicable historical rates. Current NYC/NJ Citi Bike prices must not be treated as 2013-2015 SF fares.',
        'Collect period- and system-matched operator reports, procurement records or published research assumptions. Record each parameter\'s unit, source, scope and uncertainty. If unavailable, use clearly labeled low/base/high ranges; the accompanying input template deliberately contains no invented dollar values.',
        'Keep perspectives separate. Customer fares are operator revenue and a transfer in a combined social-cost view. Do not count them twice. Distinguish capex, depreciation and cash operating expenses; when estimating incremental policy value, avoid allocating all fixed overhead as if it were a marginal relocation cost.',
        'A credible first business case can compare how much modeled service exposure/target shortfall changes per relocation budget. A profit or ROI claim needs additional evidence linking served demand to incremental contribution, while retaining membership and capital-accounting assumptions.',
    ],table=[['Input','Current evidence'],['Inventory / docks','Observed status and static station counts; temporal gaps remain.'],['Failed rental / return counts','Not observed; requires a censored-demand model.'],['Relocation labor / trucks / routes','Not observed; use evidence or labeled scenarios.'],['Bike/dock capex and maintenance','Not observed; procurement/work-order data needed.'],['Customer payments / memberships','No transactions or unique subscription accounts.'],['Revenue / contribution / profit','Unavailable without additional financial evidence.']])
    section('8. Recommended OR scope and evaluation design',[
        'Start with one city and a documented station subset. Prefer periods with high status coverage and review effective versus listed capacity before selecting capacity values. Choose a clear horizon: opening allocation or a small number of peak-window transfers. Document which snapshots initialize the plan and what earlier evidence supplies forecasts.',
        'A defensible first LP decides simultaneous transfers x_ij >= 0 and target shortfalls s_i >= 0. Given observed/assumed opening stock I_i, reviewed capacity C_i and training-derived target b_i: J_i = I_i + inbound transfers - outbound transfers; 0 <= J_i <= C_i; J_i + s_i >= b_i; outbound transfers <= I_i; total relocated bikes <= B. Minimize transfer cost plus a shortfall penalty.',
        'Here s_i is target shortfall, not measured unmet demand. Targets must be checked against capacities. A time-expanded extension uses hourly stock conservation and transfer lead times. If rental/return service is simulated, connect OD demand, travel lags, accepted rentals/returns and boundary flows so that the same customer trip does not create or destroy bicycles.',
        'Compare no moves, a budget-matched greedy rule and optimized moves using identical initial states, capacities, transfer costs, information and uncertainty scenarios. Train targets and any latent-demand model on earlier days; keep later days unseen. Use paired day/week comparisons and block intervals for policy differences.',
        f'The exploratory forecast holds out the final 60 calendar days from {m["forecast_cutoff"]}. Station+hour MAE is {forecast.MAE.iloc[0]:.3f}; adding day type gives {forecast.MAE.iloc[1]:.3f}. Peak errors are {forecast.peak_MAE.iloc[0]:.3f} and {forecast.peak_MAE.iloc[1]:.3f}. These forecast results do not establish an improvement from redistribution.',
        'Sensitivity priorities: relocation cost and budget, starting stock, capacity interpretation, coverage/gap rules, demand censoring/substitution and travel/loading times. Add binary truck decisions or routing only after the basic service and data definitions are stable. Report solver status, bounds/gaps where relevant, runtime and limitations.',
    ],table=[['Claim we can make now','Claim requiring more work'],['Availability is sometimes constrained.','How many requests failed or how much profit was lost.'],['Usage has directional and calendar structure.','That a particular plan causes better service.'],['Transparent forecasting baselines are testable.','That a policy earns a positive ROI.']])
    section('9. Sources, reproducibility and review checklist',[
        'Empirical source: the four supplied local CSV files. Full source SHA-256 hashes, byte counts, build signature and software versions are in source_manifest.json. All empirical numbers in this report are computed locally; no external operating or financial observations were merged.',
        'Dataset description: Ben Hamner, SF Bay Area Bike Share, Kaggle. The publisher describes a transformed Bay Area Bike Share open dataset. Original source rows remain unchanged. The relational audit and bounded time intervals are implemented in the delivered Python builders.',
        'Relevant methodological evidence: Liu, X. and Pelechrinis, K. (2021), Excess demand prediction for bike sharing systems, PLOS ONE 16(6), e0252894, https://pmc.ncbi.nlm.nih.gov/articles/PMC8211247/. The paper distinguishes observed trip/status information from unrecorded excess demand and proposes an estimation method. It motivates a possible later model; that method is not fitted here.',
        'Dataset link: https://www.kaggle.com/datasets/benhamner/sf-bay-area-bike-share. Source and method pages were checked on 15 November 2026. Weather-city mapping is an explicit analyst proxy and should be reviewed before a station-level weather model is used.',
        'Course connection: transportation/network flow for transfers; LP duality and sensitivity for resource values; time-expanded networks for delayed movements and inventories; integer programming for indivisible trucks or capacity; scenarios for uncertain flows. The supplied project guideline requires a clear problem, mathematical model, methodology, interpretation, references and code appendix. This EDA is preparatory evidence, not the completed term paper.',
        'Review checklist before modeling: inspect duplicate/conflicting keys, capacity ranges and monthly gaps; choose the modeling region and dates; verify the weather proxy; define lost-demand assumptions; collect or label costs; freeze a chronological holdout; and agree on identical policy information and budgets.',
        'Deliverables: executable EDA script and executed notebook; full local DuckDB database; SQL schema and relationship guide; 14 figures with question/caption index; cleaning, coverage, exposure, regression and forecast tables; financial-input template; this report in Markdown and PDF. Database files and raw 2 GB CSVs are kept out of Git by default.',
    ])

    title='SF Bay Area Bike Share: EDA, inferential findings and data gaps'
    markdown=['# '+title,'','Prepared 15 November 2026. Historical observations: August 2013-August 2015.','']
    for s in sections:
        markdown+=['## '+s['title'],'']
        for p in s['paragraphs']: markdown += [p,'']
        if s['table']:
            table=s['table'];markdown+=['| '+' | '.join(table[0])+' |','| '+' | '.join(['---']*len(table[0]))+' |']
            markdown += ['| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in table[1:]];markdown+=['']
        if s['figure']: markdown += [f'Related chart: [{s["caption"]}](figures/{s["figure"]})','']
    markdown+=['## All chart questions','']
    for n in figure_notes:markdown += [f'### {n["question"]}',n['interpretation'],f'![{n["question"]}](figures/{n["figure"]})','']
    (out/'SF_Bikeshare_Inferential_Report.md').write_text('\n'.join(markdown),encoding='utf-8')
    (out/'report_sections.json').write_text(json.dumps(sections,indent=2),encoding='utf-8')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodySF',fontName='Times-Roman',fontSize=11.5,leading=15.8,spaceAfter=10))
    styles.add(ParagraphStyle(name='TitleSF',fontName='Helvetica-Bold',fontSize=20,leading=24,textColor=colors.HexColor('#132e43'),spaceAfter=14))
    styles.add(ParagraphStyle(name='SectionSF',fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=colors.HexColor('#008b81'),spaceAfter=14))
    styles.add(ParagraphStyle(name='SmallSF',fontName='Helvetica',fontSize=8.8,leading=11.5,textColor=colors.HexColor('#50677a'),spaceAfter=9))
    styles.add(ParagraphStyle(name='CellSF',fontName='Helvetica',fontSize=8.8,leading=11))
    page_w,page_h=A4; usable=page_w-144
    # Dedicated compact report graphics retain readable labels at page width.
    # All 14 larger EDA panels remain available separately and in the notebook.
    import matplotlib.pyplot as plt
    chart_dir=out/'report_charts';chart_dir.mkdir(exist_ok=True)
    weekly=pd.read_csv(out/'weekly_paired_comparison.csv')
    with plt.rc_context({'font.size':11,'axes.titlesize':12,'axes.labelsize':11}):
        fig,ax=plt.subplots(figsize=(6.2,2.65))
        values=[weekly.weekday_mean.mean(),weekly.weekend_mean.mean()]
        bars=ax.bar(['Weekdays','Weekends'],values,color=['#2568ad','#dc942c'],width=.5)
        for bar,value in zip(bars,values):
            ax.text(bar.get_x()+bar.get_width()/2,value+12,f'{value:,.0f}',ha='center',fontsize=12)
        ax.set_ylim(0,max(values)*1.2)
        ax.set(ylabel='Mean completed trips / day',title=f'Fixed {inference["cohort_stations"]}-station San Francisco cohort')
        fig.tight_layout();fig.savefig(chart_dir/'weekday_weekend.png',dpi=160);plt.close(fig)
        fig,ax=plt.subplots(figsize=(6.2,2.65))
        ax.errorbar(availability_ci.pct,[0,1],xerr=[availability_ci.pct-availability_ci.ci_low,availability_ci.ci_high-availability_ci.pct],fmt='o',color='#008b81',capsize=6)
        ax.set_yticks([0,1],['Empty: no bikes','Full: no free docks'])
        ax.set_ylim(-.6,1.6);ax.set_xlim(.35,.85)
        ax.set(xlabel='% of valid observed time',title='95% intervals from seven-day moving blocks')
        fig.tight_layout();fig.savefig(chart_dir/'availability_intervals.png',dpi=160);plt.close(fig)
    pdf_figures={3:(chart_dir/'weekday_weekend.png','Paired weekly means for a fixed SF station cohort; these are completed-trip counts.'),
                 4:(chart_dir/'availability_intervals.png','These uncertainty intervals do not correct missing data or count customers turned away.')}
    story=[]
    for i,s in enumerate(sections):
        if i:story.append(PageBreak())
        if i==0:
            story.append(Paragraph(escape(title),styles['TitleSF']))
            story.append(Paragraph('Prepared 15 November 2026 | DBA5103 project draft | Source period: 2013-2015',styles['SmallSF']))
        story.append(Paragraph(escape(s['title']),styles['SectionSF']))
        for p in s['paragraphs']:story.append(Paragraph(escape(p),styles['BodySF']))
        if s['table']:
            table=s['table'];cells=[[Paragraph(escape(str(v)),styles['CellSF']) for v in row] for row in table]
            widths=[usable/len(table[0])]*len(table[0])
            if len(table[0])==2:widths=[usable*.34,usable*.66]
            obj=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
            obj.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7f1f7')),
              ('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),
              ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#008b81')),
              ('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#d8e2e8'))]))
            story += [Spacer(1,4),obj,Spacer(1,10)]
        # All 14 full-size figures are available in the notebook and Markdown report.
        # Only compact figures on shorter pages are included here to keep the PDF readable.
        if s['figure'] and i in [3,4]:
            from PIL import Image as PILImage
            plot,caption=pdf_figures[i]
            with PILImage.open(plot) as im:w,h=im.size
            story.append(Image(str(plot),width=usable,height=usable*h/w))
            story.append(Paragraph(escape(caption),styles['SmallSF']))
    pdf=out/'SF_Bikeshare_Inferential_Report.pdf'
    def footer(canvas,doc):
        canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#50677a'))
        canvas.drawString(72,37,'SF Bay Area Bike Share | EDA and inferential report | 15 Nov 2026')
        canvas.drawRightString(page_w-72,37,str(doc.page));canvas.restoreState()
    SimpleDocTemplate(str(pdf),pagesize=A4,leftMargin=72,rightMargin=72,topMargin=54,bottomMargin=58,
                      title=title,author='DBA5103 project group').build(story,onFirstPage=footer,onLaterPages=footer)
    print(f'Report saved: {pdf}',flush=True)
