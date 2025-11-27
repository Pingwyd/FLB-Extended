# Milestone 6: Produce Assistant - Implementation Guide

## Overview
The Produce Assistant helps farmers make data-driven decisions about farming operations through three main features:
1. **Farm Produce Cost Calculator** - Calculate final cost per produce
2. **Shelf Life Calculator** - Estimate spoilage timeline after transport
3. **AI Assistant** - Recommend what to plant based on conditions

---

## 1. Farm Produce Cost Calculator

### **Purpose:**
Calculate the final cost of each produce considering:
- Season (planting & harvest season)
- Size of harvest (quantity)
- Number of workers
- Profit margins
- Expenses (fertilizer, water, electricity, seeds, transport)

### **What's Needed:**

#### **A. Data Models** (models.py)
```python
class ProduceCalculation(Base):
    __tablename__ = 'produce_calculations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Input parameters
    crop_type = Column(String(100))  # 'tomato', 'maize', 'rice', 'cassava'
    season = Column(String(50))  # 'dry', 'rainy', 'harmattan'
    land_size_hectares = Column(Integer)
    expected_yield_kg = Column(Integer)  # Expected harvest in kg
    
    # Labor costs
    num_workers = Column(Integer)
    labor_cost = Column(Integer)  # Total labor cost in kobo
    
    # Material costs
    seed_cost = Column(Integer)
    fertilizer_cost = Column(Integer)
    pesticide_cost = Column(Integer)
    water_cost = Column(Integer)
    electricity_cost = Column(Integer)
    transport_cost = Column(Integer)
    other_expenses = Column(Integer)
    
    # Financial calculations
    total_cost = Column(Integer)  # Sum of all costs
    profit_margin_percent = Column(Integer)  # Desired profit %
    cost_per_kg = Column(Integer)  # Cost per kg in kobo
    selling_price_per_kg = Column(Integer)  # Suggested selling price
    total_revenue = Column(Integer)  # If sold at suggested price
    total_profit = Column(Integer)  # Revenue - Cost
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
```

#### **B. API Endpoint** (app.py)
```python
POST /produce-assistant/calculate-cost
```

**Request Body:**
```json
{
  "user_id": 1,
  "crop_type": "tomato",
  "season": "rainy",
  "land_size_hectares": 2,
  "expected_yield_kg": 5000,
  "num_workers": 10,
  "labor_cost": 50000000,  // 500,000 NGN in kobo
  "seed_cost": 5000000,
  "fertilizer_cost": 15000000,
  "pesticide_cost": 8000000,
  "water_cost": 3000000,
  "electricity_cost": 2000000,
  "transport_cost": 10000000,
  "other_expenses": 5000000,
  "profit_margin_percent": 30  // 30% profit margin
}
```

**Response:**
```json
{
  "id": 1,
  "crop_type": "tomato",
  "total_cost": 98000000,  // 980,000 NGN
  "cost_per_kg": 19600,  // 196 NGN per kg
  "selling_price_per_kg": 25480,  // 254.80 NGN per kg (with 30% margin)
  "total_revenue": 127400000,  // 1,274,000 NGN
  "total_profit": 29400000,  // 294,000 NGN profit
  "breakdown": {
    "labor": 50000000,
    "materials": 31000000,
    "transport": 10000000,
    "other": 7000000
  }
}
```

#### **C. Business Logic** (app.py or new calculator.py)
```python
def calculate_produce_cost(data):
    # Sum all costs
    total_cost = (
        data['labor_cost'] +
        data['seed_cost'] +
        data['fertilizer_cost'] +
        data['pesticide_cost'] +
        data['water_cost'] +
        data['electricity_cost'] +
        data['transport_cost'] +
        data['other_expenses']
    )
    
    # Calculate per kg cost
    cost_per_kg = total_cost / data['expected_yield_kg']
    
    # Calculate selling price with profit margin
    profit_multiplier = 1 + (data['profit_margin_percent'] / 100)
    selling_price_per_kg = cost_per_kg * profit_multiplier
    
    # Calculate revenue and profit
    total_revenue = selling_price_per_kg * data['expected_yield_kg']
    total_profit = total_revenue - total_cost
    
    return {
        'total_cost': total_cost,
        'cost_per_kg': cost_per_kg,
        'selling_price_per_kg': selling_price_per_kg,
        'total_revenue': total_revenue,
        'total_profit': total_profit
    }
```

---

## 2. Shelf Life Calculator

### **Purpose:**
Estimate how long produce will last after transport, accounting for:
- Heat exposure during transport
- Crop type (different crops have different shelf lives)
- Storage conditions
- Transport duration

### **What's Needed:**

#### **A. Data Model** (models.py)
```python
class ShelfLifeCalculation(Base):
    __tablename__ = 'shelf_life_calculations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Input parameters
    crop_type = Column(String(100))
    harvest_date = Column(DateTime)
    transport_duration_hours = Column(Integer)
    transport_temperature_celsius = Column(Integer)
    storage_temperature_celsius = Column(Integer)
    storage_humidity_percent = Column(Integer, nullable=True)
    
    # Calculated results
    base_shelf_life_days = Column(Integer)  # Normal shelf life
    heat_degradation_factor = Column(Float)  # How much heat reduces it
    estimated_shelf_life_days = Column(Integer)  # Adjusted shelf life
    spoilage_date = Column(DateTime)  # Estimated spoilage date
    recommendation = Column(Text)  # Advice on handling
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
```

#### **B. API Endpoint** (app.py)
```python
POST /produce-assistant/calculate-shelf-life
```

**Request Body:**
```json
{
  "user_id": 1,
  "crop_type": "tomato",
  "harvest_date": "2025-11-15T08:00:00",
  "transport_duration_hours": 6,
  "transport_temperature_celsius": 35,
  "storage_temperature_celsius": 20,
  "storage_humidity_percent": 85
}
```

**Response:**
```json
{
  "id": 1,
  "crop_type": "tomato",
  "base_shelf_life_days": 14,
  "heat_degradation_factor": 0.7,
  "estimated_shelf_life_days": 10,
  "spoilage_date": "2025-11-25T08:00:00",
  "recommendation": "High transport temperature (35°C) reduces shelf life by 30%. Store in cool place. Sell within 10 days.",
  "urgency": "medium"  // low, medium, high, critical
}
```

#### **C. Shelf Life Database** (Data reference)
Create a crop shelf life reference table:

```python
CROP_SHELF_LIFE_DATA = {
    'tomato': {
        'base_days': 14,
        'optimal_temp': 12,  # Celsius
        'heat_sensitivity': 'high'  # Degrades faster in heat
    },
    'pepper': {
        'base_days': 21,
        'optimal_temp': 10,
        'heat_sensitivity': 'medium'
    },
    'onion': {
        'base_days': 60,
        'optimal_temp': 15,
        'heat_sensitivity': 'low'
    },
    'yam': {
        'base_days': 90,
        'optimal_temp': 25,
        'heat_sensitivity': 'low'
    },
    'cassava': {
        'base_days': 7,
        'optimal_temp': 20,
        'heat_sensitivity': 'very_high'
    },
    'leafy_greens': {
        'base_days': 7,
        'optimal_temp': 4,
        'heat_sensitivity': 'very_high'
    }
}
```

#### **D. Calculation Logic**
```python
def calculate_shelf_life(crop_type, transport_temp, transport_hours, storage_temp):
    crop_data = CROP_SHELF_LIFE_DATA[crop_type]
    base_days = crop_data['base_days']
    optimal_temp = crop_data['optimal_temp']
    
    # Calculate heat degradation during transport
    temp_diff = abs(transport_temp - optimal_temp)
    heat_hours = transport_hours
    
    # Degradation formula (simplified)
    if crop_data['heat_sensitivity'] == 'very_high':
        degradation = (temp_diff / 10) * (heat_hours / 24) * 0.5
    elif crop_data['heat_sensitivity'] == 'high':
        degradation = (temp_diff / 10) * (heat_hours / 24) * 0.3
    elif crop_data['heat_sensitivity'] == 'medium':
        degradation = (temp_diff / 10) * (heat_hours / 24) * 0.15
    else:  # low
        degradation = (temp_diff / 10) * (heat_hours / 24) * 0.05
    
    # Apply degradation
    heat_factor = max(0.3, 1 - degradation)  # Minimum 30% shelf life
    estimated_days = int(base_days * heat_factor)
    
    return {
        'base_shelf_life_days': base_days,
        'heat_degradation_factor': heat_factor,
        'estimated_shelf_life_days': estimated_days
    }
```

---

## 3. AI Assistant (Planting Recommendations)

### **Purpose:**
Help farmers decide what to plant based on:
- Location (state/region)
- Season
- Land size
- Available labor force
- Available funding
- Farming experience level

### **What's Needed:**

#### **A. Data Model** (models.py)
```python
class PlantingRecommendation(Base):
    __tablename__ = 'planting_recommendations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Input parameters
    location_state = Column(String(100))
    location_area = Column(String(200))
    current_season = Column(String(50))
    land_size_hectares = Column(Integer)
    available_workers = Column(Integer)
    budget_kobo = Column(Integer)
    experience_level = Column(String(50))  # beginner, intermediate, expert
    farming_type = Column(String(100))  # crop, livestock, mixed
    
    # Recommendations
    recommended_crops = Column(Text)  # JSON array
    reasoning = Column(Text)
    estimated_roi_percent = Column(Integer)
    risk_level = Column(String(50))  # low, medium, high
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
```

#### **B. API Endpoint** (app.py)
```python
POST /produce-assistant/recommend-crop
```

**Request Body:**
```json
{
  "user_id": 1,
  "location_state": "Ogun",
  "location_area": "Abeokuta",
  "current_season": "rainy",
  "land_size_hectares": 5,
  "available_workers": 8,
  "budget_kobo": 200000000,  // 2,000,000 NGN
  "experience_level": "beginner",
  "farming_type": "crop"
}
```

**Response:**
```json
{
  "id": 1,
  "recommended_crops": [
    {
      "crop": "maize",
      "suitability_score": 95,
      "reason": "High demand, suitable for rainy season, beginner-friendly, good ROI",
      "estimated_roi_percent": 45,
      "harvest_duration_days": 90,
      "required_workers": 6,
      "estimated_cost": 150000000,
      "estimated_revenue": 217500000
    },
    {
      "crop": "cassava",
      "suitability_score": 85,
      "reason": "Very hardy, low maintenance, suitable for Ogun state soil",
      "estimated_roi_percent": 35,
      "harvest_duration_days": 365,
      "required_workers": 4,
      "estimated_cost": 100000000,
      "estimated_revenue": 135000000
    },
    {
      "crop": "vegetable (tomato/pepper)",
      "suitability_score": 75,
      "reason": "Higher profit margin but requires more experience",
      "estimated_roi_percent": 60,
      "harvest_duration_days": 60,
      "required_workers": 8,
      "estimated_cost": 180000000,
      "estimated_revenue": 288000000
    }
  ],
  "overall_recommendation": "Start with maize for reliable income, then expand to vegetables as you gain experience.",
  "risk_level": "medium",
  "tips": [
    "Rainy season is optimal for maize in Ogun state",
    "Consider crop rotation for soil health",
    "Budget allows for good quality inputs"
  ]
}
```

#### **C. Recommendation Logic** (Create calculator.py or ai_assistant.py)

**Regional Crop Database:**
```python
REGIONAL_CROP_SUITABILITY = {
    'Ogun': {
        'rainy_season': ['maize', 'cassava', 'rice', 'tomato', 'pepper', 'okra'],
        'dry_season': ['cassava', 'yam', 'vegetables'],
        'soil_type': 'loamy'
    },
    'Lagos': {
        'rainy_season': ['vegetables', 'cassava', 'plantain'],
        'dry_season': ['vegetables', 'cassava'],
        'soil_type': 'sandy-loam'
    },
    'Kano': {
        'rainy_season': ['millet', 'sorghum', 'groundnut', 'rice'],
        'dry_season': ['wheat', 'vegetables'],
        'soil_type': 'sandy'
    }
    # Add more states
}

CROP_PROFILES = {
    'maize': {
        'difficulty': 'beginner',
        'min_land_hectares': 1,
        'workers_per_hectare': 1.2,
        'cost_per_hectare_kobo': 30000000,  // 300,000 NGN
        'revenue_per_hectare_kobo': 43500000,  // 435,000 NGN
        'harvest_days': 90,
        'season': ['rainy'],
        'roi_percent': 45
    },
    'cassava': {
        'difficulty': 'beginner',
        'min_land_hectares': 0.5,
        'workers_per_hectare': 0.8,
        'cost_per_hectare_kobo': 20000000,
        'revenue_per_hectare_kobo': 27000000,
        'harvest_days': 365,
        'season': ['all'],
        'roi_percent': 35
    }
    # Add more crops
}
```

**Recommendation Algorithm:**
```python
def recommend_crops(location, season, land_size, workers, budget, experience):
    # 1. Filter crops suitable for location and season
    suitable_crops = REGIONAL_CROP_SUITABILITY[location][f'{season}_season']
    
    recommendations = []
    
    for crop in suitable_crops:
        profile = CROP_PROFILES[crop]
        
        # 2. Check if beginner-friendly
        if experience == 'beginner' and profile['difficulty'] not in ['beginner', 'easy']:
            continue
        
        # 3. Check land requirements
        if land_size < profile['min_land_hectares']:
            continue
        
        # 4. Check worker availability
        required_workers = profile['workers_per_hectare'] * land_size
        if workers < required_workers:
            continue
        
        # 5. Check budget
        total_cost = profile['cost_per_hectare_kobo'] * land_size
        if budget < total_cost:
            continue
        
        # 6. Calculate suitability score
        score = calculate_suitability_score(crop, location, season, experience)
        
        recommendations.append({
            'crop': crop,
            'suitability_score': score,
            'estimated_cost': total_cost,
            'estimated_revenue': profile['revenue_per_hectare_kobo'] * land_size,
            'roi_percent': profile['roi_percent']
        })
    
    # Sort by suitability score
    recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
    
    return recommendations[:3]  # Top 3 recommendations
```

---

## Implementation Files Structure

```
FLB extended/
├── models.py  (Add 3 new models)
│   ├── ProduceCalculation
│   ├── ShelfLifeCalculation
│   └── PlantingRecommendation
│
├── app.py  (Add 3 new endpoints)
│   ├── POST /produce-assistant/calculate-cost
│   ├── POST /produce-assistant/calculate-shelf-life
│   └── POST /produce-assistant/recommend-crop
│
├── calculator.py  (NEW - Business logic)
│   ├── calculate_produce_cost()
│   ├── calculate_shelf_life()
│   ├── recommend_crops()
│   ├── CROP_SHELF_LIFE_DATA
│   ├── REGIONAL_CROP_SUITABILITY
│   └── CROP_PROFILES
│
└── tests/
    └── test_produce_assistant.py  (NEW - Tests)
        ├── test_calculate_cost_basic()
        ├── test_calculate_cost_with_high_margin()
        ├── test_shelf_life_tomato_heat_exposure()
        ├── test_shelf_life_cassava_optimal_conditions()
        ├── test_recommend_crop_beginner()
        └── test_recommend_crop_insufficient_budget()
```

---

## Dependencies

**No new packages needed!** Everything can be built with:
- Python standard library (datetime, json)
- Existing SQLAlchemy
- Existing Flask

---

## Testing Requirements

1. **Cost Calculator Tests:**
   - Basic calculation with all fields
   - Zero profit margin edge case
   - Very high profit margin (200%+)
   - Division by zero protection (0 yield)

2. **Shelf Life Tests:**
   - Different crops at optimal conditions
   - High heat exposure scenarios
   - Very long transport times
   - Unknown crop type handling

3. **AI Recommender Tests:**
   - Perfect match scenario
   - Insufficient budget
   - Too few workers
   - Wrong season for crop
   - Beginner vs expert recommendations

---

## Summary

**Models**: 3 new database models  
**Endpoints**: 3 new API endpoints  
**Logic File**: 1 new `calculator.py` with crop/region data  
**Tests**: 1 new test file with ~15 tests  
**Data**: Crop profiles, regional suitability, shelf life database

**All deterministic (no external APIs needed)** - Can be built entirely with local logic and data!
