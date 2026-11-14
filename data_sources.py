import os,requests,time,json,sqlite3,datetime
from engine import normalize_recipe
DB=os.getenv('FOREVER_DB','forever_optimizer.sqlite3')
UA='ForeverProfessionOptimizer/0.1 (personal research; ForeverDB credited)'
def connect():
 c=sqlite3.connect(DB)
 c.execute('CREATE TABLE IF NOT EXISTS recipes (profession TEXT, id TEXT, payload TEXT, PRIMARY KEY(profession,id))')
 c.execute('CREATE TABLE IF NOT EXISTS prices (house INTEGER, captured TEXT, item_id INTEGER, quantity REAL, unit_copper REAL)')
 c.execute('CREATE INDEX IF NOT EXISTS ix_prices ON prices(house,captured,item_id)')
 return c

def fetch_recipes(profession,key):
 if not key:raise ValueError('ForeverDB API key required. Apply at foreverdb.net/developers')
 s=requests.Session();s.headers.update({'X-API-Key':key,'User-Agent':UA})
 offset=0;results=[]
 while True:
  response=s.get(f'https://foreverdb.net/api/v1/professions/{profession}',params={'limit':100,'offset':offset},timeout=40)
  response.raise_for_status();payload=response.json();data=payload.get('data',payload)
  if isinstance(data,dict):rows=data.get('recipes') or data.get('items') or []
  elif isinstance(data,list):rows=data
  else:rows=[]
  if isinstance(rows,dict):rows=rows.get('data',[])
  if not rows:break
  results.extend(rows);offset+=len(rows)
  meta=payload.get('meta',{})
  if offset>=int(meta.get('total',offset+1)) or len(rows)<100:break
  if offset>5000:break
  time.sleep(.15)
 with connect() as c:
  for r in results:
   nr=normalize_recipe(r)
   c.execute('INSERT OR REPLACE INTO recipes VALUES (?,?,?)',(profession,nr['id'],json.dumps(r)))
 return len(results)

def recipes_for(profession):
 with connect() as c: rows=c.execute('SELECT payload FROM recipes WHERE profession=?',(profession,)).fetchall()
 return [normalize_recipe(json.loads(r[0])) for r in rows]

def oauth(client,secret):
 r=requests.post('https://oauth.battle.net/token',auth=(client,secret),data={'grant_type':'client_credentials'},timeout=30);r.raise_for_status();return r.json()['access_token']

def auction_houses(token):
 s=requests.Session();s.headers['Authorization']='Bearer '+token
 url='https://eu.api.blizzard.com/data/wow/ruleset/1/auctions/'
 r=s.get(url,params={'namespace':'dynamic-forever-eu'},timeout=40);r.raise_for_status()
 return r.json().get('auctions',[])

def fetch_auctions(client,secret,house):
 token=oauth(client,secret);s=requests.Session();s.headers['Authorization']='Bearer '+token
 base=f'https://eu.api.blizzard.com/data/wow/ruleset/1/auctions/{house}'
 rows=[]
 for suffix,commodity in [('',False),('/commodities',True)]:
  r=s.get(base+suffix,params={'namespace':'dynamic-forever-eu'},timeout=180);r.raise_for_status()
  for a in r.json().get('auctions',[]):
   try:
    item=int(a['item']['id']);qty=float(a.get('quantity',1));price=float(a.get('unit_price') if commodity else a.get('buyout'))
    if qty>0 and price>0:rows.append((item,qty,price if commodity else price/qty))
   except (KeyError,ValueError,TypeError):continue
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 with connect() as c:
  c.executemany('INSERT INTO prices VALUES (?,?,?,?,?)',[(house,stamp,*r) for r in rows])
 return len(rows),stamp

def latest_prices(house):
 with connect() as c:
  last=c.execute('SELECT MAX(captured) FROM prices WHERE house=?',(house,)).fetchone()[0]
  if not last:return [],None
  rows=c.execute('SELECT item_id,quantity,unit_copper FROM prices WHERE house=? AND captured=?',(house,last)).fetchall()
 return [dict(zip(('item_id','quantity','unit_copper'),r)) for r in rows],last
