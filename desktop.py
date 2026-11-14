"""Native Windows-friendly UI for the Forever profession optimiser."""
import csv, os, threading, traceback, sqlite3, datetime, statistics
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from engine import PROFESSIONS, optimize, build_price_book
from data_sources import fetch_recipes, recipes_for, fetch_auctions, latest_prices, auction_houses, oauth

# Store data in a user-writable location when packaged as an exe.
os.environ.setdefault('FOREVER_DB', str(Path.home() / 'ForeverProfessionOptimizer' / 'market.sqlite3'))
Path(os.environ['FOREVER_DB']).parent.mkdir(parents=True, exist_ok=True)

class App(tk.Tk):
 def __init__(self):
  super().__init__(); self.title('Forever Gold Companion | EU PvP Alliance'); self.geometry('1040x740'); self.minsize(780,550)
  self.result=None; self.house=tk.StringVar(value='110'); self.prof=tk.StringVar(value='tailoring'); self.start=tk.StringVar(value='1'); self.target=tk.StringVar(value='300'); self.verified=tk.BooleanVar(value=False)
  self.fdb=tk.StringVar(); self.client=tk.StringVar(); self.secret=tk.StringVar(); self.status=tk.StringVar(value='Ready. Import Forever recipes and refresh AH prices to begin.')
  tabs=ttk.Notebook(self); tabs.pack(fill='both',expand=True,padx=12,pady=10)
  setup=ttk.Frame(tabs,padding=16); route=ttk.Frame(tabs,padding=16); tabs.add(setup,text='Connections & data'); tabs.add(route,text='Cheapest route'); market=ttk.Frame(tabs,padding=16); tabs.add(market,text='Market & deals')
  for i,(label,var,hidden) in enumerate([('ForeverDB API key',self.fdb,True),('Blizzard client ID',self.client,False),('Blizzard client secret',self.secret,True),('Auction house ID (verify EU PvP Alliance)',self.house,False)]):
   ttk.Label(setup,text=label).grid(row=i,column=0,sticky='w',pady=8)
   ttk.Entry(setup,textvariable=var,show='*' if hidden else '',width=52).grid(row=i,column=1,sticky='ew',padx=12)
  ttk.Button(setup,text='Discover AH IDs',command=self.discover).grid(row=4,column=0,pady=12,sticky='w')
  ttk.Button(setup,text='Refresh AH snapshot',command=self.refresh).grid(row=4,column=1,pady=12,sticky='w')
  ttk.Label(setup,text='Auction IDs and endpoints are unverified. Check the correct market before fetching.',wraplength=780).grid(row=5,column=0,columnspan=2,sticky='w')
  ttk.Label(setup,text='Profession').grid(row=6,column=0,sticky='w',pady=12)
  ttk.Combobox(setup,textvariable=self.prof,values=PROFESSIONS,state='readonly',width=30).grid(row=6,column=1,sticky='w')
  ttk.Button(setup,text='Import profession recipes',command=self.import_recipes).grid(row=7,column=1,sticky='w')
  ttk.Label(setup,text='Credentials are not saved. Price snapshots and recipes are stored locally in your user profile.',wraplength=800).grid(row=8,column=0,columnspan=2,sticky='w',pady=25)
  setup.columnconfigure(1,weight=1)
  top=ttk.Frame(route);top.pack(fill='x')
  for label,var,w in [('Profession',self.prof,18),('From skill',self.start,8),('To skill',self.target,8)]:
   ttk.Label(top,text=label).pack(side='left',padx=(0,5))
   if label=='Profession':ttk.Combobox(top,textvariable=var,values=PROFESSIONS,state='readonly',width=w).pack(side='left',padx=(0,15))
   else:ttk.Entry(top,textvariable=var,width=w).pack(side='left',padx=(0,15))
  ttk.Checkbutton(route,text='Require Forever-verified trainer recipes',variable=self.verified).pack(anchor='w',pady=10)
  ttk.Button(route,text='Calculate cheapest route',command=self.calculate).pack(anchor='w',pady=4)
  self.summary=ttk.Label(route,text='No route calculated yet.',font=('Segoe UI',11,'bold'));self.summary.pack(anchor='w',pady=12)
  ttk.Label(route,text='Crafting route').pack(anchor='w')
  self.route_tree=self.make_table(route,('skill','recipe','crafts','gold'),('Skill range','Recipe','Expected crafts','Estimated gold'))
  ttk.Label(route,text='Shopping list (item IDs)').pack(anchor='w',pady=(10,0))
  self.shop_tree=self.make_table(route,('item','quantity','gold'),('Item ID','Buy quantity','Estimated gold'))
  ttk.Button(route,text='Export route and shopping list as CSV',command=self.export).pack(anchor='w',pady=8)
  # Market tools operate on imported or fetched snapshots; no fictional data.
  ttk.Label(market,text='Market snapshots & vendor arbitrage',font=('Segoe UI',15,'bold')).pack(anchor='w')
  ttk.Label(market,text='CSV columns: item_id,quantity,unit_copper. Values are COPPER per item. Use real exports only.',wraplength=820).pack(anchor='w',pady=6)
  actions=ttk.Frame(market);actions.pack(fill='x',pady=8)
  ttk.Button(actions,text='Import AH CSV',command=self.import_ah_csv).pack(side='left',padx=(0,10))
  ttk.Button(actions,text='Import vendor values CSV',command=self.import_vendor_csv).pack(side='left',padx=(0,10))
  ttk.Button(actions,text='Scan vendor deals',command=self.scan_vendor).pack(side='left',padx=(0,10))
  ttk.Label(market,text='Vendor CSV columns: item_id,vendor_copper. Profits exclude travel/time costs.').pack(anchor='w')
  self.vendor_tree=self.make_table(market,('item','buy','vendor','qty','profit'),('Item ID','Buyout / item (g)','Vendor / item (g)','Quantity','Total profit (g)'))
  ttk.Label(market,text='Historical item prices (snapshots grouped by hour, UTC)').pack(anchor='w',pady=(10,2))
  finder=ttk.Frame(market);finder.pack(fill='x')
  self.market_item=tk.StringVar();ttk.Entry(finder,textvariable=self.market_item,width=18).pack(side='left')
  ttk.Button(finder,text='Analyse item ID',command=self.market_history).pack(side='left',padx=8)
  self.history_tree=self.make_table(market,('hour','observations','median','minimum'),('UTC hour','Snapshots','Median min buyout (g)','Lowest observed (g)'))
  self.market_note=ttk.Label(market,text='No live data assumed. Repeated snapshots are needed to infer time-of-day patterns.',wraplength=850);self.market_note.pack(anchor='w',pady=5)
  ttk.Label(self,textvariable=self.status,wraplength=1000).pack(fill='x',padx=15,pady=(0,12))
 def make_table(self,parent,keys,headers):
  frame=ttk.Frame(parent);frame.pack(fill='both',expand=True,pady=4)
  tree=ttk.Treeview(frame,columns=keys,show='headings',height=7)
  for k,h in zip(keys,headers):tree.heading(k,text=h);tree.column(k,width=125 if k!='recipe' else 300)
  scroll=ttk.Scrollbar(frame,orient='vertical',command=tree.yview);tree.configure(yscrollcommand=scroll.set)
  tree.pack(side='left',fill='both',expand=True);scroll.pack(side='right',fill='y');return tree
 def run_job(self,desc,fn):
  self.status.set(desc+' ...')
  def work():
   try:
    result=fn();self.after(0,lambda:self.status.set(str(result)))
   except Exception as exc:
    msg=f'{type(exc).__name__}: {exc}';self.after(0,lambda:self.status.set(msg));self.after(0,lambda:messagebox.showerror('Request failed',msg))
  threading.Thread(target=work,daemon=True).start()
 def discover(self):
  def job():
   houses=auction_houses(oauth(self.client.get(),self.secret.get()))
   return 'Auction houses (verify faction and ruleset): '+', '.join(f"{x.get('id')} {x.get('name','')}" for x in houses)[:850]
  self.run_job('Discovering auction houses',job)
 def refresh(self):
  self.run_job('Fetching auction listings',lambda: 'Imported %s listings, snapshot %s'%fetch_auctions(self.client.get(),self.secret.get(),int(self.house.get())))
 def import_recipes(self):
  self.run_job('Importing recipes',lambda:f"Imported {fetch_recipes(self.prof.get(),self.fdb.get())} recipes for {self.prof.get()}")
 def calculate(self):
  try:
   start,target=int(self.start.get()),int(self.target.get());house=int(self.house.get())
   if not (1<=start<target<=300):raise ValueError('Choose skill range between 1 and 300, with target greater than start')
   recipes=recipes_for(self.prof.get());prices,stamp=latest_prices(house)
   if not recipes or not prices:raise ValueError('Import recipes and fetch an AH snapshot first')
   result=optimize(recipes,build_price_book(prices),start,target,require_verified=self.verified.get())
   if 'error' in result:raise ValueError(result['error'])
   self.result=result
   for tree in (self.route_tree,self.shop_tree):tree.delete(*tree.get_children())
   for s in result['steps']:self.route_tree.insert('', 'end',values=(f"{s['from']}–{s['to']}",s['recipe'],f"{s['expected_crafts']:.1f}",f"{s['cost_copper']/10000:.2f}"))
   for s in result['shopping']:self.shop_tree.insert('','end',values=(s['item_id'],s['buy_quantity'],f"{s['estimated_copper']/10000:.2f}"))
   self.summary.config(text=f"Expected material cost: {result['expected_copper']/10000:,.2f} gold  |  {len(result['steps'])} crafting stages")
   self.status.set('Calculated from cached snapshot '+str(stamp)+'. Skill-up chances approximate; total costs not guaranteed.')
   if result['shortage']:messagebox.showwarning('Market depth','Not enough listings for some materials. Shopping costs may be incomplete.')
  except Exception as e:messagebox.showerror('Cannot calculate',str(e))
 def import_ah_csv(self):
  file=filedialog.askopenfilename(title='Select AH listings CSV',filetypes=[('CSV files','*.csv')]);
  if not file:return
  try:
   rows=[]
   with open(file,encoding='utf-8-sig',newline='') as f:
    for r in csv.DictReader(f):
     item=int(r['item_id']);qty=float(r['quantity']);price=float(r['unit_copper'])
     if item>0 and qty>0 and price>0:rows.append((item,qty,price))
   if not rows:raise ValueError('No valid listings')
   from data_sources import connect
   stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();house=int(self.house.get())
   with connect() as c:c.executemany('INSERT INTO prices VALUES (?,?,?,?,?)',[(house,stamp,*r) for r in rows])
   self.status.set(f'Imported {len(rows)} real CSV listings at {stamp}. Market ID {house}.')
  except Exception as e:messagebox.showerror('CSV import failed',str(e))
 def import_vendor_csv(self):
  file=filedialog.askopenfilename(title='Select verified vendor sell values CSV',filetypes=[('CSV files','*.csv')]);
  if not file:return
  try:
   from data_sources import connect
   values=[]
   with open(file,encoding='utf-8-sig',newline='') as f:
    for r in csv.DictReader(f):
     item=int(r['item_id']);price=float(r['vendor_copper'])
     if item>0 and price>0:values.append((item,price))
   with connect() as c:
    c.execute('CREATE TABLE IF NOT EXISTS vendor_values (item_id INTEGER PRIMARY KEY, vendor_copper REAL)')
    c.executemany('INSERT OR REPLACE INTO vendor_values VALUES (?,?)',values)
   self.status.set(f'Imported {len(values)} verified vendor prices.')
  except Exception as e:messagebox.showerror('Vendor CSV import failed',str(e))
 def scan_vendor(self):
  try:
   from data_sources import connect,latest_prices
   rows,stamp=latest_prices(int(self.house.get()))
   with connect() as c:
    c.execute('CREATE TABLE IF NOT EXISTS vendor_values (item_id INTEGER PRIMARY KEY, vendor_copper REAL)')
    values=dict(c.execute('SELECT item_id,vendor_copper FROM vendor_values').fetchall())
   deals=[]
   for r in rows:
    vendor=values.get(r['item_id'],0)
    if vendor>r['unit_copper']:
     profit=(vendor-r['unit_copper'])*r['quantity']
     deals.append((r['item_id'],r['unit_copper']/10000,vendor/10000,r['quantity'],profit/10000))
   deals.sort(key=lambda r:r[4],reverse=True)
   self.vendor_tree.delete(*self.vendor_tree.get_children())
   for item,buy,vendor,qty,profit in deals[:500]:self.vendor_tree.insert('','end',values=(item,f'{buy:.4f}',f'{vendor:.4f}',f'{qty:g}',f'{profit:.4f}'))
   self.status.set(f'{len(deals)} below-vendor listings found in snapshot {stamp or "none"}. Verify item variants and vendor values in game.')
  except Exception as e:messagebox.showerror('Vendor scan failed',str(e))
 def market_history(self):
  try:
   item=int(self.market_item.get());house=int(self.house.get())
   from data_sources import connect
   with connect() as c:rows=c.execute('SELECT captured,MIN(unit_copper) FROM prices WHERE house=? AND item_id=? GROUP BY captured ORDER BY captured',(house,item)).fetchall()
   buckets={}
   for captured,price in rows:
    hour=datetime.datetime.fromisoformat(captured).hour
    buckets.setdefault(hour,[]).append(price/10000)
   self.history_tree.delete(*self.history_tree.get_children())
   for hour,prices in sorted(buckets.items()):self.history_tree.insert('','end',values=(f'{hour:02d}:00',len(prices),f'{statistics.median(prices):.4f}',f'{min(prices):.4f}'))
   self.market_note.config(text=f'{len(rows)} snapshots for item {item}. Hours are UTC. These are observed listing prices, not completed sales; small samples are unreliable.')
  except Exception as e:messagebox.showerror('History failed',str(e))
 def export(self):
  if not self.result:return messagebox.showinfo('No route','Calculate a route first.')
  folder=filedialog.askdirectory(title='Choose export folder')
  if not folder:return
  for name,rows in [('route',self.result['steps']),('shopping',self.result['shopping'])]:
   with open(Path(folder)/f'forever_{name}.csv','w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else []);writer.writeheader();writer.writerows(rows)
  messagebox.showinfo('Exported','CSV files saved.')

if __name__=='__main__':App().mainloop()
