"""
Fixed Bid Strategy
Simple baseline strategy that bids a constant amount
"""

from .base import BidStrategy
from simulation.bid_request import BidRequest


class FixedBidStrategy(BidStrategy):
    """Bid the same amount for all auctions"""
    
    def __init__(self, bid_amount: float = 2.5):
        """
        Args:
            bid_amount: Fixed bid amount for all auctions
        """
        super().__init__(name="Fixed Bid", bid_amount=bid_amount)
        self.bid_amount = bid_amount
    
    def get_bid(self, bid_request: BidRequest) -> float:
        """Always return the fixed bid amount"""
        return self.bid_amount
