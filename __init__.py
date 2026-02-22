"""
RTB Optimizer - Real-Time Bidding Intelligence Platform
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .auction import AuctionSimulator, MarketDynamics, AuctionType
from .bid_request import BidRequest, DeviceType, AdFormat

__all__ = [
    'AuctionSimulator',
    'MarketDynamics',
    'AuctionType',
    'BidRequest',
    'DeviceType',
    'AdFormat',
]
