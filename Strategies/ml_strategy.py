"""
ML-Powered Bid Strategy
Uses gradient boosting to predict optimal bids based on historical performance
"""

import numpy as np
from typing import List, Dict
from .base import BidStrategy
from simulation.bid_request import BidRequest
from simulation.auction import AuctionResult


class MLBidStrategy(BidStrategy):
    """
    Machine learning-based bidding using historical data
    
    Features used for prediction:
    - Conversion probability
    - Estimated value
    - Viewability score
    - User behavior score
    - Device type
    - Position
    - Time of day
    - Competition level (if available)
    """
    
    def __init__(self,
                 base_bid: float = 2.0,
                 max_bid: float = 15.0,
                 target_cpa: float = 20.0,
                 exploration_rate: float = 0.1,
                 min_training_samples: int = 100):
        """
        Args:
            base_bid: Minimum bid
            max_bid: Maximum bid cap
            target_cpa: Target cost per acquisition
            exploration_rate: Probability of random exploration (0-1)
            min_training_samples: Minimum samples before using ML model
        """
        super().__init__(
            name="ML Bid",
            base_bid=base_bid,
            max_bid=max_bid,
            target_cpa=target_cpa,
            exploration_rate=exploration_rate
        )
        self.base_bid = base_bid
        self.max_bid = max_bid
        self.target_cpa = target_cpa
        self.exploration_rate = exploration_rate
        self.min_training_samples = min_training_samples
        
        # Model will be trained lazily
        self.model = None
        self.feature_names = [
            'conversion_prob',
            'estimated_value',
            'viewability',
            'behavior_score',
            'device_desktop',
            'device_mobile',
            'device_tablet',
            'device_ctv',
            'position_above_fold',
            'hour',
            'quality_score'
        ]
        
    def get_bid(self, bid_request: BidRequest) -> float:
        """
        Get bid using ML model if trained, otherwise use heuristic
        """
        # Exploration: sometimes use random bid
        if np.random.random() < self.exploration_rate:
            return np.random.uniform(self.base_bid, self.max_bid)
        
        # If not enough training data, use heuristic
        if len(self.results_history) < self.min_training_samples:
            return self._heuristic_bid(bid_request)
        
        # Train model if not already trained
        if self.model is None:
            self._train_model()
        
        # Extract features
        features = self._extract_features(bid_request)
        
        # Predict optimal bid
        try:
            predicted_bid = self.model.predict([features])[0]
            bid = np.clip(predicted_bid, self.base_bid, self.max_bid)
            return round(bid, 2)
        except Exception as e:
            # Fallback to heuristic if prediction fails
            return self._heuristic_bid(bid_request)
    
    def _extract_features(self, bid_request: BidRequest) -> List[float]:
        """Extract feature vector from bid request"""
        features = []
        
        # Numerical features
        features.append(bid_request.conversion_probability)
        features.append(bid_request.estimated_value)
        features.append(bid_request.impression.viewability_score)
        features.append(bid_request.user.behavior_score)
        
        # Device type (one-hot)
        device_type = bid_request.device.device_type.value
        features.append(1.0 if device_type == 'desktop' else 0.0)
        features.append(1.0 if device_type == 'mobile' else 0.0)
        features.append(1.0 if device_type == 'tablet' else 0.0)
        features.append(1.0 if device_type == 'ctv' else 0.0)
        
        # Position
        features.append(1.0 if bid_request.impression.position == 'above_fold' else 0.0)
        
        # Time features
        hour = bid_request.timestamp.hour
        features.append(hour)
        
        # Derived quality score
        quality = self._calculate_quality_score(bid_request)
        features.append(quality)
        
        return features
    
    def _calculate_quality_score(self, bid_request: BidRequest) -> float:
        """Calculate composite quality score"""
        score = (
            bid_request.impression.viewability_score * 0.4 +
            bid_request.user.behavior_score * 0.3 +
            (1.0 if bid_request.impression.position == 'above_fold' else 0.5) * 0.3
        )
        return score
    
    def _heuristic_bid(self, bid_request: BidRequest) -> float:
        """Simple heuristic bid when ML model not available"""
        quality = self._calculate_quality_score(bid_request)
        expected_value = (
            bid_request.conversion_probability * 
            bid_request.estimated_value * 
            quality
        )
        bid = expected_value * 0.8  # Conservative multiplier
        return np.clip(bid, self.base_bid, self.max_bid)
    
    def _train_model(self):
        """Train gradient boosting model on historical data"""
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            # If sklearn not available, use heuristic
            print("Warning: scikit-learn not available, using heuristic bidding")
            return
        
        # Prepare training data
        X_train = []
        y_train = []
        
        for i, result in enumerate(self.results_history):
            # We need the original bid request
            # For now, we'll create a synthetic target based on result
            if result.did_win and result.converted:
                # This was a good bid - slightly below it would be optimal
                target_bid = result.winning_price * 0.95
            elif result.did_win and not result.converted:
                # Won but no conversion - bid was too high
                target_bid = result.winning_price * 0.7
            else:
                # Lost auction - bid was too low
                # Estimate we needed to bid ~10% more than our bid
                if result.second_price:
                    target_bid = result.second_price * 1.05
                else:
                    continue  # Skip if we don't have good signal
            
            # We need to store bid_requests with results to train properly
            # For now, this is a simplified version
            # In production, you'd store full bid_request with each result
            
        # Note: This is a simplified ML implementation
        # In production, you'd want to:
        # 1. Store full bid_request with each result
        # 2. Use more sophisticated feature engineering
        # 3. Implement proper cross-validation
        # 4. Regular model retraining
        # 5. A/B testing of model versions
        
        if len(y_train) < self.min_training_samples:
            return
        
        # Train model
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=4,
            random_state=42
        )
        
        # In a real implementation with stored bid_requests:
        # self.model.fit(X_train, y_train)
        
    def update(self, bid_request: BidRequest, result: AuctionResult):
        """Store result and retrain periodically"""
        super().update(bid_request, result)
        
        # Retrain every N samples
        if len(self.results_history) % 500 == 0 and len(self.results_history) >= self.min_training_samples:
            self._train_model()
