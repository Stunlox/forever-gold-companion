import os,json,streamlit as st,pandas as pd
from engine import PROFESSIONS,optimize,build_price_book
from data_sources import fetch_recipes,recipes_for,fetch_auctions,latest_prices,auction_houses,oauth
st.set_page_config(page_title='Forever Profession Optimiser',page_icon='⚒️',layout='wide')
st.title('⚒️ WoW Forever Profession Optimiser')
st.caption('EU • Alliance • PvP | Trainer recipes | Expected-cost levelling routes')
st.info('Data from [ForeverDB.net](https://foreverdb.net). ForeverDB API access requires an approved key. Blizzard API access requires developer credentials. Neither source is affiliated with this project.')
with st.sidebar:
 st.header('Connections')
 fdb=st.text_input('ForeverDB API key',value=os.getenv('FOREVERDB_API_KEY',''),type='password')
 client=st.text_input('Blizzard client ID',value=os.getenv('BLIZZARD_CLIENT_ID',''))
 secret=st.text_input('Blizzard client secret',value=os.getenv('BLIZZARD_CLIENT_SECRET',''),type='password')
 st.caption('Credentials are used for requests in this session; do not publish them.')
 if st.button('Discover Alliance auction houses'):
  try:
   houses=auction_houses(oauth(client,secret))
   st.session_state['houses']=houses
  except Exception as e:st.error(str(e))
 if st.session_state.get('houses'):
  st.write([(x.get('id'),x.get('name')) for x in st.session_state['houses'] if 'Alliance' in str(x.get('name'))])
 st.warning('Select the EU PvP Alliance house using a verified market mapping. Ruleset 1 alone does NOT select PvP auctions.')
 house=st.number_input('Auction house ID (verify first)',min_value=100,max_value=999,value=110,step=1)
 if st.button('Refresh AH snapshot'):
  try:
   n,stamp=fetch_auctions(client,secret,int(house));st.success(f'Saved {n:,} listings at {stamp}')
  except Exception as e:st.error(str(e))
 st.divider()
 st.caption('No scheduled collection while this app is closed. Run it on a machine/server with a scheduler for automatic refresh.')
profession=st.selectbox('Profession',PROFESSIONS,index=5,format_func=str.title)
a,b,c=st.columns(3)
with a:start=st.number_input('Current skill',min_value=1,max_value=299,value=1)
with b:target=st.number_input('Target skill',min_value=2,max_value=300,value=300)
with c:verified=st.checkbox('Forever-verified trainers only',value=False)
if st.button('Import / refresh profession recipes'):
 try:
  n=fetch_recipes(profession,fdb);st.success(f'Imported {n} recipe records')
 except Exception as e:st.error(f'Import failed: {e}')
recipes=recipes_for(profession)
prices,stamp=latest_prices(int(house))
st.caption(f'{len(recipes)} recipe records cached • {len(prices):,} AH listings cached • snapshot {stamp or "none"}')
with st.expander('Optional inventory and pricing assumptions'):
 owned_text=st.text_area('Owned materials (JSON item ID to quantity)',value='{}')
 resale=st.checkbox('Estimate resale credit (speculative)',value=False)
 unknown=st.checkbox('Treat unknown materials as free (not recommended)',value=False)
try:owned={int(k):float(v) for k,v in json.loads(owned_text).items()}
except Exception:owned={};st.error('Inventory must be JSON, e.g. {"2589": 20}')
if st.button('Calculate cheapest expected route',type='primary'):
 if target<=start:st.error('Target must be higher than current skill.')
 elif not recipes:st.error('Import recipe data first.')
 elif not prices:st.error('Fetch an auction snapshot first.')
 else:
  result=optimize(recipes,build_price_book(prices),start,target,owned,resale,verified,'zero' if unknown else 'exclude')
  if 'error' in result:st.error(result['error']);st.caption(f"Eligible recipes: {result['covered']}")
  else:
   st.metric('Expected route material cost',f"{result['expected_copper']/10000:,.2f} gold")
   st.caption('Not a guarantee; skill-up probabilities are approximated. Trainer fees and travel are excluded.')
   st.subheader('Crafting route')
   df=pd.DataFrame(result['steps']);df['expected_gold']=df['cost_copper']/10000
   st.dataframe(df[['from','to','recipe','expected_crafts','expected_gold','verified']],hide_index=True,use_container_width=True)
   st.download_button('Download route CSV',df.to_csv(index=False),'forever_route.csv')
   st.subheader('Shopping list')
   shop=pd.DataFrame(result['shopping']);shop['estimated_gold']=shop['estimated_copper']/10000
   st.dataframe(shop[['item_id','expected_quantity','buy_quantity','estimated_gold']],hide_index=True,use_container_width=True)
   st.download_button('Download shopping CSV',shop.to_csv(index=False),'forever_shopping.csv')
   if result['shortage']:st.warning('Insufficient AH depth for some shopping-list quantities; totals may be understated.')
   for note in result['notes']:st.caption('• '+note)
st.divider()
st.caption('Developer note: recipes whose source or skill fields cannot be parsed are excluded. Inspect imported data before trusting an optimisation result.')
