from pathlib import Path
import openpyxl,csv,hashlib,json,datetime
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'data/download_manifest.json').read_text()) if (root/'data/download_manifest.json').exists() else []
sources=json.loads((root/'data/sources.json').read_text())
for name,sheets in {'seifa':['All By PCST, Age Group, SEIFA','Primary Care Service Types'],'primary':['State','Modified Monash']}.items():
 p=root/'data'/(name+'.xlsx');w=openpyxl.load_workbook(p,read_only=True,data_only=True)
 if not any(m['file']==p.name for m in manifest):manifest.append(dict(file=p.name,url=sources[name],retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size))
 for i,sh in enumerate(sheets):
  out=root/'data'/(name+('_definitions' if 'Types' in sh else '_'+str(i))+'.csv')
  with out.open('w',newline='',encoding='utf-8') as f:
   wr=csv.writer(f)
   for r in w[sh].iter_rows(max_col=17,values_only=True):wr.writerow(r)
  print(out.name)
(root/'data/download_manifest.json').write_text(json.dumps(manifest,indent=2))
