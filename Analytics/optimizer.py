"""
Budget Optimization Module
Optimizes budget allocation across campaigns and time periods
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class Campaign:
    """Campaign configuration"""
    campaign_id: str
    name: str
    current_cpa: float
    conversion_rate: float
    avg_order_value: float
    daily_impression_volume: int
    min_budget: float = 0.0
    max_budget: Optional[float] = None
    

@dataclass
class BudgetAllocation:
    """Optimized budget allocation"""
    campaign_id: str
    allocated_budget: float
    expected_conversions: float
    expected_revenue: float
    expected_roas: float


class BudgetOptimizer:
    """
    Optimize budget allocation to maximize ROAS or conversions
    Uses linear programming for optimal allocation
    """
    
    def __init__(self):
        self.optimization_history = []
        
    def optimize_allocation(self,
                           campaigns: List[Campaign],
                           total_budget: float,
                           objective: str = 'maximize_roas') -> List[BudgetAllocation]:
        """
        Optimize budget allocation across campaigns
        
        Args:
            campaigns: List of Campaign objects
            total_budget: Total budget to allocate
            objective: 'maximize_roas' or 'maximize_conversions'
            
        Returns:
            List of BudgetAllocation objects
        """
        try:
            from scipy.optimize import linprog
        except ImportError:
            print("Warning: scipy not available, using heuristic allocation")
            return self._heuristic_allocation(campaigns, total_budget)
        
        # Build linear programming problem
        n_campaigns = len(campaigns)
        
        if objective == 'maximize_roas':
            # Objective: maximize total revenue
            # Revenue per dollar = (conversion_rate * avg_order_value) / cpa
            c = [-((camp.conversion_rate * camp.avg_order_value) / camp.current_cpa) 
                 for camp in campaigns]
        else:  # maximize_conversions
            # Objective: maximize total conversions
            # Conversions per dollar = conversion_rate / cpa
            c = [-(camp.conversion_rate / camp.current_cpa) for camp in campaigns]
        
        # Constraints:
        # 1. Total budget constraint: sum(allocations) <= total_budget
        A_ub = [np.ones(n_campaigns)]
        b_ub = [total_budget]
        
        # 2. Individual campaign max budgets
        for i, camp in enumerate(campaigns):
            if camp.max_budget:
                constraint = np.zeros(n_campaigns)
                constraint[i] = 1
                A_ub.append(constraint)
                b_ub.append(camp.max_budget)
        
        # Bounds: each campaign gets at least min_budget
        bounds = [(camp.min_budget, camp.max_budget or total_budget) 
                  for camp in campaigns]
        
        # Solve
        result = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')
        
        if not result.success:
            print(f"Optimization failed: {result.message}")
            return self._heuristic_allocation(campaigns, total_budget)
        
        # Create allocations
        allocations = []
        for i, camp in enumerate(campaigns):
            allocated = result.x[i]
            expected_conversions = (allocated / camp.current_cpa) * camp.conversion_rate
            expected_revenue = expected_conversions * camp.avg_order_value
            expected_roas = expected_revenue / allocated if allocated > 0 else 0
            
            allocations.append(BudgetAllocation(
                campaign_id=camp.campaign_id,
                allocated_budget=allocated,
                expected_conversions=expected_conversions,
                expected_revenue=expected_revenue,
                expected_roas=expected_roas
            ))
        
        return allocations
    
    def _heuristic_allocation(self,
                             campaigns: List[Campaign],
                             total_budget: float) -> List[BudgetAllocation]:
        """
        Fallback heuristic allocation when optimization library unavailable
        Allocates based on efficiency (ROAS)
        """
        # Calculate efficiency score for each campaign
        efficiencies = []
        for camp in campaigns:
            roas = (camp.conversion_rate * camp.avg_order_value) / camp.current_cpa
            efficiencies.append(roas)
        
        # Normalize to get allocation percentages
        total_efficiency = sum(efficiencies)
        allocations = []
        
        for i, camp in enumerate(campaigns):
            # Allocate proportionally to efficiency
            allocated = (efficiencies[i] / total_efficiency) * total_budget
            
            # Respect min/max constraints
            allocated = max(camp.min_budget, allocated)
            if camp.max_budget:
                allocated = min(camp.max_budget, allocated)
            
            expected_conversions = (allocated / camp.current_cpa) * camp.conversion_rate
            expected_revenue = expected_conversions * camp.avg_order_value
            expected_roas = expected_revenue / allocated if allocated > 0 else 0
            
            allocations.append(BudgetAllocation(
                campaign_id=camp.campaign_id,
                allocated_budget=allocated,
                expected_conversions=expected_conversions,
                expected_revenue=expected_revenue,
                expected_roas=expected_roas
            ))
        
        return allocations
    
    def optimize_daily_pacing(self,
                             total_daily_budget: float,
                             hours_remaining: int,
                             spent_so_far: float,
                             historical_hourly_performance: Optional[Dict[int, float]] = None) -> List[float]:
        """
        Optimize hourly budget pacing for remainder of day
        
        Args:
            total_daily_budget: Total budget for the day
            hours_remaining: Hours left in the day
            spent_so_far: Amount already spent
            historical_hourly_performance: Dict of hour -> performance multiplier
            
        Returns:
            List of recommended hourly budgets
        """
        remaining_budget = total_daily_budget - spent_so_far
        
        if hours_remaining <= 0:
            return []
        
        # If no historical data, distribute evenly
        if not historical_hourly_performance:
            hourly_budget = remaining_budget / hours_remaining
            return [hourly_budget] * hours_remaining
        
        # Weight hours by historical performance
        current_hour = datetime.now().hour
        hourly_weights = []
        
        for i in range(hours_remaining):
            hour = (current_hour + i) % 24
            weight = historical_hourly_performance.get(hour, 1.0)
            hourly_weights.append(weight)
        
        # Normalize weights
        total_weight = sum(hourly_weights)
        hourly_budgets = [(w / total_weight) * remaining_budget for w in hourly_weights]
        
        return hourly_budgets
    
    def calculate_budget_efficiency(self,
                                   allocated_budget: float,
                                   actual_spend: float,
                                   conversions: int,
                                   revenue: float) -> Dict[str, float]:
        """
        Calculate efficiency metrics for budget utilization
        
        Returns:
            Dict with efficiency metrics
        """
        budget_utilization = actual_spend / allocated_budget if allocated_budget > 0 else 0
        cpa = actual_spend / conversions if conversions > 0 else 0
        roas = revenue / actual_spend if actual_spend > 0 else 0
        
        # Efficiency score (0-100)
        # Perfect score: 95-105% budget utilization, low CPA, high ROAS
        utilization_score = 100 * (1 - abs(budget_utilization - 1.0))
        roas_score = min(100, roas * 20)  # 5x ROAS = 100 points
        
        efficiency_score = (utilization_score * 0.4 + roas_score * 0.6)
        
        return {
            'budget_utilization': budget_utilization,
            'cpa': cpa,
            'roas': roas,
            'efficiency_score': efficiency_score,
            'status': self._get_efficiency_status(efficiency_score)
        }
    
    def _get_efficiency_status(self, score: float) -> str:
        """Get human-readable efficiency status"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def scenario_analysis(self,
                         campaigns: List[Campaign],
                         budget_scenarios: List[float]) -> pd.DataFrame:
        """
        Analyze multiple budget scenarios
        
        Args:
            campaigns: List of campaigns
            budget_scenarios: List of total budget amounts to analyze
            
        Returns:
            DataFrame with scenario comparisons
        """
        import pandas as pd
        
        results = []
        
        for budget in budget_scenarios:
            allocations = self.optimize_allocation(campaigns, budget, 'maximize_roas')
            
            total_conversions = sum(a.expected_conversions for a in allocations)
            total_revenue = sum(a.expected_revenue for a in allocations)
            avg_roas = total_revenue / budget if budget > 0 else 0
            
            results.append({
                'Budget': f"${budget:,.0f}",
                'Expected Conversions': int(total_conversions),
                'Expected Revenue': f"${total_revenue:,.0f}",
                'Expected ROAS': f"{avg_roas:.2f}x",
                'Revenue per $1000': f"${(total_revenue / budget * 1000) if budget > 0 else 0:,.2f}"
            })
        
        return pd.DataFrame(results)


import pandas as pd
