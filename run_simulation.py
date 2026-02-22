"""
Main Simulation Runner
Orchestrates full auction simulation and analysis
"""

import json
import numpy as np
from datetime import datetime
from typing import List, Dict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.auction import AuctionSimulator, MarketDynamics, generate_sample_requests
from simulation.bid_request import BidRequest
from strategies.fixed import FixedBidStrategy
from strategies.dynamic import DynamicBidStrategy
from strategies.ml_strategy import MLBidStrategy
from analytics.performance import PerformanceAnalyzer


def run_simulation(num_auctions: int = 10000,
                   strategies_to_test: List[str] = None,
                   output_file: str = 'simulation_results.json',
                   verbose: bool = True) -> Dict:
    """
    Run complete simulation comparing multiple strategies
    
    Args:
        num_auctions: Number of auctions to simulate
        strategies_to_test: List of strategy names ('fixed', 'dynamic', 'ml')
        output_file: Where to save results
        verbose: Print progress
        
    Returns:
        Dict with complete results
    """
    if strategies_to_test is None:
        strategies_to_test = ['fixed', 'dynamic', 'ml']
    
    if verbose:
        print(f"🎯 RTB Optimizer Simulation")
        print(f"{'='*60}")
        print(f"Auctions: {num_auctions:,}")
        print(f"Strategies: {', '.join(strategies_to_test)}")
        print(f"{'='*60}\n")
    
    # Generate bid requests
    if verbose:
        print("📊 Generating bid requests...")
    
    bid_requests = generate_sample_requests(num_auctions, seed=42)
    
    # Initialize simulator
    market = MarketDynamics(
        avg_competitors=5,
        volatility=0.3,
        floor_price_mean=0.5,
        floor_price_std=0.2
    )
    simulator = AuctionSimulator(market_dynamics=market)
    
    # Initialize strategies
    strategies = {}
    if 'fixed' in strategies_to_test:
        strategies['Fixed Bid ($2.50)'] = FixedBidStrategy(bid_amount=2.5)
    
    if 'dynamic' in strategies_to_test:
        strategies['Dynamic Bid'] = DynamicBidStrategy(
            base_bid=1.5,
            max_bid=12.0,
            target_cpa=15.0,
            aggressiveness=1.2
        )
    
    if 'ml' in strategies_to_test:
        strategies['ML-Powered'] = MLBidStrategy(
            base_bid=1.5,
            max_bid=12.0,
            target_cpa=15.0,
            exploration_rate=0.05,
            min_training_samples=100
        )
    
    # Run simulations
    all_results = {}
    
    for strategy_name, strategy in strategies.items():
        if verbose:
            print(f"\n🔄 Running {strategy_name}...")
        
        results = simulator.simulate_batch(bid_requests, strategy)
        all_results[strategy_name] = results
        
        # Quick stats
        wins = sum(1 for r in results if r.did_win)
        conversions = sum(1 for r in results if r.converted)
        spend = sum(r.winning_price for r in results if r.did_win)
        revenue = sum(r.revenue for r in results)
        
        if verbose:
            print(f"  ✓ Wins: {wins:,} ({wins/len(results)*100:.1f}%)")
            print(f"  ✓ Conversions: {conversions:,}")
            print(f"  ✓ Spend: ${spend:,.2f}")
            print(f"  ✓ Revenue: ${revenue:,.2f}")
            print(f"  ✓ ROAS: {revenue/spend if spend > 0 else 0:.2f}x")
    
    # Analyze and compare
    if verbose:
        print(f"\n{'='*60}")
        print("📈 PERFORMANCE ANALYSIS")
        print(f"{'='*60}\n")
    
    analyzer = PerformanceAnalyzer()
    comparison_df = analyzer.compare_strategies(all_results)
    
    if verbose:
        print(comparison_df.to_string(index=False))
    
    # Generate insights for best strategy
    best_strategy = None
    best_roas = 0
    
    for strategy_name, results in all_results.items():
        metrics = analyzer.analyze_strategy(strategy_name, results, bid_requests)
        if metrics.roas > best_roas:
            best_roas = metrics.roas
            best_strategy = (strategy_name, metrics)
    
    if verbose and best_strategy:
        print(f"\n{'='*60}")
        print(f"🏆 BEST STRATEGY: {best_strategy[0]}")
        print(f"{'='*60}")
        insights = analyzer.generate_insights(best_strategy[1])
        for insight in insights:
            print(f"  {insight}")
    
    # Statistical significance tests
    if len(strategies) >= 2:
        if verbose:
            print(f"\n{'='*60}")
            print("📊 STATISTICAL SIGNIFICANCE")
            print(f"{'='*60}\n")
        
        strategy_names = list(all_results.keys())
        for i in range(len(strategy_names)):
            for j in range(i + 1, len(strategy_names)):
                sig_test = analyzer.statistical_significance(
                    all_results[strategy_names[i]],
                    all_results[strategy_names[j]],
                    metric='win_rate'
                )
                
                if verbose and sig_test.get('significant'):
                    print(f"{strategy_names[i]} vs {strategy_names[j]}:")
                    print(f"  Win Rate: {sig_test['strategy_a_value']:.2%} vs {sig_test['strategy_b_value']:.2%}")
                    print(f"  Significant: {'Yes' if sig_test['significant'] else 'No'} (p={sig_test['p_value']:.4f})")
    
    # Save results
    output_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'num_auctions': num_auctions,
            'strategies': list(strategies.keys())
        },
        'comparison': comparison_df.to_dict(orient='records'),
        'detailed_results': {
            name: [
                {
                    'request_id': r.request_id,
                    'did_win': r.did_win,
                    'winning_price': r.winning_price,
                    'converted': r.converted,
                    'revenue': r.revenue,
                    'num_competitors': r.num_competitors
                }
                for r in results
            ]
            for name, results in all_results.items()
        }
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    if verbose:
        print(f"\n✅ Results saved to {output_file}")
    
    return output_data


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run RTB Optimizer simulation')
    parser.add_argument('--auctions', type=int, default=10000,
                       help='Number of auctions to simulate')
    parser.add_argument('--strategies', nargs='+', 
                       choices=['fixed', 'dynamic', 'ml', 'all'],
                       default=['all'],
                       help='Strategies to test')
    parser.add_argument('--output', type=str, default='simulation_results.json',
                       help='Output file path')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress output')
    
    args = parser.parse_args()
    
    strategies = ['fixed', 'dynamic', 'ml'] if 'all' in args.strategies else args.strategies
    
    run_simulation(
        num_auctions=args.auctions,
        strategies_to_test=strategies,
        output_file=args.output,
        verbose=not args.quiet
    )
