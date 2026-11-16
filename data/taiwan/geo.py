import json,os,time,urllib.request,urllib.parse
CACHE='geocache.json'
cache=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
last=[0]
def geocode(q):
    if q in cache: return cache[q]
    wait=1.1-(time.time()-last[0])
    if wait>0: time.sleep(wait)
    u='https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&countrycodes=tw&accept-language=zh-TW,en&q='+urllib.parse.quote(q)
    try:
        r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'ReduxTaiwanHarvest/1.0 (dedomenici redux project; contact via github dedomenici)'}),timeout=30))
    except Exception as e:
        print('geo err',q,e); r=None
    last[0]=time.time()
    v=None
    if r: v=dict(lat=float(r[0]['lat']),lng=float(r[0]['lon']),display=r[0]['display_name'],type=r[0].get('type'),cls=r[0].get('category') or r[0].get('class'))
    cache[q]=v; json.dump(cache,open(CACHE,'w'),ensure_ascii=False)
    return v
