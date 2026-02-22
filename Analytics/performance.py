"""
Performance Analytics Module
Analyzes and compares bid strategy performance
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
from scipy import stats


@dataclass
class PerformanceMetrics:
    """Complete performance metrics for a strategy"""
    strategy_name: str
    total_auctions: int
    wins: int
    win_rate: float
    total_spend: float
    total_revenue: float
    conversions: int
    avg_cpa: float
    median_cpa: float
    roas: float
    avg_bid: float
    avg_winning_price: float
    budget_efficiency: float
    
    # Distribution metrics
    cpa_std: float
    win_rate_by_hour: Dict[int, float]
    spend_by_device: Dict[str, float]
    
    
class PerformanceAnalyzer:
    """Analyze strategy performance and generate insights"""
    
    def __init__(self):
        self.strategies_data = {}
        
    def analyze_strategy(self, 
                         strategy_name: str,
                         results: List,
                         bid_requests: Optional[List] = None) -> PerformanceMetrics:
        """
        Comprehensive analysis of a strategy's performance
        
        Args:
            strategy_name: Name of the strategy
            results: List of AuctionResult objects
            bid_requests: Optional list of corresponding bid requests
            
        Returns:
            PerformanceMetrics object
        """
        if not results:
            raise ValueError("No results to analyze")
        
        # Basic metrics
        wins = [r for r in results if r.did_win]
        conversions = [r for r in results if r.converted]
        
        total_spend = sum(r.winning_price for r in wins)
        total_revenue = sum(r.revenue for r in results)
        
        # CPA calculations
        cpas = []
        for r in conversions:
            if r.did_win:
                cpas.append(r.winning_price)
        
        avg_cpa = total_spend / len(conversions) if conversions else 0.0
        median_cpa = np.median(cpas) if cpas else 0.0
        cpa_std = np.std(cpas) if len(cpas) > 1 else 0.0
        
        # Win rate
        win_rate = len(wins) / len(results) if results else 0.0
        
        # ROAS
        roas = total_revenue / total_spend if total_spend > 0 else 0.0
        
        # Average metrics
        avg_bid = np.mean([r.winner_bid for r in wins]) if wins else 0.0
        avg_winning_price = total_spend / len(wins) if wins else 0.0
        
        # Budget efficiency (revenue per dollar spent)
        budget_efficiency = total_revenue / total_spend if total_spend > 0 else 0.0
        
        # Time-based analysis
        win_rate_by_hour = {}
        if bid_requests:
            for hour in range(24):
                hour_results = [r for i, r in enumerate(results) 
                               if bid_requests[i].timestamp.hour == hour]
                hour_wins = sum(1 for r in hour_results if r.did_win)
                win_rate_by_hour[hour] = hour_wins / len(hour_results) if hour_results else 0.0
        
        # Device-based spend analysis
        spend_by_device = {}
        if bid_requests:
            for i, result in enumerate(results):
                if result.did_win:
                    device = bid_requests[i].device.device_type.value
                    spend_by_device[device] = spend_by_device.get(device, 0) + result.winning_price
        
        return PerformanceMetrics(
            strategy_name=strategy_name,
            total_auctions=len(results),
            wins=len(wins),
            win_rate=win_rate,
            total_spend=total_spend,
            total_revenue=total_revenue,
            conversions=len(conversions),
            avg_cpa=avg_cpa,
            median_cpa=median_cpa,
            roas=roas,
            avg_bid=avg_bid,
            avg_winning_price=avg_winning_price,
            budget_efficiency=budget_efficiency,
            cpa_std=cpa_std,
            win_rate_by_hour=win_rate_by_hour,
            spend_by_device=spend_by_device
        )
    
    def compare_strategies(self,
                          strategies_results: Dict[str, List]) -> pd.DataFrame:
        """
        Compare multiple strategies side-by-side
        
        Args:
            strategies_results: Dict mapping strategy names to their results
            
        Returns:
            DataFrame with comparative metrics
        """
        comparison_data = []
        
        for strategy_name, results in strategies_results.items():
            metrics = self.analyze_strategy(strategy_name, results)
            comparison_data.append({
                'Strategy': strategy_name,
                'Win Rate': f"{metrics.win_rate:.1%}",
                'Conversions': metrics.conversions,
                'Avg CPA': f"${metrics.avg_cpa:.2f}",
                'ROAS': f"{metrics.roas:.2f}x",
                'Total Spend': f"${metrics.total_spend:,.2f}",
                'Total Revenue': f"${metrics.total_revenue:,.2f}",
                'Budget Efficiency': f"{metrics.budget_efficiency:.2f}"
            })
        
        return pd.DataFrame(comparison_data)
    
    def statistical_significance(self,
                                 strategy_a_results: List,
                                 strategy_b_results: List,
                                 metric: str = 'win_rate') -> Dict:
        """
        Test if difference between strategies is statistically significant
        
        Args:
            strategy_a_results: Results from strategy A
            strategy_b_results: Results from strategy B
            metric: Metric to test ('win_rate', 'cpa', 'roas')
            
        Returns:
            Dict with test results
        """
        if metric == 'win_rate':
            # Chi-square test for win rates
            a_wins = sum(1 for r in strategy_a_results if r.did_win)
            b_wins = sum(1 for r in strategy_b_results if r.did_win)
            
            contingency_table = [
                [a_wins, len(strategy_a_results) - a_wins],
                [b_wins, len(strategy_b_results) - b_wins]
            ]
            
            chi2, p_value, dof, expected = stats.chi2_contingency(contingency_table)
            
            return {
                'metric': 'win_rate',
                'statistic': chi2,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'strategy_a_value': a_wins / len(strategy_a_results),
                'strategy_b_value': b_wins / len(strategy_b_results)
            }
        
        elif metric == 'cpa':
            # T-test for CPA
            a_cpas = [r.winning_price for r in strategy_a_results if r.converted and r.did_win]
            b_cpas = [r.winning_price for r in strategy_b_results if r.converted and r.did_win]
            
            if len(a_cpas) < 2 or len(b_cpas) < 2:
                return {
                    'metric': 'cpa',
                    'error': 'Insufficient conversions for statistical test'
                }
            
            t_stat, p_value = stats.ttest_ind(a_cpas, b_cpas)
            
            return {
                'metric': 'cpa',
                'statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'strategy_a_value': np.mean(a_cpas),
                'strategy_b_value': np.mean(b_cpas)
            }
        
        elif metric == 'roas':
            # Compare ROAS
            a_spend = sum(r.winning_price for r in strategy_a_results if r.did_win)
            a_revenue = sum(r.revenue for r in strategy_a_results)
            
            b_spend = sum(r.winning_price for r in strategy_b_results if r.did_win)
            b_revenue = sum(r.revenue for r in strategy_b_results)
            
            a_roas = a_revenue / a_spend if a_spend > 0 else 0
            b_roas = b_revenue / b_spend if b_spend > 0 else 0
            
            # Bootstrap confidence intervals for ROAS
            n_bootstrap = 1000
            a_roas_samples = []
            b_roas_samples = []
            
            for _ in range(n_bootstrap):
                a_sample = np.random.choice(len(strategy_a_results), 
                                           size=len(strategy_a_results), 
                                           replace=True)
                a_sample_spend = sum(strategy_a_results[i].winning_price 
                                    for i in a_sample if strategy_a_results[i].did_win)
                a_sample_revenue = sum(strategy_a_results[i].revenue for i in a_sample)
                a_roas_samples.append(a_sample_revenue / a_sample_spend if a_sample_spend > 0 else 0)
                
                b_sample = np.random.choice(len(strategy_b_results), 
                                           size=len(strategy_b_results), 
                                           replace=True)
                b_sample_spend = sum(strategy_b_results[i].winning_price 
                                    for i in b_sample if strategy_b_results[i].did_win)
                b_sample_revenue = sum(strategy_b_results[i].revenue for i in b_sample)
                b_roas_samples.append(b_sample_revenue / b_sample_spend if b_sample_spend > 0 else 0)
            
            # Check if confidence intervals overlap
            a_ci = np.percentile(a_roas_samples, [2.5, 97.5])
            b_ci = np.percentile(b_roas_samples, [2.5, 97.5])
            
            significant = not (a_ci[1] < b_ci[0] or b_ci[1] < a_ci[0])
            
            return {
                'metric': 'roas',
                'strategy_a_value': a_roas,
                'strategy_b_value': b_roas,
                'strategy_a_ci': a_ci,
                'strategy_b_ci': b_ci,
                'significant': significant
            }
    
    def generate_insights(self, metrics: PerformanceMetrics) -> List[str]:
        """
        Generate actionable insights from metrics
        
        Args:
            metrics: PerformanceMetrics object
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Win rate insights
        if metrics.win_rate < 0.3:
            insights.append(f"⚠️ Low win rate ({metrics.win_rate:.1%}). Consider increasing bids.")
        elif metrics.win_rate > 0.7:
            insights.append(f"💰 High win rate ({metrics.win_rate:.1%}). You may be overbidding - consider reducing bids to improve efficiency.")
        
        # CPA insights
        if metrics.avg_cpa > 0:
            if metrics.cpa_std / metrics.avg_cpa > 0.5:
                insights.append(f"📊 High CPA variance (std: ${metrics.cpa_std:.2f}). Your bidding could be more consistent.")
        
        # ROAS insights
        if metrics.roas < 2.0:
            insights.append(f"📉 Low ROAS ({metrics.roas:.2f}x). Focus on higher-quality inventory or reduce bids.")
        elif metrics.roas > 5.0:
            insights.append(f"🚀 Excellent ROAS ({metrics.roas:.2f}x)! Consider scaling this strategy.")
        
        # Budget efficiency
        if metrics.budget_efficiency < 1.5:
            insights.append(f"⚡ Low budget efficiency ({metrics.budget_efficiency:.2f}). Review targeting and bid strategy.")
        
        # Conversion rate
        conversion_rate = metrics.conversions / metrics.wins if metrics.wins > 0 else 0
        if conversion_rate < 0.01:
            insights.append(f"🎯 Low conversion rate ({conversion_rate:.2%}). Improve targeting or creative quality.")
        
        return insights
