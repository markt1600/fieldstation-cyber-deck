"""Subject navigation using source bookmarks and verified printed contents links."""
import json,re,time
from contextlib import closing
import catalogue

_cache={'at':0,'value':None}
KNOT_CONTENTS={
 'Pioneering - illustrated knots lashings and ropework': [('Safety',9),('Rope-end whipping',12),('Rope tackle',15),('Clove hitch and half hitches',18),('Clove hitch on a bight',20),('Butterfly loop — illustrated steps',21),('Roundturn with two half hitches',21),('Rolling hitch',22),('Water knot',24),('Carrick bend',25),('Draw hitch',26),('Constrictor knot',27),('Lashings',30),('Rope materials and care',40),('Splicing rope',50)],
 'Fishing knots - illustrated handbook': [('Arbor knot',3),('Nail / tube knot',4),('Improved clinch knot',5),('Palomar knot',6),('Uni knot',7),('Double uni knot',8),("Surgeon’s knot",9),("Surgeon’s loop",10),('Loop-to-loop connection',11)]
}
ENV=['Community health','Organising for community health','Protecting natural resources','Environmental rights','Unsafe water and health','Protecting community water','Toilets and sanitation','Mosquitoes and health','Watersheds','Forests','Restoring land and planting trees','Food security','Genetically engineered foods','Pesticides','Sustainable farming','Toxic chemicals','Healthy homes','Solid waste','Health care waste','Reducing harm from toxins','Mining and health','Oil and health','Clean energy']
MED=['Home remedies and popular beliefs','Causes of sickness','Examining a sick person','Caring for a sick person','Healing without medicines','Use and misuse of medicines','Antibiotics','Measuring medicines','Injections','First aid','Nutrition','Prevention and cleanliness','Common sicknesses','Serious illnesses','Skin problems','Eye problems','Teeth and gums','Urinary and genital health','Women’s health and childbirth','Family planning','Children’s health','Older people’s health','Medicine kits']
DENT=['Your own teeth and gums','Teaching family and friends','Teaching children','School activities','Taking care of teeth and gums','Examination and diagnosis','Common dental problems','Scaling teeth','Injections inside the mouth','Treating a cavity','Taking out a tooth','HIV and dental care']
ORDER=['Emergency preparedness & first aid','General health & medicines','Dental health','Family & child health','Parenting & family life','Water & sanitation','Energy & electricity','Food & growing','Shelter & environmental safety','Community & environment','Mathematics','Science','Humanities & study skills','French','Mandarin','Other languages','Reference & reading']

def identify(b):
    title=b['title']; group='Reference & reading';label=title
    if 'Parenting' in b['folder']:return 'Parenting & family life',title
    if 'Knots and ropework' in b['folder']:return 'Knots & ropework',title
    m=re.search(r'en (cgeh|wtnd|dent) \d+ (\d+)$',title)
    if m:
        kind,n=m[1],int(m[2]);names={'cgeh':ENV,'wtnd':MED,'dent':DENT}[kind]
        if 1<=n<=len(names):label=names[n-1]
        if kind=='dent':group='Dental health'
        elif kind=='wtnd':
            group='Emergency preparedness & first aid' if n==10 else 'Dental health' if n==17 else 'Family & child health' if 19<=n<=22 else 'General health & medicines'
        else:
            group='Water & sanitation' if n in (5,6,7,9,18,19) else 'Energy & electricity' if n==23 else 'Food & growing' if n in (12,13,15) else 'Shelter & environmental safety' if n in (8,14,16,17,20,21,22) else 'Community & environment'
    elif 'SCDF' in title.upper():group='Emergency preparedness & first aid';label='Singapore civil defence emergency handbook'
    elif b['category']=='Medical':group='Dental health' if 'Dentist' in b['folder'] else 'General health & medicines'
    elif b['category']=='Practical':group='Community & environment'
    elif b['category']=='Education':
        group='Mathematics' if re.search(r'algebra|calculus|math|statistics|geometry',title,re.I) else 'Science' if re.search(r'biology|chemistry|physics|science|anatomy|astronomy',title,re.I) else 'Humanities & study skills'
    elif b['category']=='Languages':
        group='French' if 'French' in b['folder'] else 'Mandarin' if 'Mandarin' in b['folder'] else 'Other languages'
        label=re.sub(r'^\d+[-_ ]*','',title).replace('.pdf','').replace('_',' ').replace('-',' ')
        label=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',label)
        label=re.sub(r'\s+',' ',label).strip()
    # Give supporting files understandable names without pretending they are chapters.
    suffix=title.split()[-1] if title else ''
    if re.match(r'en (cgeh|wtnd|dent) ',title) and not m:
        label={'fm':'Introduction & publication information','bm':'Appendices','toc':'Printed table of contents','indx':'Alphabetical index','gloss':'Glossary','resc':'Further resources','gp':'Medicine reference — Green Pages','info':'Additional information','int':'Guide for community health workers','appa':'Safety and emergencies','appb':'Environmental rights'}.get(suffix,title)
    return group,label

def contents(b,c):
    if b['title'] in KNOT_CONTENTS:
        return [{'title':label,'page':page,'depth':0} for label,page in KNOT_CONTENTS[b['title']]],'Curated contents — checked against source PDF pages'
    entries=json.loads(b['toc'])
    if entries:return entries,'Publisher bookmarks'
    pages={int(r['page']):r['text'] for r in c.execute('SELECT page,text FROM pages WHERE id=?',(b['id'],))}
    # A printed number is accepted only when it occurs alone near a page edge.
    printed={}
    for n,text in pages.items():
        lines=[s.strip() for s in text.splitlines() if s.strip()]
        header=re.search(r'(?:^|\s)(\d{1,4})$',lines[0]) if lines else None
        if header and len(lines[0])<100:printed.setdefault(int(header[1]),[]).append(n)
        for line in lines[:2]+lines[-2:]:
            if re.fullmatch(r'\d{1,4}',line):printed.setdefault(int(line),[]).append(n)
    for n in sorted(pages)[:8]:
        for line in pages[n].splitlines():
            match=re.match(r'^\s*(.+?)\s*(?:\.\s*){3,}(\d{1,4})\s*$',line)
            if not match:continue
            destinations=set(printed.get(int(match[2]),[]))
            if len(destinations)==1:
                target=destinations.pop()
                entries.append({'title':match[1].strip(),'page':target,'depth':0})
    if entries:return entries,'Printed contents; page numbers matched to PDF pages'
    # For unbookmarked chapters, provide a small set of literal source page headings.
    seen=set()
    for n,text in pages.items():
        for line in [s.strip() for s in text.splitlines() if s.strip()][:4]:
            if 6<len(line)<85 and line.isupper() and re.search('[A-Z]{3}',line) and line not in seen and line not in ('CHAPTER','CONTENTS'):
                seen.add(line);entries.append({'title':line.title(),'page':n,'depth':0})
                break
    return entries[:100], 'Extracted page headings' if entries else 'No reliable chapter links available yet'

def tree():
    if time.time()-_cache['at']<60:return _cache['value']
    groups={name:[] for name in ORDER}
    with closing(catalogue.connect()) as c:
        for row in c.execute('SELECT * FROM books ORDER BY folder,title').fetchall():
            b=dict(row);group,label=identify(b);toc,method=contents(b,c)
            groups.setdefault(group,[]).append({'id':b['id'],'label':label,'source':b['folder'].replace('\\',' / '),'pages':b['pages'],'entries':toc,'method':method,'status':b['status']})
    value={'groups':[{'title':name,'items':items} for name,items in groups.items() if items]}
    _cache.update(at=time.time(),value=value);return value
