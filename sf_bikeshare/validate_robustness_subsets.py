"""Validate the portable robustness handoff without the large source database.

Run: python sf_bikeshare/validate_robustness_subsets.py
Uses only standard-library readers, so this also checks CSV/GZIP export usability.
"""
from pathlib import Path
import csv
import gzip
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/sf_bikeshare'
SUITE=BASE/'robustness_testing'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()
def csv_rows(path):
    opener=gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt',encoding='utf-8',newline='') as stream:
        yield from csv.DictReader(stream)
def schemas(path):
    result={}
    for row in csv_rows(path):
        result.setdefault(row['table'],[]).append((row['column'],row['sql_type']))
    return result
def validate():
    reference=schemas(BASE/'model_inputs_v3/data_dictionary.csv')
    expected_header=[name for name,_ in reference['station_hour_observed']]
    manifests=sorted(SUITE.glob('R*/manifest.json'))
    assert len(manifests)==5
    report=[]
    for path in manifests:
        m=json.loads(path.read_text(encoding='utf-8'))
        folder=path.parent
        assert m['purpose']=='ROBUSTNESS TESTING ONLY'
        assert m['script_sha256']==sha(ROOT/'sf_bikeshare/build_robustness_subsets.py')
        assert schemas(folder/'data_dictionary.csv')==reference,(folder,'schema mismatch')
        assert len(reference)==21 and len(expected_header)==51
        for file in m['files']:
            target=(ROOT/file['path']).resolve()
            assert target.is_relative_to(folder.resolve()),target
            assert target.stat().st_size==file['bytes'] and sha(target)==file['sha256'],target
        checks=list(csv_rows(folder/'validation_checks.csv'))
        assert len(checks)==65 and all(row['passed']=='True' for row in checks)
        with gzip.open(folder/'station_hour_observed.csv.gz','rt',encoding='utf-8',newline='') as stream:
            reader=csv.DictReader(stream)
            assert reader.fieldnames==expected_header
            seen=set();training=0;validation=0
            totals=dict(subscriber_pickups=0,customer_pickups=0,subscriber_returns=0,customer_returns=0)
            for row in reader:
                key=row['station_id'],row['hour_start']
                assert key not in seen
                seen.add(key)
                training+=row['split']=='training'
                validation+=row['split']=='validation'
                for field in totals:
                    totals[field]+=int(row[field])
            n=m['summary']['stations']
            assert len(seen)==n*70*24==m['summary']['station_hours']
            assert training==n*56*24 and validation==n*14*24
            assert totals=={k:int(m['summary']['rider_totals'][0][k]) for k in totals}
        for table in csv_rows(folder/'table_inventory.csv'):
            if table['export']!='local_database_only':
                assert sum(1 for _ in csv_rows(folder/table['export']))==int(table['rows']),table
        openings=list(csv_rows(folder/'opening_inventory_daily.csv'))
        for row in openings:
            if row['inventory_quality']!='valid_within_90_seconds':
                assert row['opening_bikes']=='' and row['opening_available_docks']==''
        assert all(r['value']=='' for r in csv_rows(folder/'operating_parameter_register.csv')
                   if r['parameter'].startswith('gasoline_'))
        report.append(dict(case_id=m['case_id'],city=m['city'],rows=len(seen),
           matched_core_schemas=len(reference),hourly_columns=len(expected_header),
           build_checks=65,export_readbacks=18,portable_validation='passed'))
    print(json.dumps(report,indent=2))
    print('All five portable packages passed hash, schema, row, rider-total, split and missing-stock checks.')
    return report
if __name__=='__main__':
    validate()
