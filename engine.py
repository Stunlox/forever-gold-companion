"""Expected-cost profession levelling engine. All monetary values are copper."""
from collections import defaultdict
import math

PROFESSIONS = ['alchemy','blacksmithing','enchanting','engineering','leatherworking','tailoring','cooking','first-aid']

def chance(skill, orange, yellow, green, grey):
    if skill < orange: return 1.0
    if skill >= grey: return 0.0
    if skill < yellow: return 1.0
    if skill < green: return max(.01, 1 - .5*(skill-yellow)/max(1,green-yellow))
    return max(.01, .5*(grey-skill)/max(1,grey-green))

def normalize_recipe(raw):
    """Accept normalized JSON and common ForeverDB field shapes; flag missing data."""
    if 'recipe' in raw and isinstance(raw['recipe'],dict):
        raw = {**raw['recipe'], **{k:v for k,v in raw.items() if k!='recipe'}}
    skill=raw.get('skill') or {}
    if not isinstance(skill,dict): skill={'orange':skill}
    sources=(raw.get('learnedFrom') or {}).get('sources',{}) if isinstance(raw.get('learnedFrom'),dict) else {}
    trainers=sources.get('trainers',[]) if isinstance(sources,dict) else []
    if isinstance(trainers,dict): trainers=list(trainers.values())
    learn=raw.get('learnedFrom') or {}
    learnstr=str(learn).lower()
    trainer=bool(trainers) or 'trainer' in learnstr or raw.get('trainerOnly') is True
    auto='automatically' in learnstr or raw.get('automatic') is True
    verified=any(isinstance(t,dict) and (t.get('seenInForever') is True) for t in trainers)
    reagents=raw.get('reagents') or raw.get('materials') or []
    mats={}
    if isinstance(reagents,dict): reagents=[{'item':{'id':k},'quantity':v} for k,v in reagents.items()]
    for m in reagents:
        if not isinstance(m,dict):continue
        item=m.get('item') or m.get('reagent') or m.get('itemId') or m.get('id')
        if isinstance(item,dict): item=item.get('id') or item.get('itemId')
        qty=m.get('quantity',m.get('count',m.get('amount',1)))
        try: mats[int(item)]=mats.get(int(item),0)+float(qty)
        except (ValueError,TypeError):pass
    produced=raw.get('makes') or raw.get('creates') or raw.get('output') or {}
    if isinstance(produced,list):produced=produced[0] if produced else {}
    if not isinstance(produced,dict):produced={}
    out=produced.get('item') or produced.get('id') or raw.get('itemId')
    if isinstance(out,dict):out=out.get('id')
    try:out=int(out)
    except (ValueError,TypeError):out=None
    thresholds={}
    for k in ('orange','yellow','green','grey'):
        try:thresholds[k]=int(skill.get(k))
        except (ValueError,TypeError):thresholds[k]=None
    return {'id':str(raw.get('id') or raw.get('spellId') or raw.get('name') or ''),
      'name':raw.get('name') or raw.get('recipeName') or str(raw.get('id','Unknown')),
      'mats':mats,'output_id':out,'output_count':float(produced.get('count') or 1),
      'trainer':trainer,'automatic':auto,'verified':verified,'skill':thresholds,
      'source':raw}

def valid(r,require_verified=False):
    s=r['skill']
    return bool(r['mats']) and all(isinstance(s.get(k),int) for k in ('orange','yellow','green','grey')) and (r['trainer'] or r['automatic']) and (not require_verified or r['verified'] or r['automatic']) and s['orange']<=s['yellow']<=s['green']<=s['grey']

def build_price_book(listings):
    """List of {item_id,quantity,unit_copper}; cheapest quantities first."""
    book=defaultdict(list)
    for x in listings:
        try:
            item=int(x['item_id']);qty=float(x['quantity']);price=float(x['unit_copper'])
            if qty>0 and price>=0:book[item].append((price,qty))
        except (KeyError,ValueError,TypeError):continue
    for k in book:book[k].sort()
    return dict(book)

def material_cost(book,item,quantity,allow_partial=False):
    left=quantity;cost=0
    for price,available in book.get(int(item),[]):
        take=min(left,available);cost+=take*price;left-=take
        if left<=1e-8:break
    if left>1e-8 and not allow_partial:return math.inf
    return cost

def optimize(recipes,book,start,target,owned=None,include_resale=False,require_verified=False,unknown_policy='exclude'):
    """Bellman expected-cost recurrence: V(s)=min_r[cost(r)/p(r)+V(s+1)].
    Fixed-price independent crafts; inventory and volume constraints checked in final shopping list.
    """
    owned=owned or {};dp={target:0.};choice={};warnings=[]
    candidates=[r for r in recipes if valid(r,require_verified)]
    for s in range(target-1,start-1,-1):
        best=(math.inf,None)
        for r in candidates:
            t=r['skill']
            if s<t['orange'] or s>=t['grey']:continue
            p=chance(s,**t)
            if p<=0:continue
            craft_cost=0
            for item,qty in r['mats'].items():
                c=material_cost(book,item,qty)
                if math.isinf(c):
                    if unknown_policy=='exclude':craft_cost=math.inf;break
                    c=0
                craft_cost+=c
            if include_resale and r['output_id']:
                sale=book.get(r['output_id'],[])
                if sale:craft_cost=max(0,craft_cost-sale[0][0]*r['output_count']*.75)
            total=craft_cost/p+dp.get(s+1,math.inf)
            if total<best[0]:best=(total,r)
        dp[s]=best[0];choice[s]=best[1]
    if not math.isfinite(dp.get(start,math.inf)):
        return {'error':'No complete route found. Check trainer recipes, skill thresholds and missing material prices.','covered':len(candidates)}
    steps=[];shopping=defaultdict(float)
    for s in range(start,target):
        r=choice[s];p=chance(s,**r['skill']);crafts=1/p
        steps.append({'skill':s,'recipe':r['name'],'recipe_id':r['id'],'expected_crafts':crafts,'chance':p,'cost_copper':sum(material_cost(book,k,v) for k,v in r['mats'].items())*crafts,'verified':r['verified'],'mats':r['mats']})
        for k,v in r['mats'].items():shopping[k]+=v*crafts
    groups=[]
    for step in steps:
        if groups and groups[-1]['recipe_id']==step['recipe_id']:
            groups[-1]['to']=step['skill']+1;groups[-1]['expected_crafts']+=step['expected_crafts'];groups[-1]['cost_copper']+=step['cost_copper']
        else:groups.append({'from':step['skill'],'to':step['skill']+1,**step})
    shopping_rows=[];shortage=False
    for item,qty in sorted(shopping.items()):
        need=max(0,math.ceil(qty-owned.get(item,0)))
        cost=material_cost(book,item,need)
        if math.isinf(cost):shortage=True
        shopping_rows.append({'item_id':item,'expected_quantity':round(qty,2),'buy_quantity':need,'estimated_copper':cost})
    return {'expected_copper':dp[start],'steps':groups,'shopping':shopping_rows,'covered':len(candidates),'shortage':shortage,'notes':['Expected crafts are probabilistic, not guaranteed.','Shopping-list cost accounts for listing depth, but the route itself uses marginal craft costs; large purchases may cost more.','Owned inventory is applied to the shopping list, not route selection.','Resale uses a speculative 75% of lowest listed price, not guaranteed sale proceeds.']}
