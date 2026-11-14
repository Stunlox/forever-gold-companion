import unittest
from engine import chance, normalize_recipe, valid, build_price_book, material_cost, optimize

class EngineTests(unittest.TestCase):
    def test_skill_chance_bounds(self):
        self.assertEqual(chance(10, 20, 30, 40, 50), 1.0)
        self.assertEqual(chance(50, 20, 30, 40, 50), 0.0)
    def test_market_depth(self):
        book=build_price_book([
            {"item_id": 1, "quantity": 2, "unit_copper": 100},
            {"item_id": 1, "quantity": 3, "unit_copper": 200}])
        self.assertEqual(material_cost(book, 1, 4), 600)
        self.assertEqual(material_cost(book, 1, 6), float("inf"))
    def test_optimiser(self):
        recipe={"id":"x","name":"Sample","mats":{1:1},"output_id":2,
                "output_count":1,"trainer":True,"automatic":False,
                "verified":True,"skill":{"orange":1,"yellow":100,"green":150,"grey":200}}
        result=optimize([recipe],build_price_book([
            {"item_id":1,"quantity":100,"unit_copper":50}]),1,5)
        self.assertNotIn("error",result)
        self.assertEqual(result["expected_copper"],200)
        self.assertEqual(result["shopping"][0]["buy_quantity"],4)

if __name__ == "__main__":
    unittest.main()
