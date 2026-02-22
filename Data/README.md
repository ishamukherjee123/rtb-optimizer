# RTB Optimizer Data Schemas

## Bid Request Schema

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-02-22T10:30:00Z",
  "user": {
    "user_id": "user_123456",
    "segments": ["tech_enthusiast", "high_income", "mobile_first"],
    "behavior_score": 0.75,
    "demographics": {
      "age_range": "25-34",
      "gender": "F"
    }
  },
  "device": {
    "type": "mobile",
    "os": "iOS",
    "browser": "Safari",
    "ip": "192.168.1.1",
    "geo_city": "San Francisco",
    "geo_country": "US"
  },
  "impression": {
    "impression_id": "imp_789012",
    "format": "display",
    "width": 300,
    "height": 250,
    "position": "above_fold",
    "viewability_score": 0.85
  },
  "floor_price": 0.75,
  "competition_level": 5,
  "conversion_probability": 0.025,
  "estimated_value": 12.50
}
```

## Auction Result Schema

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "winner_bid": 3.50,
  "winning_price": 3.25,
  "second_price": 3.25,
  "did_win": true,
  "num_competitors": 5,
  "floor_price": 0.75,
  "converted": false,
  "revenue": 0.00,
  "timestamp": "2024-02-22T10:30:00.123Z"
}
```

## Performance Metrics Schema

```json
{
  "strategy_name": "Dynamic Bid",
  "total_auctions": 10000,
  "wins": 4870,
  "win_rate": 0.487,
  "total_spend": 45120.50,
  "total_revenue": 185093.20,
  "conversions": 234,
  "avg_cpa": 15.20,
  "median_cpa": 14.85,
  "roas": 4.1,
  "avg_bid": 3.25,
  "avg_winning_price": 9.26,
  "budget_efficiency": 4.1,
  "cpa_std": 3.45,
  "win_rate_by_hour": {
    "0": 0.42,
    "1": 0.39,
    "8": 0.51,
    "12": 0.54,
    "18": 0.48,
    "23": 0.43
  },
  "spend_by_device": {
    "desktop": 18500.20,
    "mobile": 22300.15,
    "tablet": 3100.10,
    "ctv": 1220.05
  }
}
```

## Budget Allocation Schema

```json
{
  "campaign_id": "camp_001",
  "allocated_budget": 5000.00,
  "expected_conversions": 333,
  "expected_revenue": 20500.00,
  "expected_roas": 4.1,
  "allocation_timestamp": "2024-02-22T10:00:00Z"
}
```

## Campaign Configuration Schema

```json
{
  "campaign_id": "camp_001",
  "name": "Q1 Awareness Campaign",
  "current_cpa": 15.00,
  "conversion_rate": 0.022,
  "avg_order_value": 61.50,
  "daily_impression_volume": 50000,
  "min_budget": 100.00,
  "max_budget": 10000.00,
  "target_roas": 4.0,
  "status": "active",
  "start_date": "2024-01-01",
  "end_date": "2024-03-31"
}
```

## Strategy Configuration Schema

```json
{
  "strategy_type": "dynamic",
  "parameters": {
    "base_bid": 1.50,
    "max_bid": 12.00,
    "target_cpa": 15.00,
    "aggressiveness": 1.2,
    "learning_rate": 0.1
  },
  "constraints": {
    "max_daily_budget": 5000.00,
    "target_win_rate": 0.45
  },
  "enabled": true
}
```

## Field Descriptions

### Device Types
- `desktop`: Traditional desktop/laptop computers
- `mobile`: Smartphones
- `tablet`: Tablet devices
- `ctv`: Connected TV / Over-the-top devices

### Ad Formats
- `display`: Banner and display ads
- `video`: Video advertisements
- `native`: Native content ads
- `audio`: Audio/podcast ads

### Position Types
- `above_fold`: Visible without scrolling
- `below_fold`: Requires scrolling to view

### Auction Types
- `first_price`: Winner pays their bid
- `second_price`: Winner pays second-highest bid
- `vcg`: Vickrey-Clarke-Groves mechanism

## Data Types

| Field | Type | Range/Format | Required |
|-------|------|--------------|----------|
| request_id | UUID | RFC 4122 | Yes |
| timestamp | DateTime | ISO 8601 | Yes |
| behavior_score | Float | 0.0 - 1.0 | Yes |
| viewability_score | Float | 0.0 - 1.0 | Yes |
| conversion_probability | Float | 0.0 - 1.0 | Yes |
| floor_price | Float | > 0.0 | Yes |
| estimated_value | Float | > 0.0 | Yes |
| competition_level | Integer | >= 0 | Yes |

## CSV Export Format

Results can be exported to CSV with the following columns:

```csv
request_id,timestamp,strategy,bid,won,price,converted,revenue,competitors,device,position
550e8400-e29b-41d4-a716-446655440000,2024-02-22T10:30:00Z,dynamic,3.50,true,3.25,false,0.00,5,mobile,above_fold
```

## Database Schema (Future)

For production deployment with PostgreSQL:

```sql
CREATE TABLE bid_requests (
    request_id UUID PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    user_id VARCHAR(100),
    device_type VARCHAR(20),
    ad_format VARCHAR(20),
    floor_price DECIMAL(10, 2),
    conversion_prob DECIMAL(5, 4),
    estimated_value DECIMAL(10, 2)
);

CREATE TABLE auction_results (
    result_id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES bid_requests(request_id),
    strategy_name VARCHAR(50),
    bid DECIMAL(10, 2),
    won BOOLEAN,
    winning_price DECIMAL(10, 2),
    converted BOOLEAN,
    revenue DECIMAL(10, 2),
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_results_strategy ON auction_results(strategy_name);
CREATE INDEX idx_results_timestamp ON auction_results(timestamp);
CREATE INDEX idx_requests_timestamp ON bid_requests(timestamp);
```
