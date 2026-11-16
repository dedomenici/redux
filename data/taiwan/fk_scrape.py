import re,html,json,time,urllib.request,urllib.parse
B='https://www.filmkh.org/tc/'
def get(u):
    for i in range(3):
        try:
            return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read().decode('utf8','ignore')
        except Exception as e: time.sleep(2)
    return ''
def text(t):
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    s=html.unescape(re.sub(r'<[^>]+>','\n',t)); return re.sub(r'\n\s*\n+','\n',s)
if __name__!="__main__": raise SystemExit
out=[]
for kd in ['電影','電視劇/電視節目','短片/學生製片']:
    ids=[]
    for p in range(1,30):
        t=get(B+'teams?tm_kd='+urllib.parse.quote(kd)+'&page=%d'%p)
        new=[x for x in re.findall(r'teams_detail\?tm_sn=(\d+)',t) if x not in ids]
        if not new: break
        ids+=new; time.sleep(0.5)
    print(kd,len(ids))
    for i in ids:
        u=B+'teams_detail?tm_sn='+i
        s=text(get(u)); time.sleep(0.4)
        j=s.find('找支援\n'); s2=s[j+4:]
        lines=s2.split('\n')
        def field(name):
            m=re.search(name+r'[：:]\s*\n?(.*?)\n',s2); return m.group(1).strip() if m else ''
        rec=dict(kind=kd,id=i,url=u,company=lines[0].strip(),title=lines[1].strip(),
                 director=field('導演'),cast=field('演員卡司'),date=field('受理日期'),scenes=field('拍攝場景'),note=field('備  註'))
        out.append(rec)
json.dump(out,open('fk/teams.json','w'),ensure_ascii=False,indent=1)
print(len(out))
