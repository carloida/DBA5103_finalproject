# Model-input handoff - 20 November 2026

**Data release preserved | Cost benchmarks provisional | Demand and model checks pending**

Carlo will have limited/no internet tonight. This note makes the current handoff explicit so implementation can proceed without treating unanswered questions as approved inputs. It reflects the supplied 20 November team messages and Jason's updated report. The Google Doc was not edited.

## Confirmed data decisions

- Main scope remains 34 SF stations, 9 February-19 April 2015, hourly. [Main V3 inputs](../../output/sf_bikeshare/model_inputs_v3/README.md) and [five robustness packages](../../output/sf_bikeshare/robustness_testing/README.md) are unchanged.
- Carlo confirmed `station.csv:dock_count` as the base capacity. The 67 main-case discrepancies are station-day opening records, not 67 stations. A lower-capacity sensitivity is supported, but its exact definition still needs agreement.
- The proposed daily model initializes from `opening_inventory_daily:opening_bikes`. All 2,380 main-case midnight stocks are fresh. Hourly opening snapshots remain diagnostics; their 34 DST-related stale readings are not daily initialization inputs. Retaining recorded hours still requires the stated DST limitation.
- The [Section 3 draft](../SF_Bikeshare_Consolidated_Data_Preparation_Report.md) remains Carlo's data contribution, with Fu Yan's demand subsection pending. The [figure plan](SF_Bikeshare_Section3_Figure_Plan.md) is a plan, not generated EDA results.

## Provisional rental-cost scenario

These are benchmark inputs, not actual operator expenses or an executable fully calibrated configuration. Currency is USD and physical working units are metric.

| Component | Candidate value | Evidence and treatment |
| --- | ---: | --- |
| Fixed hire `F` | 60 USD/truck-day | High-top cargo van in the 2015 Enterprise contract sheet; a Florida contract-rate proxy, not an SF quote. Charge once per activated truck-day. |
| Rental mileage `r` | 0.08699197 USD/km | 0.14 USD/mile divided by 1.609344; a payable distance charge in this scenario, separate from fuel. |
| Fuel consumption `q` | approximately 16.8 litres/100 km | Ford's 14 US mpg city rating for a specified gasoline wagon configuration; not a measured cargo-van/bike-redistribution duty cycle. |
| Fuel price `P` | 0.88180631 USD/litre | Main V3's March 2015 California gasoline benchmark, displayed as approximately 0.882. Using it for all dates is an explicit common-price scenario, not period-matched observations. |
| Fuel expense `P*q/100` | approximately 0.148 USD/km | Derived; keep fuel separately identifiable from rental mileage. |
| Rental mileage plus fuel | approximately 0.235 USD/km | Excludes driver time, handling and other charges; this is not a complete Stage 1 travel coefficient. |
| AAA maintenance plus tyres | 0.03746868 USD/km | Owner-vehicle benchmark: (0.0519 + 0.0084) USD/mile divided by 1.609344. Do not automatically add it to the rented-vehicle baseline. |
| Additional hourly vehicle charge `V` | not selected | Do not invent a second hourly rental fee on top of daily hire. A reduced rental scenario can explicitly set `V=0` if there is no separate hourly vehicle expense. |

Primary evidence: [Enterprise price sheet, PDF page 4](https://www.fa.ufl.edu/wp-content/uploads/2019/04/Enterprise-National-Pricing-and-Age-Information.pdf), [Ford 2015 Transit brochure, PDF page 7](https://cdn.dealereprocess.org/cdn/brochures/ford/2015-transit.pdf), and [AAA 2015, printed page 8/PDF page 9](https://exchange.aaa.com/wp-content/uploads/2015/04/Your-Driving-Costs-2015.pdf). The Enterprise truck-rate page excludes roadside assistance, liability coverage and loss-damage waiver. These and any other relevant fees are unresolved; missing amounts are not verified zeros. The source title is dated August 2015, after the study windows, so the rate is a historical-year scenario rather than proof of the price in those windows.

### Accounting clarification for implementation

Correct the fuel expression to **`G = D*q/100`**, without a trailing `G`. `D` is route km and `G` is litres.

If the rental mileage charge is represented by the generic route coefficient `M`, the rental scenario uses **`M=r≈0.087 USD/km`**, with fuel `P*G` separate. The AAA value `0.0375` must not replace the payable rental mileage charge or be added automatically as an extra renter expense. Any separately borne maintenance expense needs explicit evidence and scope.

For a single-truck scenario, with no additional hourly vehicle charge and a common paid crew-time basis, the illustrative route accounting reduces to:

```text
C_route = 60*y + W*H + P*(D*q/100) + r*D + A
        approximately 60*y + W*H + 0.235*D + A
```

Here `y` is daily activation, `W` the total assigned crew cost per paid clock-hour, `H` paid hours including driving/handling/setup/waiting, and `A` separately identified other charges. This is conditional accounting, not a solved route or a final cost estimate. Handling already counted in `H` is not added again to Stage 2. Fixed hire is not charged once per hour or once per tour.

Stage 1 remains `c_ij = h + k*d_ij/Lbar`. The non-labour `0.235 USD/km` is not the final `k` if driving labor is included. With crew rate `W`, source driving time `tau_ij` in minutes and no extra hourly vehicle expense, a candidate pair-specific approximation is:

```text
h = W*(loading_minutes_per_bike + unloading_minutes_per_bike)/60
c_ij = h + [(r + P*q/100)*d_ij + W*tau_ij/60]/Lbar
```

This uses existing matrix times and explicitly separates handling from driving. It remains an average-load allocation and does not certify truck routes. Agree this interpretation or an explicit average-speed conversion for a scalar `k` before implementation. Stage 1 and Stage 2 costs describe the same operation and must be compared, not added.

## Proposed parameters awaiting final configuration

| Item | Latest team proposal | Status |
| --- | --- | --- |
| Planning horizon | Independent daily, 24 recorded hours; observed midnight start | Joohee's proposed base; distinguish daily experiments from continuous inventory simulation |
| Terminal stock | No target in base; end stock at least opening stock as a sensitivity | Proposed; report resulting stock depletion and feasibility |
| Truck count | Integer `y`; explicit `0 <= y <= 1` for a single-truck experiment | Ensure the upper bound is actually present in code |
| Average load `Lbar` | 10 / 15 / 25 bikes | Low/base/high team assumptions, not measurements; reconcile with specified onboard capacity |
| Hourly throughput `U` | 10 / 15 / 20 bikes per truck-hour | Team assumptions; does not prove route/load/time feasibility |
| Failed-return penalty | 0 / 0.88 / 4.50 USD/bike | Assumed service weights, not observed compensation or receipts |
| Trip values | Subscriber 0.88; Customer 4.50 USD/trip in base, with existing low/high allocations | Allocated pass value, not marginal cash revenue; no per-trip wear cost is modeled in the proposed base |
| Depot/routing | Open routes, first pickup to last drop-off | Proposed; truck travel and load continuity between hours still need explicit treatment |

## Inputs and decisions still needed

1. **Demand:** Fu Yan's `D_itr` by station/hour/rider class and `A_it`, with documented training, pooling and fallback. Keep source `Subscriber/Customer` labels mapped explicitly to model `member/casual`. A missing demand table is not zero demand. Current evidence does not establish these inputs are complete.
2. **Cost/resources:** confirmed numeric crew rate, handling/setup times, final `h` and travel coefficient interpretation, vehicle configuration/onboard capacity and any extra charges. Keep observed, published-proxy and assumed values distinguishable.
3. **Capacity sensitivity:** specify the exact lower-capacity rule. One possible daily rule is `min(dock_count, midnight snapshot_effective_capacity)`; all 2,380 main-case openings fit that bound. This option has been checked for initialization compatibility, not adopted as the agreed physical-capacity rule.
4. **Return handling:** Joohee/Hong Jin should address fixed internal returns not linked to accepted internal rentals, and ensure failed-return variables represent actual unavailable-dock events rather than discretionary rejection. Merely imposing `o_it <= A_it` does not enforce that condition.
5. **R4 evaluation:** the existing R4 split is training 20 April-14 June and evaluation 15-28 June 2015. Prior data/quality inspection must be disclosed; settings can be frozen prospectively for retrospective evaluation, rather than describing all ten weeks as an untouched test. Station 73 has an unusable midnight opening on 15 June. Agree a documented fallback or common whole-city-day exclusion across policies; do not insert zero or silently remove one station.
6. **Implementation checks:** use the supplied small hand-worked instance before empirical policy results. Approximately 11 minutes maximum SF point-to-point driving time excludes multi-stop travel, loading/unloading and setup. Label perfect-information service allocation if policies use future realized requests. No solver/runtime/financial gains have been established by the data preparation.

## Release boundary

The V3 and robustness CSV/GZIP files, manifests and builders are frozen and unchanged by this note. Their older parameter/decision registers describe that release's preparation state. Use this dated supplement to track subsequent proposals; the legacy blank parameter entries are not permission to treat values as zero. A future model configuration should cite the release and record final numerical values, sources and approval status separately.

Data are available for coding and focused EDA. **The full empirical model-input set is not locked until demand, cost and operational checks are resolved.** The final report should retain this distinction while work proceeds without Carlo's internet access tonight.
