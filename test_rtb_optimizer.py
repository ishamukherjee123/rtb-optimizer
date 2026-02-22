"""
Test Suite for RTB Optimizer
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.auction import AuctionSimulator, MarketDynamics, generate_sample_requests
from simulation.bid_request import BidRequest, User, Device, Impression, DeviceType, AdFormat
from strategies.fixed import FixedBidStrategy
from strategies.dynamic import DynamicBidStrategy
from analytics.performance import PerformanceAnalyzer
from analytics.optimizer import BudgetOptimizer, Campaign


class TestBidRequest(unittest.TestCase):
    """Test bid request generation"""
    
    def test_bid_request_creation(self):
        """Test basic bid request creation"""
        req = BidRequest()
        self.assertIsNotNone(req.request_id)
        self.assertIsNotNone(req.timestamp)
        self.assertGreater(req.floor_price, 0)
        
    def test_bid_request_serialization(self):
        """Test bid request to dict conversion"""
        req = BidRequest()
        req_dict = req.to_dict()
        self.assertIn('request_id', req_dict)
        self.assertIn('user', req_dict)
        self.assertIn('device', req_dict)
        

class TestAuctionSimulator(unittest.TestCase):
    """Test auction simulation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.market = MarketDynamics(avg_competitors=3, volatility=0.2)
        self.simulator = AuctionSimulator(market_dynamics=self.market)
        
    def test_single_auction(self):
        """Test running a single auction"""
        req = BidRequest()
        result = self.simulator.run_auction(req, bid=5.0)
        
        self.assertIsNotNone(result)
        self.assertIn(result.did_win, [True, False])
        if result.did_win:
            self.assertGreater(result.winning_price, 0)
    
    def test_batch_simulation(self):
        """Test batch auction simulation"""
        requests = generate_sample_requests(100, seed=42)
        strategy = FixedBidStrategy(2.5)
        
        results = self.simulator.simulate_batch(requests, strategy)
        
        self.assertEqual(len(results), 100)
        wins = sum(1 for r in results if r.did_win)
        self.assertGreater(wins, 0)
        self.assertLess(wins, 100)
        

class TestBidStrategies(unittest.TestCase):
    """Test bid strategies"""
    
    def test_fixed_strategy(self):
        """Test fixed bid strategy"""
        strategy = FixedBidStrategy(bid_amount=3.0)
        req = BidRequest()
        
        bid = strategy.get_bid(req)
        self.assertEqual(bid, 3.0)
        
    def test_dynamic_strategy(self):
        """Test dynamic bid strategy"""
        strategy = DynamicBidStrategy(
            base_bid=1.0,
            max_bid=10.0,
            target_cpa=15.0
        )
        req = BidRequest()
        
        bid = strategy.get_bid(req)
        self.assertGreaterEqual(bid, 1.0)
        self.assertLessEqual(bid, 10.0)
        
    def test_strategy_stats(self):
        """Test strategy statistics tracking"""
        strategy = FixedBidStrategy(2.5)
        simulator = AuctionSimulator()
        
        requests = generate_sample_requests(50, seed=42)
        results = simulator.simulate_batch(requests, strategy)
        
        stats = strategy.get_stats()
        self.assertEqual(stats['total_auctions'], 50)
        self.assertIn('win_rate', stats)
        self.assertIn('avg_cpa', stats)
        

class TestPerformanceAnalyzer(unittest.TestCase):
    """Test performance analytics"""
    
    def setUp(self):
        """Set up test data"""
        self.simulator = AuctionSimulator()
        self.requests = generate_sample_requests(100, seed=42)
        self.strategy = FixedBidStrategy(2.5)
        self.results = self.simulator.simulate_batch(self.requests, self.strategy)
        
    def test_analyze_strategy(self):
        """Test strategy analysis"""
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze_strategy('Test Strategy', self.results, self.requests)
        
        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.total_auctions, 100)
        self.assertGreaterEqual(metrics.win_rate, 0)
        self.assertLessEqual(metrics.win_rate, 1)
        
    def test_compare_strategies(self):
        """Test strategy comparison"""
        analyzer = PerformanceAnalyzer()
        
        strategy2 = DynamicBidStrategy()
        results2 = self.simulator.simulate_batch(self.requests, strategy2)
        
        comparison = analyzer.compare_strategies({
            'Fixed': self.results,
            'Dynamic': results2
        })
        
        self.assertEqual(len(comparison), 2)
        self.assertIn('Strategy', comparison.columns)
        
    def test_generate_insights(self):
        """Test insight generation"""
        analyzer = PerformanceAnalyzer()
        metrics = analyzer.analyze_strategy('Test', self.results, self.requests)
        
        insights = analyzer.generate_insights(metrics)
        self.assertIsInstance(insights, list)
        

class TestBudgetOptimizer(unittest.TestCase):
    """Test budget optimization"""
    
    def test_optimize_allocation(self):
        """Test budget allocation optimization"""
        optimizer = BudgetOptimizer()
        
        campaigns = [
            Campaign('c1', 'Campaign 1', 12.0, 0.02, 50.0, 10000),
            Campaign('c2', 'Campaign 2', 15.0, 0.015, 60.0, 8000),
            Campaign('c3', 'Campaign 3', 10.0, 0.025, 45.0, 12000),
        ]
        
        allocations = optimizer.optimize_allocation(campaigns, 10000)
        
        self.assertEqual(len(allocations), 3)
        total_allocated = sum(a.allocated_budget for a in allocations)
        self.assertLessEqual(total_allocated, 10000)
        
    def test_daily_pacing(self):
        """Test daily budget pacing"""
        optimizer = BudgetOptimizer()
        
        hourly_budgets = optimizer.optimize_daily_pacing(
            total_daily_budget=1000,
            hours_remaining=8,
            spent_so_far=200
        )
        
        self.assertEqual(len(hourly_budgets), 8)
        self.assertAlmostEqual(sum(hourly_budgets), 800, places=1)
        

class TestMarketDynamics(unittest.TestCase):
    """Test market dynamics simulation"""
    
    def test_competition_generation(self):
        """Test competitor generation"""
        market = MarketDynamics(avg_competitors=5)
        req = BidRequest()
        
        competitors = market.generate_competition(req)
        self.assertGreater(competitors, 0)
        
    def test_competitor_bids(self):
        """Test competitor bid generation"""
        market = MarketDynamics()
        req = BidRequest()
        
        bids = market.generate_competitor_bids(5, 0.5, req)
        
        self.assertEqual(len(bids), 5)
        for bid in bids:
            self.assertGreaterEqual(bid, 0.5)
        # Bids should be sorted descending
        self.assertEqual(bids, sorted(bids, reverse=True))
        

def run_tests():
    """Run all tests"""
    unittest.main()


if __name__ == '__main__':
    run_tests()
