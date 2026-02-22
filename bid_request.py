"""
Bid Request Data Model
Represents incoming bid requests in programmatic advertising
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum


class DeviceType(Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"
    CTV = "ctv"


class AdFormat(Enum):
    DISPLAY = "display"
    VIDEO = "video"
    NATIVE = "native"
    AUDIO = "audio"


@dataclass
class User:
    """User information from bid request"""
    user_id: str
    segments: List[str] = field(default_factory=list)
    demographics: Dict[str, str] = field(default_factory=dict)
    behavior_score: float = 0.5  # 0-1 likelihood to convert


@dataclass
class Device:
    """Device information"""
    device_type: DeviceType
    os: str
    browser: str
    ip: str
    geo_city: str
    geo_country: str


@dataclass
class Impression:
    """Ad impression opportunity"""
    impression_id: str
    ad_format: AdFormat
    width: int
    height: int
    position: str  # above_fold, below_fold
    viewability_score: float  # 0-1 predicted viewability
    

@dataclass
class BidRequest:
    """Complete bid request object"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    user: User = field(default_factory=lambda: User(user_id=str(uuid.uuid4())))
    device: Device = field(default_factory=lambda: Device(
        device_type=DeviceType.DESKTOP,
        os="unknown",
        browser="unknown",
        ip="0.0.0.0",
        geo_city="unknown",
        geo_country="US"
    ))
    impression: Impression = field(default_factory=lambda: Impression(
        impression_id=str(uuid.uuid4()),
        ad_format=AdFormat.DISPLAY,
        width=300,
        height=250,
        position="above_fold",
        viewability_score=0.7
    ))
    
    # Auction metadata
    floor_price: float = 0.5  # Minimum bid
    competition_level: int = 3  # Number of competing bidders
    
    # Predicted values (in real system, from ML model)
    conversion_probability: float = 0.02  # 2% default
    estimated_value: float = 10.0  # Expected revenue if conversion happens
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'request_id': self.request_id,
            'timestamp': self.timestamp.isoformat(),
            'user': {
                'user_id': self.user.user_id,
                'segments': self.user.segments,
                'behavior_score': self.user.behavior_score
            },
            'device': {
                'type': self.device.device_type.value,
                'os': self.device.os,
                'browser': self.device.browser,
                'geo_city': self.device.geo_city,
                'geo_country': self.device.geo_country
            },
            'impression': {
                'format': self.impression.ad_format.value,
                'width': self.impression.width,
                'height': self.impression.height,
                'position': self.impression.position,
                'viewability_score': self.impression.viewability_score
            },
            'floor_price': self.floor_price,
            'competition_level': self.competition_level,
            'conversion_probability': self.conversion_probability,
            'estimated_value': self.estimated_value
        }
