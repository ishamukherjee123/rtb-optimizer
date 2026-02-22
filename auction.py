"""
Auction Simulator - Core RTB Auction Logic
Simulates programmatic ad auctions with realistic market dynamics
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import random

from .bid_request import BidRequest, DeviceType, AdFormat


class AuctionType(Enum):
    FIRST_PRICE = "first_price"
    SECOND_PRICE = "second_price"
    VCG = "vcg"  # Vickrey-Clarke-Groves


@dataclass
class AuctionResult:
    """Result of a single auction"""
    request_id: str
    winner_bid: Optional[float]
    winning_price: float
    second_price: Optional[float]
    did_win: bool
    num_competitors: int
    floor_price: float
    converted: bool = False
    revenue: float = 0.0
    
    
class MarketDynamics:
    """Simulates realistic market competition and pricing"""
    
    def __init__(self, 
                 avg_competitors: int = 5,
                 volatility: float = 0.3,
                 floor_price_mean: float = 0.5,
                 floor_price_std: float = 0.2):
        """
        Args:
            avg_competitors: Average number of competing bidders
            volatility: Market price volatility (0-1)
            floor_price_mean: Average floor price
            floor_price_std: Floor price standard deviation
        """
        self.avg_competitors = avg_competitors
        self.volatility = volatility
        self.floor_price_mean = floor_price_mean
        self.floor_price_std = floor_price_std
        
    def generate_competition(self, bid_request: BidRequest) -> int:
        """Generate number of competing bidders"""
        # More competition for valuable inventory
        base = self.avg_competitors
        
        # Adjust based on quality signals
        if bid_request.impression.position == "above_fold":
            base *= 1.3
        if bid_request.impression.viewability_score > 0.8:
            base *= 1.2
        if bid_request.user.behavior_score > 0.7:
            base *= 1.4
            
        # Add randomness
        competitors = int(np.random.poisson(base))
        return max(1, competitors)
    
    def generate_competitor_bids(self, 
                                  num_competitors: int,
                                  floor_price: float,
                                  bid_request: BidRequest) -> List[float]:
        """Generate realistic competitor bid distribution"""
        if num_competitors == 0:
            return []
        
        # Base price depends on inventory quality
        quality_multiplier = (
            bid_request.impression.viewability_score * 0.5 +
            bid_request.user.behavior_score * 0.3 +
            (1.0 if bid_request.impression.position == "above_fold" else 0.7) * 0.2
        )
        
        base_price = floor_price + (2.0 * quality_multiplier)
        
        # Generate bids using log-normal distribution
        # This creates realistic bid clustering with long tail
        bids = []
        for _ in range(num_competitors):
            # Log-normal parameters
            mu = np.log(base_price)
            sigma = self.volatility
            
            bid = np.random.lognormal(mu, sigma)
            bid = max(floor_price, bid)  # Ensure above floor
            bids.append(bid)
            
        return sorted(bids, reverse=True)
    
    def generate_floor_price(self) -> float:
        """Generate floor price for auction"""
        price = np.random.normal(self.floor_price_mean, self.floor_price_std)
        return max(0.1, price)  # Minimum floor of $0.10


class AuctionSimulator:
    """Main auction simulation engine"""
    
    def __init__(self,
                 auction_type: AuctionType = AuctionType.SECOND_PRICE,
                 market_dynamics: Optional[MarketDynamics] = None):
        """
        Args:
            auction_type: Type of auction mechanism
            market_dynamics: Market dynamics simulator
        """
        self.auction_type = auction_type
        self.market = market_dynamics or MarketDynamics()
        
    def run_auction(self, 
                    bid_request: BidRequest,
                    our_bid: float) -> AuctionResult:
        """
        Run a single auction
        
        Args:
            bid_request: The bid request object
            our_bid: Our bid amount
            
        Returns:
            AuctionResult with outcome details
        """
        # Generate floor price if not set
        if bid_request.floor_price <= 0:
            bid_request.floor_price = self.market.generate_floor_price()
        
        # Check if our bid meets floor
        if our_bid < bid_request.floor_price:
            return AuctionResult(
                request_id=bid_request.request_id,
                winner_bid=None,
                winning_price=0.0,
                second_price=None,
                did_win=False,
                num_competitors=0,
                floor_price=bid_request.floor_price
            )
        
        # Generate competition
        num_competitors = self.market.generate_competition(bid_request)
        competitor_bids = self.market.generate_competitor_bids(
            num_competitors, 
            bid_request.floor_price,
            bid_request
        )
        
        # Combine all bids
        all_bids = [our_bid] + competitor_bids
        all_bids.sort(reverse=True)
        
        # Determine winner and price based on auction type
        did_win = all_bids[0] == our_bid
        
        if self.auction_type == AuctionType.FIRST_PRICE:
            winning_price = our_bid if did_win else all_bids[0]
            
        elif self.auction_type == AuctionType.SECOND_PRICE:
            # Winner pays second-highest bid
            second_price = all_bids[1] if len(all_bids) > 1 else bid_request.floor_price
            winning_price = second_price if did_win else all_bids[0]
            
        else:  # VCG
            winning_price = our_bid if did_win else all_bids[0]
        
        # Simulate conversion
        converted = False
        revenue = 0.0
        if did_win:
            # Conversion happens based on probability
            converted = random.random() < bid_request.conversion_probability
            if converted:
                revenue = bid_request.estimated_value
        
        return AuctionResult(
            request_id=bid_request.request_id,
            winner_bid=our_bid if did_win else all_bids[0],
            winning_price=winning_price,
            second_price=all_bids[1] if len(all_bids) > 1 else None,
            did_win=did_win,
            num_competitors=num_competitors,
            floor_price=bid_request.floor_price,
            converted=converted,
            revenue=revenue
        )
    
    def simulate_batch(self,
                       bid_requests: List[BidRequest],
                       bid_strategy) -> List[AuctionResult]:
        """
        Simulate multiple auctions using a bid strategy
        
        Args:
            bid_requests: List of bid requests
            bid_strategy: Strategy object with get_bid() method
            
        Returns:
            List of auction results
        """
        results = []
        
        for bid_request in bid_requests:
            # Get bid from strategy
            bid = bid_strategy.get_bid(bid_request)
            
            # Run auction
            result = self.run_auction(bid_request, bid)
            results.append(result)
            
            # Update strategy with result (for learning strategies)
            if hasattr(bid_strategy, 'update'):
                bid_strategy.update(bid_request, result)
        
        return results
    
    
def generate_sample_requests(num_requests: int = 1000,
                             seed: Optional[int] = None) -> List[BidRequest]:
    """Generate sample bid requests for testing"""
    if seed:
        np.random.seed(seed)
        random.seed(seed)
    
    requests = []
    
    device_types = list(DeviceType)
    ad_formats = list(AdFormat)
    positions = ["above_fold", "below_fold"]
    
    for _ in range(num_requests):
        # Randomize request parameters
        device_type = random.choice(device_types)
        ad_format = random.choice(ad_formats)
        position = random.choice(positions)
        
        # Quality scores affect conversion
        viewability = np.random.beta(8, 2)  # Skewed toward high viewability
        behavior_score = np.random.beta(3, 5)  # Skewed toward lower scores
        
        # Conversion probability based on quality
        base_cvr = 0.01
        quality_boost = (viewability * 0.3 + behavior_score * 0.7) * 0.05
        conversion_prob = base_cvr + quality_boost
        
        # Estimated value varies
        estimated_value = np.random.gamma(3, 5)  # Right-skewed distribution
        
        from .bid_request import User, Device, Impression
        
        request = BidRequest(
            user=User(
                user_id=str(uuid.uuid4()),
                behavior_score=behavior_score,
                segments=[f"seg_{i}" for i in range(random.randint(1, 5))]
            ),
            device=Device(
                device_type=device_type,
                os=random.choice(["Windows", "MacOS", "iOS", "Android"]),
                browser=random.choice(["Chrome", "Safari", "Firefox", "Edge"]),
                ip=f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                geo_city=random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                geo_country="US"
            ),
            impression=Impression(
                impression_id=str(uuid.uuid4()),
                ad_format=ad_format,
                width=random.choice([300, 728, 970, 320]),
                height=random.choice([250, 90, 250, 50]),
                position=position,
                viewability_score=viewability
            ),
            conversion_probability=conversion_prob,
            estimated_value=estimated_value
        )
        
        requests.append(request)
    
    return requests


import uuid
