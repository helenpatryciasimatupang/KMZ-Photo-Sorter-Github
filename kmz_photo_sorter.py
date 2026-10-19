#!/usr/bin/env python3
"""Gabungkan pecahan KMZ dan pisahkan titik yang memiliki foto / belum memiliki foto.

Pemakaian:
  python kmz_photo_sorter.py FOLDER_INPUT FOLDER_OUTPUT
  python kmz_photo_sorter.py FOLDER_INPUT FOLDER_OUTPUT target.csv
CSV opsional menggunakan kolom name, latitude, longitude.
Hanya menggunakan pustaka bawaan Python.
"""
import csv, html, re, sys, zipfile
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

NS = 'http://www.opengis.net/kml/2.2'
ET.register_namespace('', NS)
ET.register_namespace('gx', 'http://www.google.com/kml/ext/2.2')
ET.register_namespace('atom', 'http://www.w3.org/2005/Atom')
IMAGE_EXTS = {'.jpg','.jpeg','.png','.gif','.webp','.bmp','.tif','.tiff'}

def local(tag): return tag.rsplit('}',1)[-1] if '}' in tag else tag

def text_of(node, wanted):
    for e in node.iter():
        if local(e.tag).lower() == wanted.lower() and e.text: return e.text.strip()
    return ''

def coords(pm):
    for e in pm.iter():
        if local(e.tag) == 'coordinates' and e.text:
            try:
                p=e.text.strip().split()[0].split(',')
                return float(p[1]),float(p[0])
            except Exception: pass
    return None

def norm(s): return re.sub(r'[^a-z0-9]+','',(s or '').lower())

def distance_m(a,b):
    from math import radians,sin,cos,asin,sqrt
    lat1,lon1=a; lat2,lon2=b
    dlat=radians(lat2-lat1); dlon=radians(lon2-lon1)
    h=sin(dlat/2)**2+cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 6371000*2*asin(sqrt(h))

def load_targets(path):
    if not path: return []
    result=[]
    with open(path,newline='',encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            d={str(k).strip().lower():(v or '').strip() for k,v in row.items() if k}
            name=next((d[k] for k in ('name','nama','nama hp nn dan new','site id','site_id') if d.get(k)), '')
            lat=next((d[k] for k in ('latitude','lat') if d.get(k)), '')
            lon=next((d[k] for k in ('longitude','langitude','lon','lng') if d.get(k)), '')
            try: result.append({'name':name,'norm':norm(name),'coord':(float(lat),float(lon))})
            except ValueError: continue
    return result

def match_target(name, point, targets):
    n=norm(name)
    exact=[t for t in targets if n and t['norm']==n]
    if exact: return exact[0]
    partial=[t for t in targets if n and t['norm'] and (t['norm'] in n or n in t['norm'])]
    if len(partial)==1: return partial[0]
    if point and targets:
        closest=min(targets,key=lambda t:distance_m(point,t['coord']))
        if distance_m(point,closest['coord'])<=15: return closest
    return None

def find_kml(zf):
    names=[n for n in zf.namelist() if n.lower().endswith('.kml')]
    if not names: return None
    names.sort(key=lambda n:(0 if PurePosixPath(n).name.lower()=='doc.kml' else 1,len(n)))
    return names[0]

def image_hrefs(pm):
    refs=[]
    for e in pm.iter():
        if local(e.tag)=='href' and e.text:
            h=e.text.strip()
            if Path(urlparse(h).path).suffix.lower() in IMAGE_EXTS: refs.append(h)
        if local(e.tag)=='description' and e.text:
            refs += [m for m in re.findall(r"(?:src|href)\s*=\s*[\"']([^\"']+)[\"']",e.text,re.I) if Path(urlparse(m).path).suffix.lower() in IMAGE_EXTS]
    return list(dict.fromkeys(refs))

def resolve_member(kml_name, href, members):
    href=html.unescape(href.strip()).replace('\\','/')
    parsed=urlparse(href)
    if parsed.scheme or href.startswith('//') or href.startswith('data:'): return None
    raw=unquote(parsed.path).lstrip('/'); parent=str(PurePosixPath(kml_name).parent)
    candidates=[raw]
    if parent not in ('','.'): candidates.append(str(PurePosixPath(parent)/raw))
    candidates += [n for n in members if PurePosixPath(n).name==PurePosixPath(raw).name]
    for c in candidates:
        if c in members: return c
    return None

def process_placemark(pm,kml_name,members,zf,assets,counter):
    found=False
    for href in image_hrefs(pm):
        member=resolve_member(kml_name,href,members)
        if not member: continue
        found=True
        if member not in assets:
            ext=Path(member).suffix.lower() or '.jpg'
            assets[member]=f'images/photo_{counter[0]:05d}{ext}'
            counter[0]+=1
        new=assets[member]
        for e in pm.iter():
            if local(e.tag)=='href' and e.text and e.text.strip()==href: e.text=new
            if local(e.tag)=='description' and e.text:
                pattern = r"""((?:src|href)\s*=\s*[\"'])""" + re.escape(href) + r"""([\"'])"""
                e.text=re.sub(pattern,lambda m:m.group(1)+new+m.group(2),e.text,flags=re.I)
    for e in pm.iter():
        if local(e.tag)=='description' and e.text and re.search(r'data:image/(?:jpeg|jpg|png|gif|webp);base64,',e.text,re.I): found=True
    return found

def build_kml(placemarks,title):
    root=ET.Element('{%s}kml'%NS); doc=ET.SubElement(root,'{%s}Document'%NS)
    ET.SubElement(doc,'{%s}name'%NS).text=title
    for pm in placemarks: doc.append(pm)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)

def main():
    if len(sys.argv)<3:
        print(__doc__); return 2
    inp=Path(sys.argv[1]).expanduser().resolve(); out=Path(sys.argv[2]).expanduser().resolve()
    csv_path=Path(sys.argv[3]).expanduser().resolve() if len(sys.argv)>3 else None
    if not inp.is_dir(): raise SystemExit(f'Folder input tidak ditemukan: {inp}')
    out.mkdir(parents=True,exist_ok=True); targets=load_targets(csv_path) if csv_path else []
    with_photo=[]; without_photo=[]; photo_assets={}; counter=[1]; skipped=[]
    files=sorted(inp.glob('*.kmz'))
    if not files: raise SystemExit('Tidak ada file .kmz di folder input.')
    for path in files:
        try:
            with zipfile.ZipFile(path) as zf:
                kml=find_kml(zf)
                if not kml: skipped.append(f'{path.name}: tidak ada KML'); continue
                members=set(zf.namelist()); root=ET.fromstring(zf.read(kml))
                for original in [e for e in root.iter() if local(e.tag)=='Placemark']:
                    pm=ET.fromstring(ET.tostring(original,encoding='utf-8'))
                    name=text_of(pm,'name'); point=coords(pm)
                    target=match_target(name,point,targets) if targets else None
                    if targets and not target: continue
                    if target and target['name']:
                        first=next((e for e in pm if local(e.tag)=='name'),None)
                        if first is not None: first.text=target['name']
                    has=process_placemark(pm,kml,members,zf,photo_assets,counter)
                    (with_photo if has else without_photo).append(pm)
        except Exception as e: skipped.append(f'{path.name}: gagal dibaca ({e})')
    out_with=out/'KMZ_SUDAH_BERISI_FOTO.kmz'; out_without=out/'KMZ_BELUM_ADA_FOTO.kmz'
    # Write only image assets referenced by placemarks with photos. The source files are never changed.
    for dest,placemarks,title,include_assets in [(out_with,with_photo,'Lokasi sudah berisi foto',True),(out_without,without_photo,'Lokasi belum memiliki foto',False)]:
        with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as oz:
            oz.writestr('doc.kml',build_kml(placemarks,title))
            if include_assets:
                used=set()
                for pm in placemarks:
                    for h in image_hrefs(pm):
                        if h.startswith('images/photo_'):
                            used.add(h)
                # Each copied resource is stored at its rewritten relative path.
                for source, destname in photo_assets.items():
                    if destname in used:
                        # Retrieve the exact original asset from whichever input archive contains it.
                        for src in files:
                            try:
                                with zipfile.ZipFile(src) as iz:
                                    if source in iz.namelist(): oz.writestr(destname,iz.read(source)); raise StopIteration
                            except StopIteration: break
                            except Exception: pass
    report=out/'LAPORAN_PEMROSESAN.txt'
    report.write_text(f'File KMZ input: {len(files)}\nLokasi dengan foto: {len(with_photo)}\nLokasi tanpa foto: {len(without_photo)}\nFilter CSV target: {"aktif" if targets else "tidak digunakan"}\n'+('File bermasalah:\n- '+'\n- '.join(skipped) if skipped else 'Semua file input dapat dibaca.\n'),encoding='utf-8')
    print(f'Selesai. Dengan foto: {len(with_photo)}; tanpa foto: {len(without_photo)}. Hasil: {out}')
    if skipped: print('Periksa LAPORAN_PEMROSESAN.txt untuk file yang dilewati.')
    return 0
if __name__=='__main__': sys.exit(main())
