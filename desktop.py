"""Forever Gold Companion 0.5 — PySide6 dark trading-terminal UI."""
import csv
import datetime as dt
import os
import statistics
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QFrame, QLineEdit, QComboBox, QCheckBox,
    QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QAbstractItemView, QScrollArea, QTabBar)

from engine import PROFESSIONS, optimize, build_price_book
from data_sources import (fetch_recipes, recipes_for, fetch_auctions, latest_prices,
                          auction_houses, oauth, connect)

os.environ.setdefault('FOREVER_DB', str(Path.home() / 'ForeverGoldCompanion' / 'market.sqlite3'))
Path(os.environ['FOREVER_DB']).parent.mkdir(parents=True, exist_ok=True)

STYLE = '''
QWidget { background: #0B1018; color: #DDE6F1; font-family: 'Segoe UI'; font-size: 12px; }
QMainWindow, QScrollArea { background: #0B1018; }
QFrame#sidebar { background: #101722; border-right: 1px solid #273347; }
QFrame#panel { background: #141E2B; border: 1px solid #273347; border-radius: 12px; }
QLabel#brand { color: #F4F7FB; font-size: 21px; font-weight: 800; }
QLabel#muted { color: #92A3B9; }
QLabel#heading { color: #F4F7FB; font-size: 25px; font-weight: 700; }
QLabel#section { color: #F1F5FB; font-size: 15px; font-weight: 700; }
QLabel#metric { color: #6BE2BA; font-size: 27px; font-weight: 800; }
QLabel#eyebrow { color: #91A8C4; font-size: 11px; font-weight: 700; }
QPushButton { background: #1C2A3B; border: 1px solid #34445B; border-radius: 8px;
 padding: 10px 14px; color: #E7EFF9; font-weight: 600; text-align: center; }
QPushButton:hover { background: #293D54; border-color: #5C7799; }
QPushButton#primary { background: #16A37F; border-color: #16A37F; color: #071711; }
QPushButton#primary:hover { background: #39C9A3; }
QPushButton#nav { text-align: left; background: transparent; border: none; padding: 13px 17px;
 color: #9AAEC5; font-size: 13px; }
QPushButton#nav:hover { background: #1D2A3A; color: white; }
QPushButton#nav[active="true"] { background: #1C3442; color: #78E5C4; border-left: 3px solid #43D8B0; border-radius: 0; }
QLineEdit, QComboBox { background: #0E1621; border: 1px solid #34445B; border-radius: 7px;
 padding: 9px 10px; color: #E8F0F9; min-height: 18px; }
QLineEdit:focus, QComboBox:focus { border: 1px solid #49C9A6; }
QComboBox QAbstractItemView { background: #172331; color: white; selection-background-color: #276957; }
QTableWidget { background: #111A26; alternate-background-color: #152130; border: 1px solid #2C3A4C;
 border-radius: 8px; gridline-color: #243144; selection-background-color: #235A52; }
QHeaderView::section { background: #1C2A3B; color: #AFC0D5; border: none;
 border-bottom: 1px solid #314157; padding: 10px; font-weight: 700; }
QTableWidget::item { padding: 6px; }
QCheckBox { spacing: 9px; }
QTabBar::tab { background: #1B2939; border: 1px solid #34445B; padding: 11px 18px; color: #AFC0D5; }
QTabBar::tab:selected { background: #145847; color: #F4FFFA; border-bottom: 2px solid #57DEBA; }
QTabBar::tab:hover { background: #2B4158; }
QScrollBar:vertical { background: #111A26; width: 10px; }
QScrollBar::handle:vertical { background: #34465B; border-radius: 4px; }
'''

class Bridge(QObject):
    done = Signal(str)
    failed = Signal(str)


def text_label(text, kind=None, wrap=False):
    label = QLabel(text)
    if kind: label.setObjectName(kind)
    label.setWordWrap(wrap)
    return label


def panel():
    frame = QFrame(); frame.setObjectName('panel')
    layout = QVBoxLayout(frame); layout.setContentsMargins(20, 18, 20, 20); layout.setSpacing(13)
    return frame, layout


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setAlternatingRowColors(True)
    widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    widget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    widget.verticalHeader().hide()
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    widget.setMinimumHeight(215)
    return widget


def fill_table(widget, rows):
    widget.setRowCount(0)
    for values in rows:
        r = widget.rowCount(); widget.insertRow(r)
        for col, value in enumerate(values):
            cell = QTableWidgetItem(str(value))
            if col: cell.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight)
            widget.setItem(r, col, cell)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Forever Gold Companion | Market Terminal')
        self.resize(1240, 830); self.setMinimumSize(950, 650)
        self.pool = ThreadPoolExecutor(max_workers=2)
        self.bridge = Bridge()
        self.bridge.done.connect(self.set_status)
        self.bridge.failed.connect(self.show_error)
        self.result = None
        root = QWidget(); self.setCentralWidget(root)
        outer = QHBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        sidebar = QFrame(); sidebar.setObjectName('sidebar'); sidebar.setFixedWidth(236)
        side = QVBoxLayout(sidebar); side.setContentsMargins(16,25,16,18); side.setSpacing(9)
        side.addWidget(text_label('◈  FOREVER', 'brand'))
        side.addWidget(text_label('GOLD COMPANION   /   v0.5', 'muted'))
        side.addSpacing(28)
        self.nav=[]
        for i, (icon, name) in enumerate([('▦','Overview'),('▤','Profession planner'),('↗','Market scanner'),('▥','Auction browser'),('◷','Price history'),('⚙','Connections')]):
            b=QPushButton(f'{icon}   {name}'); b.setObjectName('nav'); b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _, ix=i: self.go(ix)); side.addWidget(b); self.nav.append(b)
        side.addStretch()
        side.addWidget(text_label('EU PvP Alliance', 'section'))
        side.addWidget(text_label('Market data: manual import or experimental API', 'muted', True))
        side.addWidget(text_label('UNOFFICIAL COMMUNITY TOOL', 'eyebrow'))
        outer.addWidget(sidebar)
        right=QWidget(); main=QVBoxLayout(right); main.setContentsMargins(28,23,28,18); main.setSpacing(13)
        top=QHBoxLayout(); top.addWidget(text_label('MARKET INTELLIGENCE  /  EU PVP', 'eyebrow')); top.addStretch()
        self.data_indicator=text_label('●  No snapshot loaded', 'muted'); top.addWidget(self.data_indicator)
        main.addLayout(top)
        self.pages=QStackedWidget(); main.addWidget(self.pages, 1)
        self.status=text_label('Ready. Import real auction CSV data or configure an experimental connection.', 'muted', True)
        main.addWidget(self.status)
        outer.addWidget(right,1)
        self.make_overview(); self.make_professions(); self.make_market(); self.make_browser(); self.make_history(); self.make_connections()
        self.go(0); self.update_overview()

    def page(self, title, subtitle):
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        body=QWidget(); layout=QVBoxLayout(body); layout.setContentsMargins(2,4,2,8); layout.setSpacing(17)
        layout.addWidget(text_label(title,'heading'))
        layout.addWidget(text_label(subtitle,'muted',True))
        scroll.setWidget(body); self.pages.addWidget(scroll)
        return layout

    def make_overview(self):
        lay=self.page('Overview', 'Your auction intelligence workspace. All figures are sourced from locally stored snapshots.')
        metrics=QHBoxLayout(); self.metrics=[]
        for name in ['LATEST LISTINGS','UNIQUE ITEMS','CAPTURED (UTC)']:
            box,l=panel(); l.addWidget(text_label(name,'eyebrow')); v=text_label('—','metric'); l.addWidget(v); metrics.addWidget(box); self.metrics.append(v)
        lay.addLayout(metrics)
        box,l=panel(); l.addWidget(text_label('START HERE','section'))
        l.addWidget(text_label('1  Import an auction CSV (item_id, quantity, unit_copper).\n2  Import verified vendor values to scan for below-vendor deals.\n3  Add verified profession recipes to calculate levelling routes.\n4  Repeat imports over time to build an observed price history.','muted',True))
        row=QHBoxLayout()
        for title,fn in [('Import auction CSV',self.import_ah),('Open market scanner',lambda:self.go(2)),('Configure sources',lambda:self.go(5))]:
            b=QPushButton(title); b.clicked.connect(fn); row.addWidget(b)
        l.addLayout(row); lay.addWidget(box)
        box,l=panel(); l.addWidget(text_label('DATA INTEGRITY','section'))
        l.addWidget(text_label('No simulated market values are displayed. Listings are asking prices, not completed sales. Blizzard/ForeverDB integrations are experimental and require verification for Forever realms.','muted',True))
        lay.addWidget(box); lay.addStretch()

    def make_professions(self):
        lay=self.page('Profession planner', 'Estimate the cheapest levelling route from imported recipes and your current auction snapshot.')
        box,l=panel(); grid=QGridLayout();
        self.prof=QComboBox(); self.prof.addItems(PROFESSIONS)
        self.start=QLineEdit('1'); self.target=QLineEdit('300')
        self.verified=QCheckBox('Require verified trainer recipes')
        for i,(name,widget) in enumerate([('Profession',self.prof),('Current skill',self.start),('Target skill',self.target)]):
            grid.addWidget(text_label(name,'eyebrow'),0,i); grid.addWidget(widget,1,i)
        l.addLayout(grid); l.addWidget(self.verified)
        btn=QPushButton('Calculate cheapest route'); btn.setObjectName('primary'); btn.clicked.connect(self.calculate); l.addWidget(btn)
        lay.addWidget(box)
        self.route_summary=text_label('No route calculated yet.','section'); lay.addWidget(self.route_summary)
        box,l=panel(); l.addWidget(text_label('CRAFTING ROUTE','section'))
        self.route_table=table(['Skill range','Recipe','Expected crafts','Cost (gold)']); l.addWidget(self.route_table); lay.addWidget(box)
        box,l=panel(); l.addWidget(text_label('SHOPPING LIST','section'))
        self.shop_table=table(['Item ID','Buy quantity','Estimated gold']); l.addWidget(self.shop_table)
        export=QPushButton('Export route + shopping CSV'); export.clicked.connect(self.export); l.addWidget(export)
        lay.addWidget(box)

    def make_market(self):
        lay=self.page('Market scanner', 'Spot auction listings priced below verified vendor sell values.')
        box,l=panel(); row=QHBoxLayout()
        for name,fn in [('Import AH CSV',self.import_ah),('Import vendor CSV',self.import_vendor),('Scan vendor flips',self.scan_vendor)]:
            b=QPushButton(name); b.clicked.connect(fn); row.addWidget(b)
        l.addLayout(row); l.addWidget(text_label('Auction CSV: item_id,quantity,unit_copper  •  Vendor CSV: item_id,vendor_copper. All source values must be in copper.','muted',True)); lay.addWidget(box)
        box,l=panel(); l.addWidget(text_label('BELOW-VENDOR OPPORTUNITIES','section'))
        self.deal_table=table(['Item ID','AH / item (g)','Vendor / item (g)','Quantity','Potential profit (g)'])
        l.addWidget(self.deal_table); lay.addWidget(box)
        lay.addWidget(text_label('Potential profit ignores travel, auction rules, and availability changes. Verify values before purchasing.','muted',True))

    def make_browser(self):
        lay=self.page('Auction house browser', 'Browse the latest AH snapshot by item category. Prices are asking prices, not confirmed sales.')
        box,l=panel()
        actions=QHBoxLayout()
        self.browser_search=QLineEdit(); self.browser_search.setPlaceholderText('Search item name or ID...')
        self.browser_search.textChanged.connect(self.refresh_browser)
        actions.addWidget(self.browser_search, 1)
        import_btn=QPushButton('Import item catalogue CSV'); import_btn.clicked.connect(self.import_catalogue)
        actions.addWidget(import_btn)
        reload_btn=QPushButton('Reload'); reload_btn.clicked.connect(self.refresh_browser); actions.addWidget(reload_btn)
        l.addLayout(actions)
        l.addWidget(text_label('Catalogue columns: item_id,name,category,subcategory. Unmatched items remain under Uncategorised; no category is guessed.', 'muted',True))
        lay.addWidget(box)
        self.category_tabs=QTabBar(); self.category_tabs.setExpanding(False); self.category_tabs.setUsesScrollButtons(True)
        self.category_tabs.currentChanged.connect(self.category_changed)
        lay.addWidget(self.category_tabs)
        self.subcategory_tabs=QTabBar(); self.subcategory_tabs.setExpanding(False); self.subcategory_tabs.setUsesScrollButtons(True)
        self.subcategory_tabs.currentChanged.connect(self.refresh_browser)
        lay.addWidget(self.subcategory_tabs)
        self.browser_note=text_label('Import a catalogue to classify auction items.', 'muted'); lay.addWidget(self.browser_note)
        box,l=panel()
        self.browser_table=table(['Item ID','Item name','Category','Subcategory','Listings','Quantity','Lowest (g)','Average (g)'])
        self.browser_table.setSortingEnabled(True)
        l.addWidget(self.browser_table)
        lay.addWidget(box)
        self.refresh_browser()

    def import_catalogue(self):
        path,_=QFileDialog.getOpenFileName(self,'Import item catalogue CSV','','CSV files (*.csv)')
        if not path:return
        try:
            values=[]
            with open(path,encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f)
                required={'item_id','name','category','subcategory'}
                if not required.issubset(set(reader.fieldnames or [])):
                    raise ValueError('Catalogue requires columns: item_id,name,category,subcategory')
                for row in reader:
                    item=int(row['item_id'])
                    if item>0:
                        values.append((item,(row['name'] or '').strip(),(row['category'] or 'Uncategorised').strip() or 'Uncategorised',
                                       (row['subcategory'] or 'Other').strip() or 'Other'))
            with connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS item_catalogue (item_id INTEGER PRIMARY KEY, name TEXT, category TEXT, subcategory TEXT)')
                db.executemany('INSERT OR REPLACE INTO item_catalogue VALUES (?,?,?,?)',values)
            self.refresh_browser()
            self.set_status(f'Imported {len(values):,} item catalogue records.')
        except Exception as e:self.show_error(str(e))

    def category_changed(self, _=None):
        cat=self.category_tabs.tabData(self.category_tabs.currentIndex())
        self.subcategory_tabs.blockSignals(True)
        self.subcategory_tabs.clear()
        self.subcategory_tabs.addTab('All'); self.subcategory_tabs.setTabData(0,'All')
        for sub in sorted({r[3] for r in getattr(self,'browser_rows',[]) if cat=='All' or r[2]==cat}):
            i=self.subcategory_tabs.addTab(sub); self.subcategory_tabs.setTabData(i,sub)
        self.subcategory_tabs.blockSignals(False)
        self.refresh_browser()

    def refresh_browser(self, _=None):
        if not hasattr(self,'browser_table'):return
        try:
            with connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS item_catalogue (item_id INTEGER PRIMARY KEY, name TEXT, category TEXT, subcategory TEXT)')
                house=self.house_id()
                latest=db.execute('SELECT MAX(captured) FROM prices WHERE house=?',(house,)).fetchone()[0]
                if latest:
                    data=db.execute("""SELECT p.item_id, COALESCE(NULLIF(c.name, ''), 'Unknown item'),
                        COALESCE(NULLIF(c.category, ''), 'Uncategorised'),
                        COALESCE(NULLIF(c.subcategory, ''), 'Other'), COUNT(*), SUM(p.quantity),
                        MIN(p.unit_copper), SUM(p.unit_copper*p.quantity)/SUM(p.quantity)
                        FROM prices p LEFT JOIN item_catalogue c ON p.item_id=c.item_id
                        WHERE p.house=? AND p.captured=? GROUP BY p.item_id,c.name,c.category,c.subcategory""",(house,latest)).fetchall()
                else:data=[]
            self.browser_rows=data
            current=self.category_tabs.tabData(self.category_tabs.currentIndex()) or 'All'
            categories=['All','Trade Goods','Armor','Weapons','Consumables','Recipes','Gems','Miscellaneous','Uncategorised']
            categories += sorted({r[2] for r in data}.difference(categories))
            if [self.category_tabs.tabData(i) for i in range(self.category_tabs.count())]!=categories:
                self.category_tabs.blockSignals(True); self.category_tabs.clear()
                for cat in categories:
                    ix=self.category_tabs.addTab(cat);self.category_tabs.setTabData(ix,cat)
                self.category_tabs.setCurrentIndex(categories.index(current) if current in categories else 0)
                self.category_tabs.blockSignals(False)
                self.category_changed()
                return
            category=self.category_tabs.tabData(self.category_tabs.currentIndex()) or 'All'
            sub=self.subcategory_tabs.tabData(self.subcategory_tabs.currentIndex()) or 'All'
            query=self.browser_search.text().strip().lower()
            filtered=[r for r in data if (category=='All' or r[2]==category) and (sub=='All' or r[3]==sub)
                      and (not query or query in str(r[0]) or query in r[1].lower())]
            self.browser_table.setSortingEnabled(False)
            fill_table(self.browser_table,[(r[0],r[1],r[2],r[3],r[4],f'{r[5]:,.0f}',f'{r[6]/10000:,.4f}',f'{r[7]/10000:,.4f}') for r in filtered[:5000]])
            self.browser_table.setSortingEnabled(True)
            self.browser_note.setText(f'{len(filtered):,} items in selection • Showing up to 5,000 • Snapshot: {latest or "none"} • {len(data):,} unique items total')
        except Exception as e:self.browser_note.setText(f'Browser unavailable: {e}')

    def make_history(self):
        lay=self.page('Price history', 'Observed minimum buyouts grouped by capture hour (UTC).')
        box,l=panel(); row=QHBoxLayout(); self.history_item=QLineEdit(); self.history_item.setPlaceholderText('Enter item ID')
        row.addWidget(self.history_item,1); b=QPushButton('Analyse item'); b.setObjectName('primary'); b.clicked.connect(self.history); row.addWidget(b); l.addLayout(row)
        l.addWidget(text_label('More snapshots improve time-of-day comparisons. This is not completed-sales data.','muted',True)); lay.addWidget(box)
        box,l=panel(); l.addWidget(text_label('HOURLY PRICE OBSERVATIONS','section'))
        self.history_table=table(['UTC hour','Snapshots','Median min (g)','Lowest observed (g)']); l.addWidget(self.history_table); lay.addWidget(box)
        self.history_note=text_label('No item selected.','muted'); lay.addWidget(self.history_note)

    def make_connections(self):
        lay=self.page('Connections & data', 'Import actual data locally. Experimental APIs are optional and not yet confirmed for WoW Forever.')
        box,l=panel(); grid=QGridLayout()
        self.house=QLineEdit('110'); self.key=QLineEdit(); self.key.setEchoMode(QLineEdit.EchoMode.Password)
        self.client=QLineEdit(); self.secret=QLineEdit(); self.secret.setEchoMode(QLineEdit.EchoMode.Password)
        for i,(name,widget) in enumerate([('Auction house ID (verify before use)',self.house),('ForeverDB API key',self.key),('Blizzard client ID',self.client),('Blizzard client secret',self.secret)]):
            grid.addWidget(text_label(name,'eyebrow'),i,0); grid.addWidget(widget,i,1)
        l.addLayout(grid)
        for name,fn in [('Discover AH IDs (experimental)',self.discover),('Refresh auction snapshot (experimental)',self.refresh),('Import profession recipes (experimental)',self.import_recipes)]:
            b=QPushButton(name); b.clicked.connect(fn); l.addWidget(b)
        l.addWidget(text_label('Credentials are not saved. The auction endpoints, namespace, realm mapping, and ForeverDB response format have not been independently validated. Never distribute your personal API secret in a public build.','muted',True))
        lay.addWidget(box); lay.addStretch()

    def go(self,index):
        self.pages.setCurrentIndex(index)
        for i,b in enumerate(self.nav):
            b.setProperty('active','true' if i==index else 'false'); b.style().unpolish(b); b.style().polish(b)
        if index==0:self.update_overview()
        if index==3:self.refresh_browser()

    def set_status(self,msg):
        self.status.setText(msg); self.update_overview()

    def show_error(self,msg):
        self.status.setText('Error: '+msg)
        QMessageBox.warning(self,'Operation failed',msg)

    def job(self,description,func):
        self.status.setText(description+' …')
        def runner():
            try: self.bridge.done.emit(str(func()))
            except Exception as e: self.bridge.failed.emit(f'{type(e).__name__}: {e}')
        self.pool.submit(runner)

    def house_id(self):
        val=int(self.house.text());
        if val<=0:raise ValueError('Auction house ID must be positive')
        return val

    def update_overview(self):
        try:
            rows,stamp=latest_prices(self.house_id())
            self.metrics[0].setText(f'{len(rows):,}')
            self.metrics[1].setText(f'{len({r["item_id"] for r in rows}):,}')
            self.metrics[2].setText(stamp[:16].replace('T',' ') if stamp else '—')
            self.data_indicator.setText('●  Snapshot loaded' if stamp else '●  No snapshot loaded')
        except Exception: pass

    def import_ah(self):
        path,_=QFileDialog.getOpenFileName(self,'Import auction listings CSV','','CSV files (*.csv)')
        if not path:return
        try:
            records=[]
            with open(path,encoding='utf-8-sig',newline='') as file:
                for row in csv.DictReader(file):
                    item=int(row['item_id']); qty=float(row['quantity']); price=float(row['unit_copper'])
                    if item>0 and qty>0 and price>0:records.append((item,qty,price))
            if not records:raise ValueError('No valid listings found')
            stamp=dt.datetime.now(dt.timezone.utc).isoformat(); house=self.house_id()
            with connect() as db: db.executemany('INSERT INTO prices VALUES (?,?,?,?,?)',[(house,stamp,*r) for r in records])
            self.set_status(f'Imported {len(records):,} listings at {stamp} (AH {house}).')
            self.refresh_browser()
        except Exception as e:self.show_error(str(e))

    def import_vendor(self):
        path,_=QFileDialog.getOpenFileName(self,'Import vendor values CSV','','CSV files (*.csv)')
        if not path:return
        try:
            values=[]
            with open(path,encoding='utf-8-sig',newline='') as file:
                for row in csv.DictReader(file):
                    item=int(row['item_id']); price=float(row['vendor_copper'])
                    if item>0 and price>0:values.append((item,price))
            with connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS vendor_values (item_id INTEGER PRIMARY KEY, vendor_copper REAL)')
                db.executemany('INSERT OR REPLACE INTO vendor_values VALUES (?,?)',values)
            self.set_status(f'Imported {len(values):,} verified vendor values.')
        except Exception as e:self.show_error(str(e))

    def scan_vendor(self):
        try:
            rows,stamp=latest_prices(self.house_id())
            with connect() as db:
                db.execute('CREATE TABLE IF NOT EXISTS vendor_values (item_id INTEGER PRIMARY KEY, vendor_copper REAL)')
                vendors=dict(db.execute('SELECT item_id,vendor_copper FROM vendor_values').fetchall())
            deals=[]
            for row in rows:
                vendor=vendors.get(row['item_id'],0)
                if vendor>row['unit_copper']:
                    profit=(vendor-row['unit_copper'])*row['quantity']/10000
                    deals.append((row['item_id'],f'{row["unit_copper"]/10000:.4f}',f'{vendor/10000:.4f}',f'{row["quantity"]:g}',f'{profit:.4f}'))
            deals.sort(key=lambda r:float(r[4]),reverse=True)
            fill_table(self.deal_table,deals[:500]); self.set_status(f'{len(deals):,} below-vendor listings in snapshot {stamp or "none"}.')
        except Exception as e:self.show_error(str(e))

    def calculate(self):
        try:
            start=int(self.start.text()); target=int(self.target.text())
            if not 1<=start<target<=300:raise ValueError('Skill must satisfy 1 ≤ current < target ≤ 300')
            recipes=recipes_for(self.prof.currentText()); prices,stamp=latest_prices(self.house_id())
            if not recipes or not prices:raise ValueError('Import profession recipes and an auction snapshot first')
            result=optimize(recipes,build_price_book(prices),start,target,require_verified=self.verified.isChecked())
            if 'error' in result:raise ValueError(result['error'])
            self.result=result
            fill_table(self.route_table,[(f'{s["from"]}–{s["to"]}',s['recipe'],f'{s["expected_crafts"]:.1f}',f'{s["cost_copper"]/10000:.2f}') for s in result['steps']])
            fill_table(self.shop_table,[(s['item_id'],s['buy_quantity'],f'{s["estimated_copper"]/10000:.2f}') for s in result['shopping']])
            self.route_summary.setText(f'Estimated cost  {result["expected_copper"]/10000:,.2f} gold    •    {len(result["steps"])} stages')
            self.set_status(f'Calculated from {stamp}. Skill-up probabilities are estimates, not guarantees.')
            if result['shortage']:QMessageBox.warning(self,'Limited market depth','Not enough listings to buy all estimated materials.')
        except Exception as e:self.show_error(str(e))

    def history(self):
        try:
            item=int(self.history_item.text()); house=self.house_id()
            with connect() as db:
                rows=db.execute('SELECT captured, MIN(unit_copper) FROM prices WHERE house=? AND item_id=? GROUP BY captured ORDER BY captured',(house,item)).fetchall()
            buckets={}
            for captured,price in rows:
                hour=dt.datetime.fromisoformat(captured).hour
                buckets.setdefault(hour,[]).append(price/10000)
            fill_table(self.history_table,[(f'{h:02d}:00',len(v),f'{statistics.median(v):.4f}',f'{min(v):.4f}') for h,v in sorted(buckets.items())])
            self.history_note.setText(f'{len(rows)} snapshots for item {item}. Observed listings, not completed sales.')
            self.set_status(f'Loaded hourly history for item {item}.')
        except Exception as e:self.show_error(str(e))

    def export(self):
        if not self.result:return self.show_error('Calculate a route before exporting.')
        folder=QFileDialog.getExistingDirectory(self,'Export route and shopping list')
        if not folder:return
        try:
            for name,rows in [('route',self.result['steps']),('shopping',self.result['shopping'])]:
                with open(Path(folder)/f'forever_{name}.csv','w',encoding='utf-8-sig',newline='') as f:
                    if rows:
                        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
            self.set_status('Route and shopping CSV files exported.')
        except Exception as e:self.show_error(str(e))

    def discover(self):
        client=self.client.text();secret=self.secret.text()
        self.job('Discovering AH IDs',lambda:'AH IDs (verify realm): '+str(auction_houses(oauth(client,secret)))[:700])

    def refresh(self):
        client=self.client.text();secret=self.secret.text()
        try:house=self.house_id()
        except Exception as e:return self.show_error(str(e))
        self.job('Refreshing auction snapshot',lambda:'Imported %s listings at %s'%fetch_auctions(client,secret,house))

    def import_recipes(self):
        profession=self.prof.currentText();key=self.key.text()
        self.job('Importing profession recipes',lambda:f'Imported {fetch_recipes(profession,key)} recipes for {profession}.')

    def closeEvent(self,event):
        self.pool.shutdown(wait=False,cancel_futures=True)
        super().closeEvent(event)


def main():
    app=QApplication(sys.argv); app.setStyle('Fusion'); app.setStyleSheet(STYLE)
    win=MainWindow();win.show()
    sys.exit(app.exec())

if __name__=='__main__':main()
