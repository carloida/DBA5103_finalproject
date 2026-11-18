hey team! updated the dataset to V3 based on everyone's comments :)

same 34 SF stations, 10 weeks, hourly. all working units are metric, with costs in USD.

for Jason:
- added the historical pass-price/overtime-fee references and your low/base/high allocated-revenue assumptions. these are still assumptions since we don't have actual payments.

for Fu Yan:
- added Subscriber/Customer counts matched to bike/dock availability periods for demand estimation.
- updated the cost note for multi-stop trips, separating Stage 1's estimated transfer cost from Stage 2's route-based cost check.

for Joo Hee:
- added hourly Subscriber/Customer pickups and returns, daily opening bikes, available docks and capacity checks.
- included station coordinates, current road-distance/travel-time estimates, external inflows/outflows and trip-timing inputs.

the data checks passed. I'll upload the updated dataset and changelog to GitHub here:
https://github.com/carloida/DBA5103_finalproject/tree/main/output/sf_bikeshare/model_inputs_v3

I'll add the changelog to our shared Doc manually too. demand estimates and truck/cost values still need finalising. feel free to suggest changes, just let me know so I can keep the data aligned with the model. thanks team!
