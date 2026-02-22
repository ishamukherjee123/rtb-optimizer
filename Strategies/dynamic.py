"""
Dynamic Bid Strategy
Adjusts bids based on predicted value and competition
"""

import numpy as np
from .base import BidStrategy
from simulation.bid_request import BidRequest


class DynamicBidStrategy(BidStrategy):
    """
    Dynamically adjust bids based on:
    - Conversion probability
    - Estimated value
    - Quality signals (viewability, position, user behavior)
    - Target CPA
    """
    
    def __init__(self, 
                 base_bid: float = 2.0,
                 max_bid: float = 15.0,
                 target_cpa: float = 20.0,
                 aggressiveness: float = 1.0):
        """
        Args:
            base_bid: Minimum bid amount
            max_bid: Maximum bid cap
            target_cpa: Target cost per acquisition
            aggressiveness: Multiplier for bid adjustments (0.5-2.0)
        """
        super().__init__(
            name="Dynamic Bid",
            base_bid=base_bid,
            max_bid=max_bid,
            target_cpa=target_cpa,
            aggressiveness=aggressiveness
        )
        self.base_bid = base_bid
        self.max_bid = max_bid
        self.target_cpa = target_cpa
        self.aggressiveness = aggressiveness
        
        # Running statistics for adaptive adjustment
        self.running_win_rate = 0.5
        self.running_cpa = target_cpa
        self.smoothing_factor = 0.1
        
    def get_bid(self, bid_request: BidRequest) -> float:
        """
        Calculate optimal bid based on expected value
        
        Bid = (Conversion Probability × Expected Value × Quality Score) / Target CPA
        """
        # Calculate quality score
        quality_score = self._calculate_quality_score(bid_request)
        
        # Expected value of this impression
        expected_value = (
            bid_request.conversion_probability * 
            bid_request.estimated_value * 
            quality_score
        )
        
        # Bid as a function of expected value and target CPA
        # If expected value is high, we can bid more
        base_optimal_bid = expected_value * self.aggressiveness
        
        # Adjust based on running performance
        if len(self.results_history) > 50:
            # If win rate is too low, increase bids
            if self.running_win_rate < 0.3:
                base_optimal_bid *= 1.2
            # If win rate is too high and CPA is low, we can bid higher
            elif self.running_win_rate > 0.7 and self.running_cpa < self.target_cpa * 0.8:
                base_optimal_bid *= 1.3
            # If CPA is too high, reduce bids
            elif self.running_cpa > self.target_cpa * 1.2:
                base_optimal_bid *= 0.8
        
        # Apply floor and ceiling
        bid = np.clip(base_optimal_bid, self.base_bid, self.max_bid)
        
        return round(bid, 2)
    
    def _calculate_quality_score(self, bid_request: BidRequest) -> float:
        """
        Calculate quality score from 0-2 based on multiple signals
        1.0 is neutral, >1.0 is premium, <1.0 is discount
        """
        score = 1.0
        
        # Viewability boost
        score += (bid_request.impression.viewability_score - 0.5) * 0.4
        
        # Position boost
        if bid_request.impression.position == "above_fold":
            score += 0.3
        
        # User behavior boost
        score += (bid_request.user.behavior_score - 0.5) * 0.6
        
        # Device type adjustment
        device_multipliers = {
            'desktop': 1.1,
            'mobile': 1.0,
            'tablet': 0.95,
            'ctv': 1.2
        }
        score *= device_multipliers.get(bid_request.device.device_type.value, 1.0)
        
        # Ensure score is reasonable
        return np.clip(score, 0.3, 2.0)
    
    def update(self, bid_request: BidRequest, result):
        """Update running statistics for adaptive bidding"""
        super().update(bid_request, result)
        
        # Update running win rate
        self.running_win_rate = (
            (1 - self.smoothing_factor) * self.running_win_rate +
            self.smoothing_factor * (1.0 if result.did_win else 0.0)
        )
        
        # Update running CPA if we have conversions
        if result.converted and result.did_win:
            current_cpa = result.winning_price
            self.running_cpa = (
                (1 - self.smoothing_factor) * self.running_cpa +
                self.smoothing_factor * current_cpa
            )
