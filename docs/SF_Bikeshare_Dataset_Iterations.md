# SF Bike Share: dataset progression and V3 handoff

Prepared 18 November 2026. The labels below describe the analytical progression; they are not historical Git tags. V1 and V2 already existed. V3 was built in response to the teammates' comments. V4 and V5 are planned, not completed datasets.

## Progression table

| Version | Scope / grain | What changed | What it supports | Status / owner |
| --- | --- | --- | --- | --- |
| **V1 - complete Bay Area data** | 70 stations, 5 cities; 29 Aug 2013-31 Aug 2015 trip starts; 669,959 completed trips, 71,984,434 status snapshots, 3,665 weather location-days | Typed/audited station, trip, status and weather tables; linked hourly exposure and EDA | Full-system quality audit, context, subset selection and later sensitivity history | Existing; Carlo. Raw sources and full database remain local |
| **V2 - SF pilot** | 34 fixed SF stations; 9 Feb-19 Apr 2015; hourly; 57,120 station-hours | Restricted geography and dates; summarized pickups, returns, availability and weather; retained zero-count hours and boundary endpoints; eight training weeks plus two exploratory validation weeks | Manageable observed panel for focused EDA and demand-estimation inputs | Existing scope approved by Joohee in supplied comments; original Parquet preserved |
| **V3 - enriched SF model inputs** | Same 34 stations/dates; station-hour, station-day, OD-hour, station-pair and parameter tables | Added Subscriber/Customer flows, opening snapshots, capacity diagnostics, internal/external OD flows, transit-boundary records, directed road distance/time, historical tariff evidence and separately labeled revenue scenarios; metric working units | Carlo's handoff to Fu Yan, Joohee, Jason and Hong Jin | **Built locally on 18 Nov**; 21 database tables, 43 reconciliation checks, 18 CSV/GZIP export row-count readbacks |
| **V4 - demand and agreed parameters** | Training-derived attempted-demand estimates/scenarios plus agreed operating inputs | Fu Yan estimates/validates demand; Jason/Joohee agree trip-value interpretation, vehicle/cost inputs; team specifies capacity, timing, boundary and horizon rules | Formulation and reproducible optimization inputs | Planned. Not yet fitted or agreed |
| **V5 - policy and route results** | Policy/day/route/scenario results | Compare no moves, a rule and optimized transfers; evaluate routes, costs, service and sensitivities under common conditions | Results, limitations and recommendations | Planned; Hong Jin/Joohee with team inputs. Outputs are not new observed data |

The complete source has **35 listed SF stations**; the pilot has 34 because of the fixed installation-date cohort rule. Filtering full-history trips to at least one SF endpoint gives 603,733 journeys. That is an intermediate queryable selection, not a previously published standalone release. V2 also narrows dates and aggregates time; its smaller file is not simply a deletion of other cities.

The V2 package's 63,974 relevant journeys are counted once when at least one cohort endpoint occurs in the window. V3 keeps those plus one flagged horizon-spanning journey for transit review. The station-hour endpoint counts remain identical to V2.

V3 measurements now use kilometres/metres, degrees Celsius, kilometres/hour, millimetres, litres, USD/litre and USD/km. Fuel-consumption assumptions use litres/100 km. Metric weather fields replace the original-unit fields in V3; the original V1/V2 sources are preserved. Road estimates and tariff evidence were newly integrated externally, gasoline proxies were carried from earlier EIA research, and Jason's trip-frequency assumptions remain separately labeled team inputs.

## How V3 responds to the comments

The latest Joohee/Fu Yan comments were supplied by Carlo in this conversation. Jason's exact frequency scenarios and Fu Yan's earlier multi-stop cost note were read in the [shared project document](https://docs.google.com/document/d/12mtigIDA4NQ2ycOh-fxOVmE1-lP0h9YF6kfvWXMp1z0/edit). No Google Doc was edited; Carlo will upload information manually.

| Comment / requirement | Local V3 response | Remaining responsibility |
| --- | --- | --- |
| Joohee approves 34 SF stations, 10 weeks, hourly | Same station/date/hour grid; original training/validation labels retained | Later policy-evaluation dates still need agreement |
| Joohee input 2: Subscriber/Customer pickups and returns | Dense rider-split hourly panel. Pickups: 55,179 Subscriber + 7,064 Customer. Returns: 55,234 Subscriber + 7,092 Customer | Fu Yan estimates attempted demand; observed counts remain observations |
| Joohee input 3: latitude/longitude and distances | 34 coordinates plus 1,156 directed road/air pairs, including diagonal pairs | Review current driving profile, depot location and historical/truck limitations |
| Joohee input 4: opening inventory and dock capacity | 2,380 valid midnight opening snapshots, with time/age; listed docks and station-level status diagnostics | Joohee/Carlo agree physical versus effective-capacity assumptions |
| Joohee: outside-cohort trips as fixed inflows/outflows | Dense external flows and OD records preserve both endpoint times; 1,647 external departures and 1,729 external arrivals | Joohee defines shortages, blocked returns and other feasibility rules |
| Joohee Stage 1: per-bike handling + allocated distance, fixed activation | Distance matrix and explicit cost/load/activation parameter register | Jason/Joohee set defensible values and activation period; no invented rates |
| Joohee Stage 2: route the movements and compare costs | Directed road distance/time with provenance and snapping diagnostics | Hong Jin/Joohee check route/load/time/depot feasibility; estimated route cost is not actual operator expenditure |
| Jason: historical membership/pass pricing, frequency assumptions, low/base/high estimates | Historical tariff table and six proposed allocated-revenue scenarios | Jason/Joohee review plan mix and economic interpretation; allocation is not incremental cash revenue |
| Fu Yan: does the original data contain charges; could regression recover a duration-based scheme? | Confirms no charge/payment field. Added official historical duration-fee schedule as external evidence | Charge regression cannot be fitted without charges; do not reconstruct actual bills from trip duration alone |
| Fu Yan: multi-stop truck operation and TSP extension | Current road matrix and separate vehicle/handling/stop/depot requirements | Singapore truck observation and earlier AI-generated dollar values are not calibrated SF inputs |
| Shared notes: demand estimation from valid availability | Class-specific numerators matched to the same short-gap intervals as availability denominators | Fu Yan pools training estimates, handles zero exposure and validates assumptions |

The machine-readable [requirements table](../output/sf_bikeshare/model_inputs_v3/teammate_requirements.csv) records 12 separate entries and their statuses. The [handoff guide](../output/sf_bikeshare/model_inputs_v3/README.md) describes every input and its limitations.

## Material findings from the enrichment

1. **Opening stocks are available.** All 2,380 midnight stocks are fresh within 90 seconds. No initial-bike assumption was substituted. They are historical initial states, not a no-rebalancing trajectory.
2. **Capacity needs an explicit interpretation.** All 34 listed dock counts equal their modal/maximum valid status totals, but lower totals occur in 177,539 of 3,424,038 snapshots. There are 67 midnight mismatches. These can reflect effective availability and do not prove physical docks changed.
3. **DST affects hourly snapshots.** The 34 stale hourly openings occur at 03:00 on 8 March 2015. They remain NULL/flagged rather than being imputed from the future. Recorded-clock/DST ambiguity remains visible.
4. **Transit records reveal an extreme-duration case.** One December-to-June trip spans the whole pilot and is flagged long/inconsistent. OD/transit tables preserve flags for a retain/exclude sensitivity. V3 has 14 long records including this supplement; V2's endpoint-relevant 13 have not changed.
5. **Road distances are directional estimates.** All pairs are available; maximum snapping displacement is about 61.9 m. The current default driving model is not a historical truck route. Depot legs are still unspecified.
6. **Historical pricing evidence is stronger, but billing remains absent.** The SFMTA board supplies the 30-minute surcharge structure; an April 2015 Air District release corroborates pass prices and adds a trial plan absent from the simple annual/day allocation. The actual release is dated 16 April despite its filename. The source date and applicability assumptions are recorded explicitly.

## Immediate handoff and remaining work

Carlo can hand off V3 now and finalize the focused observed-data EDA using these reconciled tables. This does not require waiting for all financial assumptions. The remaining work belongs to V4: Fu Yan's demand estimates, Jason's defensible costs/value assumptions and Joohee's inventory/timing/vehicle rules. Hong Jin can start a small implementation against the V3 schema while those parameters are finalized.

The full raw data, original database and V2 file remain intact. V3 is a separate local database with compact scoped exports. No optimized plan, measured missed demand or profit improvement has been generated.
