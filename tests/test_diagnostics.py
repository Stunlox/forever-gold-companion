import unittest
from diagnostics import planner_diagnostics, format_auction_houses

class DiagnosticsTests(unittest.TestCase):
    def test_both_missing(self):
        self.assertIn('AND refresh',planner_diagnostics('blacksmithing',110,0,0,None))
    def test_recipes_missing(self):
        self.assertIn('Missing profession recipes',planner_diagnostics('blacksmithing',110,0,10,'2026-11-14T10:00:00+00:00'))
    def test_auction_missing(self):
        self.assertIn('Missing auction listings',planner_diagnostics('blacksmithing',110,4,0,None))
    def test_ready(self):
        self.assertIn('Both datasets available',planner_diagnostics('blacksmithing',110,4,10,'2026-11-14T10:00:00+00:00'))
    def test_auction_format(self):
        rows=format_auction_houses([{'key':{'href':'https://example.com/auctions/110?namespace=foo'},'name':{'en_US':'Alliance Auction House'}}])
        self.assertEqual(rows[0][0],'110')
        self.assertEqual(rows[0][1],'Alliance Auction House')
