"""Fetch optional original sources; main numerical reproduction does not need these."""
from pathlib import Path
import argparse, hashlib, urllib.request, zipfile, shutil
SOURCES = {
 "boundaries": ("https://gisco-services.ec.europa.eu/distribution/v2/urau/geojson/URAU_RG_100K_2018_4326_FUA.geojson", "4b5423cb8a551b6c70506ca6271c221ab0b00f99fac961d5e4a31f15de0352bd", "sources/boundaries.geojson"),
 "map": ("https://gisco-services.ec.europa.eu/distribution/v2/countries/geojson/CNTR_RG_10M_2024_4326.geojson", "bb418fe0c0c295c8467b96db7d2064e883c70c0723e6ceeebc38a38c086ba162", "context_inputs/CNTR_RG_10M_2024_4326.geojson"),
 "population": ("https://ec.europa.eu/eurostat/cache/GISCO/geodatafiles/JRC_GRID_2018.zip", "894f4fc114c683701b979b05a52a381979a551146f1e1ded0a4f50a22e94d17d", None)
}
MEMBERS = {"JRC_1K_POP_2018.tif": "4372a58f2e4a0b0bd784ef72761717e524bbf4007afe5691b1f16bfb3b187c31", "JRC-GEOSTAT_2018_TechnicalFactsheet.pdf": "dbe0456d9f13e2d9b4dc020d25ed09a58e14462a7877d2e4a0e72d18fb90a85d"}
def digest(p):
 with open(p,"rb") as f: return hashlib.file_digest(f,"sha256").hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__+" Read THIRD_PARTY_TERMS.md before acquisition. Population ZIP is large.")
 ap.add_argument("--sources",nargs="+",choices=list(SOURCES),required=True)
 ap.add_argument("--raw-dir",type=Path,required=True,help="Original download storage (E: on the study host)")
 ap.add_argument("--work-dir",type=Path,default=Path(__file__).resolve().parent)
 a=ap.parse_args();a.raw_dir.mkdir(parents=True,exist_ok=True)
 for name in a.sources:
  url,expected,dest=SOURCES[name];raw=a.raw_dir/url.rsplit("/",1)[-1]
  if not raw.exists():
   with urllib.request.urlopen(url,timeout=180) as response,raw.open("xb") as f: shutil.copyfileobj(response,f)
  if digest(raw)!=expected: raise ValueError("Source identity mismatch: "+str(raw)+"; existing raw file was not modified")
  if dest:
   target=a.work_dir/dest;target.parent.mkdir(parents=True,exist_ok=True)
   if target.exists():
    if digest(target)!=expected: raise ValueError("Existing work file differs: "+str(target))
   else: shutil.copyfile(raw,target)
  else:
   with zipfile.ZipFile(raw) as z:
    for member,h in MEMBERS.items():
     matches=[n for n in z.namelist() if Path(n).name==member]
     if len(matches)!=1: raise ValueError("Unexpected ZIP membership: "+member)
     target=a.work_dir/"sources"/member;target.parent.mkdir(parents=True,exist_ok=True)
     if not target.exists():
      with z.open(matches[0]) as src,target.open("xb") as dst: shutil.copyfileobj(src,dst)
     if digest(target)!=h: raise ValueError("Member identity mismatch: "+member)
  print(name+": verified and available")
if __name__=="__main__": main()
