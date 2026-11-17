"""Convert the percent-cell EDA script to a notebook and execute in this Python env."""
from pathlib import Path
import json
import re
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'sf_bikeshare'
source=(folder/'SF_Bay_Area_Bikeshare_EDA.py').read_text(encoding='utf-8')
cells=[]
for kind,body in re.findall(r'^# %%( \[markdown\])?\n(.*?)(?=^# %%|\Z)',source,flags=re.M|re.S):
    if kind:
        lines=[line[2:] if line.startswith('# ') else line[1:] if line.startswith('#') else line for line in body.rstrip().splitlines()]
        cells.append(nbformat.v4.new_markdown_cell('\n'.join(lines)))
    else:
        cells.append(nbformat.v4.new_code_cell(body.rstrip()))
nb=nbformat.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},
    'language_info':{'name':'python','version':sys.version.split()[0]}})
kernel_root=ROOT/'tmp/sf_eda_kernels'
kernel_dir=kernel_root/'sf_eda';kernel_dir.mkdir(parents=True,exist_ok=True)
(kernel_dir/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
    'display_name':'SF EDA workspace Python','language':'python'}),encoding='utf-8')
km=KernelManager(kernel_name='sf_eda',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernel_root)]))
client=NotebookClient(nb,km=km,timeout=1200,allow_errors=False,resources={'metadata':{'path':str(ROOT)}})
print(f'Executing {len(cells)} cells in the workspace Python environment...',flush=True)
try:
    client.execute()
finally:
    if km.has_kernel:
        km.shutdown_kernel(now=True)
path=folder/'SF_Bay_Area_Bikeshare_EDA.ipynb'
nbformat.write(nb,path)
assert not any(o.get('output_type')=='error' for c in nb.cells for o in c.get('outputs',[]))
print(f'Executed notebook saved: {path}',flush=True)
