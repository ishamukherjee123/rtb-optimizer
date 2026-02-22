"""
Base Bid Strategy Interface
All bidding strategies inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from simulation.bid_request import BidRequest
from simulation.auction import AuctionResult


class BidStrategy(ABC):
    """Abstract base class for all bid strategies"""
    
    def __init__(self, name: str, **kwargs):
        """
        Args:
            name: Strategy identifier
            **kwargs: Strategy-specific parameters
        """
        self.name = name
        self.params = kwargs
        self.bid_history = []
        self.results_history = []
        
    @abstractmethod
    def get_bid(self, bid_request: BidRequest) -> float:
        """
        Calculate bid amount for a given request
        
        Args:
            bid_request: The bid request to evaluate
            
        Returns:
            Bid amount in dollars
        """
        pass
    
    def update(self, bid_request: BidRequest, result: AuctionResult):
        """
        Update strategy based on auction result (for learning strategies)
        
        Args:
            bid_request: The original bid request
            result: Auction outcome
        """
        self.bid_history.append({
            'request_id': bid_request.request_id,
            'bid': result.winner_bid if result.did_win else 0.0,
            'timestamp': bid_request.timestamp
        })
        self.results_history.append(result)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get strategy performance statistics"""
        if not self.results_history:
            return {
                'total_auctions': 0,
                'wins': 0,
                'win_rate': 0.0,
                'total_spend': 0.0,
                'total_revenue': 0.0,
                'conversions': 0,
                'avg_cpa': 0.0,
                'roas': 0.0
            }
        
        wins = sum(1 for r in self.results_history if r.did_win)
        total_spend = sum(r.winning_price for r in self.results_history if r.did_win)
        conversions = sum(1 for r in self.results_history if r.converted)
        total_revenue = sum(r.revenue for r in self.results_history)
        
        avg_cpa = total_spend / conversions if conversions > 0 else 0.0
        roas = total_revenue / total_spend if total_spend > 0 else 0.0
        
        return {
            'strategy_name': self.name,
            'total_auctions': len(self.results_history),
            'wins': wins,
            'win_rate': wins / len(self.results_history),
            'total_spend': total_spend,
            'total_revenue': total_revenue,
            'conversions': conversions,
            'avg_cpa': avg_cpa,
            'roas': roas,
            'avg_bid': sum(r.winner_bid or 0 for r in self.results_history if r.did_win) / wins if wins > 0 else 0.0,
            'avg_price_paid': total_spend / wins if wins > 0 else 0.0
        }
    
    def reset(self):
        """Reset strategy state and history"""
        self.bid_history = []
        self.results_history = []
