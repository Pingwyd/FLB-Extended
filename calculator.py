"""
Produce Assistant Calculator Functions
Contains business logic for cost calculation, shelf life estimation, and crop recommendations
"""


def calculate_produce_cost(data):
    """
    Calculate the total cost, selling price, and profit for farm produce.
    
    Args:
        data (dict): Input parameters including costs, yield, and profit margin
        
    Returns:
        dict: Calculated financial metrics
        
    Raises:
        ValueError: If expected_yield_kg is zero or negative
    """
    # Validate inputs
    if data.get('expected_yield_kg', 0) <= 0:
        raise ValueError("Expected yield must be greater than zero")
    
    if data.get('profit_margin_percent', 0) < 0:
        raise ValueError("Profit margin cannot be negative")
    
    # Sum all costs
    total_cost = (
        data.get('labor_cost', 0) +
        data.get('seed_cost', 0) +
        data.get('fertilizer_cost', 0) +
        data.get('pesticide_cost', 0) +
        data.get('water_cost', 0) +
        data.get('electricity_cost', 0) +
        data.get('transport_cost', 0) +
        data.get('other_expenses', 0)
    )
    
    # Calculate per kg cost
    cost_per_kg = total_cost / data['expected_yield_kg']  # Float division for Naira
    
    # Calculate selling price with profit margin
    profit_margin_percent = data.get('profit_margin_percent', 0)
    profit_multiplier = 1 + (profit_margin_percent / 100)
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


def get_cost_breakdown(data):
    """
    Get a breakdown of costs by category.
    
    Args:
        data (dict): Cost data
        
    Returns:
        dict: Categorized cost breakdown
    """
    labor = data.get('labor_cost', 0)
    materials = (
        data.get('seed_cost', 0) +
        data.get('fertilizer_cost', 0) +
        data.get('pesticide_cost', 0)
    )
    utilities = (
        data.get('water_cost', 0) +
        data.get('electricity_cost', 0)
    )
    transport = data.get('transport_cost', 0)
    other = data.get('other_expenses', 0)
    
    total = labor + materials + utilities + transport + other
    
    # Calculate percentages
    breakdown = {
        'labor': {
            'amount': labor,
            'percentage': round((labor / total * 100), 2) if total > 0 else 0
        },
        'materials': {
            'amount': materials,
            'percentage': round((materials / total * 100), 2) if total > 0 else 0
        },
        'utilities': {
            'amount': utilities,
            'percentage': round((utilities / total * 100), 2) if total > 0 else 0
        },
        'transport': {
            'amount': transport,
            'percentage': round((transport / total * 100), 2) if total > 0 else 0
        },
        'other': {
            'amount': other,
            'percentage': round((other / total * 100), 2) if total > 0 else 0
        },
        'total': total
    }
    
    return breakdown


def get_profitability_analysis(total_cost, total_profit, total_revenue):
    """
    Analyze the profitability of the farming operation.
    
    Args:
        total_cost (float): Total cost in Naira
        total_profit (float): Total profit in Naira
        total_revenue (float): Total revenue in Naira
        
    Returns:
        dict: Profitability metrics and recommendations
    """
    # Calculate actual profit margin
    actual_margin = round((total_profit / total_revenue * 100), 2) if total_revenue > 0 else 0
    
    # Calculate ROI
    roi = round((total_profit / total_cost * 100), 2) if total_cost > 0 else 0
    
    # Profitability rating
    if roi >= 50:
        rating = "excellent"
        recommendation = "High profitability expected. Good investment opportunity."
    elif roi >= 30:
        rating = "good"
        recommendation = "Solid profit margins. Recommended for experienced farmers."
    elif roi >= 15:
        rating = "moderate"
        recommendation = "Moderate returns. Consider cost optimization strategies."
    elif roi >= 5:
        rating = "low"
        recommendation = "Low profit margins. Review costs and consider alternative crops."
    else:
        rating = "poor"
        recommendation = "Minimal or negative returns. High risk investment."
    
    return {
        'roi_percent': roi,
        'profit_margin_percent': actual_margin,
        'rating': rating,
        'recommendation': recommendation,
        'break_even_required': total_cost > 0
    }


# ============== SHELF LIFE CALCULATOR ==============

# Baseline shelf life data for common Nigerian produce (in days at optimal storage)
PRODUCE_SHELF_LIFE = {
    # Vegetables
    'tomato': {'base_days': 14, 'optimal_temp': 13, 'optimal_humidity': 90, 'category': 'vegetable'},
    'pepper': {'base_days': 21, 'optimal_temp': 7, 'optimal_humidity': 90, 'category': 'vegetable'},
    'onion': {'base_days': 90, 'optimal_temp': 0, 'optimal_humidity': 65, 'category': 'vegetable'},
    'cabbage': {'base_days': 90, 'optimal_temp': 0, 'optimal_humidity': 95, 'category': 'vegetable'},
    'carrot': {'base_days': 120, 'optimal_temp': 0, 'optimal_humidity': 95, 'category': 'vegetable'},
    'lettuce': {'base_days': 14, 'optimal_temp': 0, 'optimal_humidity': 95, 'category': 'vegetable'},
    
    # Grains
    'maize': {'base_days': 180, 'optimal_temp': 15, 'optimal_humidity': 14, 'category': 'grain'},
    'rice': {'base_days': 365, 'optimal_temp': 15, 'optimal_humidity': 14, 'category': 'grain'},
    'millet': {'base_days': 180, 'optimal_temp': 15, 'optimal_humidity': 14, 'category': 'grain'},
    'sorghum': {'base_days': 180, 'optimal_temp': 15, 'optimal_humidity': 14, 'category': 'grain'},
    
    # Tubers
    'yam': {'base_days': 180, 'optimal_temp': 16, 'optimal_humidity': 75, 'category': 'tuber'},
    'cassava': {'base_days': 7, 'optimal_temp': 0, 'optimal_humidity': 85, 'category': 'tuber'},
    'potato': {'base_days': 120, 'optimal_temp': 4, 'optimal_humidity': 90, 'category': 'tuber'},
    'sweet_potato': {'base_days': 90, 'optimal_temp': 13, 'optimal_humidity': 85, 'category': 'tuber'},
    
    # Fruits
    'banana': {'base_days': 14, 'optimal_temp': 13, 'optimal_humidity': 90, 'category': 'fruit'},
    'plantain': {'base_days': 21, 'optimal_temp': 12, 'optimal_humidity': 90, 'category': 'fruit'},
    'orange': {'base_days': 60, 'optimal_temp': 3, 'optimal_humidity': 90, 'category': 'fruit'},
    'mango': {'base_days': 21, 'optimal_temp': 13, 'optimal_humidity': 85, 'category': 'fruit'},
    'pineapple': {'base_days': 28, 'optimal_temp': 7, 'optimal_humidity': 90, 'category': 'fruit'},
    'watermelon': {'base_days': 21, 'optimal_temp': 10, 'optimal_humidity': 90, 'category': 'fruit'},
    
    # Legumes
    'beans': {'base_days': 365, 'optimal_temp': 15, 'optimal_humidity': 14, 'category': 'legume'},
    'groundnut': {'base_days': 180, 'optimal_temp': 10, 'optimal_humidity': 65, 'category': 'legume'},
    'soybean': {'base_days': 365, 'optimal_temp': 15, 'optimal_humidity': 14, 'category': 'legume'},
}

# Storage method modifiers (multiplier for shelf life)
STORAGE_METHOD_MULTIPLIERS = {
    'cold_storage': 1.5,
    'refrigerated': 1.3,
    'warehouse': 0.9,
    'room_temp': 0.6,
    'outdoor': 0.4,
}

# Packaging type modifiers
PACKAGING_MULTIPLIERS = {
    'vacuum': 1.4,
    'sealed': 1.2,
    'crates': 1.0,
    'open': 0.7,
    'bags': 0.9,
}


def calculate_shelf_life(data):
    """
    Calculate predicted shelf life for produce based on storage conditions.
    
    Args:
        data (dict): Input parameters including produce type, storage conditions, harvest date
        
    Returns:
        dict: Shelf life predictions and quality timeline
        
    Raises:
        ValueError: If produce type is not recognized or dates are invalid
    """
    import datetime
    
    produce_type = data.get('produce_type', '').lower()
    
    # Validate produce type
    if produce_type not in PRODUCE_SHELF_LIFE:
        available = ', '.join(sorted(PRODUCE_SHELF_LIFE.keys()))
        raise ValueError(f"Unknown produce type: {produce_type}. Available: {available}")
    
    # Get baseline data
    baseline = PRODUCE_SHELF_LIFE[produce_type]
    base_days = baseline['base_days']
    
    # Get storage conditions
    storage_method = data.get('storage_method', 'room_temp').lower()
    storage_temp = data.get('storage_temperature_celsius')
    storage_humidity = data.get('storage_humidity_percent')
    packaging = data.get('packaging_type', 'open').lower()
    
    # Calculate storage method modifier
    storage_modifier = STORAGE_METHOD_MULTIPLIERS.get(storage_method, 0.8)
    
    # Calculate packaging modifier
    packaging_modifier = PACKAGING_MULTIPLIERS.get(packaging, 1.0)
    
    # Temperature impact (if provided)
    temp_modifier = 1.0
    if storage_temp is not None:
        optimal_temp = baseline['optimal_temp']
        temp_diff = abs(storage_temp - optimal_temp)
        
        # For every 5 degrees away from optimal, reduce shelf life by 15%
        temp_modifier = max(0.3, 1.0 - (temp_diff / 5 * 0.15))
    
    # Humidity impact (if provided)
    humidity_modifier = 1.0
    if storage_humidity is not None:
        optimal_humidity = baseline['optimal_humidity']
        humidity_diff = abs(storage_humidity - optimal_humidity)
        
        # For every 10% humidity difference, reduce shelf life by 10%
        humidity_modifier = max(0.5, 1.0 - (humidity_diff / 10 * 0.10))
    
    # Calculate final shelf life
    predicted_days = int(base_days * storage_modifier * packaging_modifier * temp_modifier * humidity_modifier)
    predicted_days = max(1, predicted_days)  # At least 1 day
    
    # Calculate quality degradation rate (percentage per day)
    quality_degradation_rate = round(100.0 / predicted_days, 2)
    
    # Parse harvest date
    harvest_date = data.get('harvest_date')
    if isinstance(harvest_date, str):
        harvest_date = datetime.datetime.fromisoformat(harvest_date.replace('Z', '+00:00'))
    elif not isinstance(harvest_date, datetime.datetime):
        harvest_date = datetime.datetime.now(datetime.timezone.utc)
    
    # Calculate milestone dates
    optimal_sell_by = harvest_date + datetime.timedelta(days=int(predicted_days * 0.7))
    spoilage_date = harvest_date + datetime.timedelta(days=predicted_days)
    
    # Quality milestones
    excellent_until = harvest_date + datetime.timedelta(days=int(predicted_days * 0.3))
    good_until = harvest_date + datetime.timedelta(days=int(predicted_days * 0.6))
    fair_until = harvest_date + datetime.timedelta(days=int(predicted_days * 0.85))
    
    return {
        'predicted_shelf_life_days': predicted_days,
        'quality_degradation_rate': quality_degradation_rate,
        'optimal_sell_by_date': optimal_sell_by,
        'spoilage_date': spoilage_date,
        'excellent_quality_until': excellent_until,
        'good_quality_until': good_until,
        'fair_quality_until': fair_until,
        'modifiers_applied': {
            'storage_method': storage_modifier,
            'packaging': packaging_modifier,
            'temperature': temp_modifier,
            'humidity': humidity_modifier
        }
    }


def get_storage_recommendations(produce_type, current_storage):
    """
    Get recommendations for optimal storage to maximize shelf life.
    
    Args:
        produce_type (str): Type of produce
        current_storage (dict): Current storage conditions
        
    Returns:
        dict: Storage recommendations and improvement suggestions
    """
    produce_type = produce_type.lower()
    
    if produce_type not in PRODUCE_SHELF_LIFE:
        return {'error': f'Unknown produce type: {produce_type}'}
    
    baseline = PRODUCE_SHELF_LIFE[produce_type]
    recommendations = []
    
    # Temperature recommendation
    optimal_temp = baseline['optimal_temp']
    current_temp = current_storage.get('storage_temperature_celsius')
    
    if current_temp is not None:
        if abs(current_temp - optimal_temp) > 5:
            recommendations.append(
                f"Adjust temperature to {optimal_temp}°C (currently {current_temp}°C) for optimal preservation."
            )
    else:
        recommendations.append(f"Maintain storage temperature at {optimal_temp}°C for best results.")
    
    # Humidity recommendation
    optimal_humidity = baseline['optimal_humidity']
    current_humidity = current_storage.get('storage_humidity_percent')
    
    if current_humidity is not None:
        if abs(current_humidity - optimal_humidity) > 10:
            recommendations.append(
                f"Adjust humidity to {optimal_humidity}% (currently {current_humidity}%) to prevent spoilage."
            )
    else:
        recommendations.append(f"Maintain storage humidity at {optimal_humidity}% for optimal freshness.")
    
    # Storage method recommendation
    storage_method = current_storage.get('storage_method', 'room_temp')
    if storage_method in ['room_temp', 'outdoor'] and baseline['category'] in ['vegetable', 'fruit']:
        recommendations.append(
            "Consider using cold storage or refrigeration to significantly extend shelf life."
        )
    
    # Packaging recommendation
    packaging = current_storage.get('packaging_type', 'open')
    if packaging == 'open':
        recommendations.append(
            "Use sealed or vacuum packaging to reduce moisture loss and contamination."
        )
    
    return {
        'optimal_conditions': {
            'temperature_celsius': optimal_temp,
            'humidity_percent': optimal_humidity,
            'storage_method': 'cold_storage' if baseline['category'] in ['vegetable', 'fruit'] else 'warehouse',
            'packaging': 'sealed' if baseline['category'] in ['vegetable', 'fruit'] else 'bags'
        },
        'recommendations': recommendations,
        'category': baseline['category'],
        'baseline_shelf_life_days': baseline['base_days']
    }


def get_quality_timeline(harvest_date, predicted_days):
    """
    Generate a timeline showing quality degradation over time.
    
    Args:
        harvest_date (datetime): Date of harvest
        predicted_days (int): Predicted shelf life in days
        
    Returns:
        list: Timeline of quality checkpoints
    """
    import datetime
    
    if isinstance(harvest_date, str):
        harvest_date = datetime.datetime.fromisoformat(harvest_date.replace('Z', '+00:00'))
    
    timeline = [
        {
            'day': 0,
            'date': harvest_date.isoformat(),
            'quality_percent': 100,
            'status': 'excellent',
            'description': 'Freshly harvested - peak quality'
        },
        {
            'day': int(predicted_days * 0.3),
            'date': (harvest_date + datetime.timedelta(days=int(predicted_days * 0.3))).isoformat(),
            'quality_percent': 90,
            'status': 'excellent',
            'description': 'Still in excellent condition'
        },
        {
            'day': int(predicted_days * 0.6),
            'date': (harvest_date + datetime.timedelta(days=int(predicted_days * 0.6))).isoformat(),
            'quality_percent': 70,
            'status': 'good',
            'description': 'Good quality - recommended sell-by period'
        },
        {
            'day': int(predicted_days * 0.85),
            'date': (harvest_date + datetime.timedelta(days=int(predicted_days * 0.85))).isoformat(),
            'quality_percent': 50,
            'status': 'fair',
            'description': 'Fair quality - sell soon or process'
        },
        {
            'day': predicted_days,
            'date': (harvest_date + datetime.timedelta(days=predicted_days)).isoformat(),
            'quality_percent': 30,
            'status': 'poor',
            'description': 'Approaching spoilage - not recommended for sale'
        }
    ]
    
    return timeline


# ================== CROP RECOMMENDATION FUNCTIONS ==================

# Comprehensive crop database with suitability criteria
CROP_DATABASE = {
    'maize': {
        'soil_types': ['loamy', 'sandy_loam', 'silt'],
        'soil_ph_range': (5.5, 7.5),
        'climate_zones': ['tropical', 'subtropical', 'temperate'],
        'rainfall_mm': (500, 1200),
        'temperature_range': (20, 30),
        'seasons': ['rainy_season', 'early_dry'],
        'difficulty': 'beginner',
        'budget': 'low',
        'yield_kg_per_hectare': (2000, 4000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    },
    'rice': {
        'soil_types': ['clay', 'loamy', 'clay_loam'],
        'soil_ph_range': (5.0, 7.0),
        'climate_zones': ['tropical', 'subtropical'],
        'rainfall_mm': (1000, 2000),
        'temperature_range': (20, 35),
        'seasons': ['rainy_season'],
        'difficulty': 'intermediate',
        'budget': 'medium',
        'yield_kg_per_hectare': (3000, 6000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    },
    'cassava': {
        'soil_types': ['sandy', 'loamy', 'sandy_loam'],
        'soil_ph_range': (4.5, 7.0),
        'climate_zones': ['tropical', 'subtropical'],
        'rainfall_mm': (600, 1500),
        'temperature_range': (25, 35),
        'seasons': ['rainy_season', 'dry_season'],
        'difficulty': 'beginner',
        'budget': 'low',
        'yield_kg_per_hectare': (10000, 25000),
        'market_demand': 'high',
        'irrigation_tolerance': False
    },
    'yam': {
        'soil_types': ['loamy', 'sandy_loam', 'silt'],
        'soil_ph_range': (5.5, 6.5),
        'climate_zones': ['tropical'],
        'rainfall_mm': (1000, 1500),
        'temperature_range': (25, 30),
        'seasons': ['rainy_season'],
        'difficulty': 'intermediate',
        'budget': 'medium',
        'yield_kg_per_hectare': (8000, 15000),
        'market_demand': 'high',
        'irrigation_tolerance': False
    },
    'tomato': {
        'soil_types': ['loamy', 'sandy_loam'],
        'soil_ph_range': (6.0, 7.0),
        'climate_zones': ['tropical', 'subtropical', 'temperate'],
        'rainfall_mm': (400, 800),
        'temperature_range': (18, 27),
        'seasons': ['dry_season', 'harmattan'],
        'difficulty': 'intermediate',
        'budget': 'medium',
        'yield_kg_per_hectare': (15000, 35000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    },
    'pepper': {
        'soil_types': ['loamy', 'sandy_loam'],
        'soil_ph_range': (6.0, 7.0),
        'climate_zones': ['tropical', 'subtropical'],
        'rainfall_mm': (600, 1200),
        'temperature_range': (20, 30),
        'seasons': ['rainy_season', 'dry_season'],
        'difficulty': 'intermediate',
        'budget': 'medium',
        'yield_kg_per_hectare': (2000, 5000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    },
    'beans': {
        'soil_types': ['loamy', 'sandy_loam', 'silt'],
        'soil_ph_range': (6.0, 7.5),
        'climate_zones': ['tropical', 'subtropical', 'temperate'],
        'rainfall_mm': (400, 800),
        'temperature_range': (15, 25),
        'seasons': ['rainy_season', 'early_dry'],
        'difficulty': 'beginner',
        'budget': 'low',
        'yield_kg_per_hectare': (800, 1500),
        'market_demand': 'high',
        'irrigation_tolerance': False
    },
    'groundnut': {
        'soil_types': ['sandy', 'sandy_loam', 'loamy'],
        'soil_ph_range': (5.9, 6.3),
        'climate_zones': ['tropical', 'subtropical'],
        'rainfall_mm': (500, 1000),
        'temperature_range': (20, 30),
        'seasons': ['rainy_season'],
        'difficulty': 'beginner',
        'budget': 'low',
        'yield_kg_per_hectare': (1000, 2500),
        'market_demand': 'high',
        'irrigation_tolerance': False
    },
    'sorghum': {
        'soil_types': ['sandy', 'loamy', 'clay'],
        'soil_ph_range': (5.5, 8.5),
        'climate_zones': ['tropical', 'subtropical', 'arid'],
        'rainfall_mm': (400, 800),
        'temperature_range': (25, 35),
        'seasons': ['rainy_season', 'dry_season'],
        'difficulty': 'beginner',
        'budget': 'low',
        'yield_kg_per_hectare': (1500, 3500),
        'market_demand': 'medium',
        'irrigation_tolerance': False
    },
    'millet': {
        'soil_types': ['sandy', 'sandy_loam'],
        'soil_ph_range': (5.0, 7.0),
        'climate_zones': ['tropical', 'arid', 'semi_arid'],
        'rainfall_mm': (300, 600),
        'temperature_range': (25, 35),
        'seasons': ['rainy_season', 'harmattan'],
        'difficulty': 'beginner',
        'budget': 'low',
        'yield_kg_per_hectare': (800, 2000),
        'market_demand': 'medium',
        'irrigation_tolerance': False
    },
    'okra': {
        'soil_types': ['loamy', 'sandy_loam'],
        'soil_ph_range': (6.0, 6.8),
        'climate_zones': ['tropical', 'subtropical'],
        'rainfall_mm': (600, 1000),
        'temperature_range': (24, 32),
        'seasons': ['rainy_season', 'dry_season'],
        'difficulty': 'beginner',
        'budget': 'low',
        'yield_kg_per_hectare': (5000, 10000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    },
    'watermelon': {
        'soil_types': ['sandy', 'sandy_loam', 'loamy'],
        'soil_ph_range': (6.0, 7.0),
        'climate_zones': ['tropical', 'subtropical', 'arid'],
        'rainfall_mm': (400, 600),
        'temperature_range': (21, 30),
        'seasons': ['dry_season'],
        'difficulty': 'intermediate',
        'budget': 'medium',
        'yield_kg_per_hectare': (20000, 40000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    },
    'cucumber': {
        'soil_types': ['loamy', 'sandy_loam'],
        'soil_ph_range': (6.0, 7.0),
        'climate_zones': ['tropical', 'subtropical', 'temperate'],
        'rainfall_mm': (400, 800),
        'temperature_range': (18, 28),
        'seasons': ['dry_season', 'rainy_season'],
        'difficulty': 'beginner',
        'budget': 'low',
        'yield_kg_per_hectare': (10000, 25000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    },
    'cabbage': {
        'soil_types': ['loamy', 'clay_loam'],
        'soil_ph_range': (6.0, 7.5),
        'climate_zones': ['temperate', 'subtropical'],
        'rainfall_mm': (400, 800),
        'temperature_range': (15, 25),
        'seasons': ['dry_season', 'harmattan'],
        'difficulty': 'intermediate',
        'budget': 'medium',
        'yield_kg_per_hectare': (25000, 50000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    },
    'onion': {
        'soil_types': ['loamy', 'sandy_loam', 'silt'],
        'soil_ph_range': (6.0, 7.5),
        'climate_zones': ['tropical', 'subtropical', 'temperate'],
        'rainfall_mm': (350, 550),
        'temperature_range': (13, 24),
        'seasons': ['dry_season'],
        'difficulty': 'intermediate',
        'budget': 'medium',
        'yield_kg_per_hectare': (15000, 30000),
        'market_demand': 'high',
        'irrigation_tolerance': True
    }
}


def calculate_crop_suitability(crop_name, crop_data, user_conditions):
    """
    Calculate suitability score for a specific crop based on user's conditions.
    Returns score 0-100 and factors affecting the score.
    """
    score = 0
    max_score = 0
    factors = []
    
    # Soil type match (20 points)
    max_score += 20
    if user_conditions.get('soil_type') in crop_data['soil_types']:
        score += 20
        factors.append(f"Excellent soil match ({user_conditions.get('soil_type')})")
    elif user_conditions.get('soil_type'):
        # Partial match for similar soils
        user_soil = user_conditions.get('soil_type', '').lower()
        if any(soil in user_soil or user_soil in soil for soil in crop_data['soil_types']):
            score += 10
            factors.append(f"Acceptable soil type ({user_conditions.get('soil_type')})")
    
    # Soil pH (15 points)
    max_score += 15
    if user_conditions.get('soil_ph'):
        ph = user_conditions['soil_ph']
        min_ph, max_ph = crop_data['soil_ph_range']
        if min_ph <= ph <= max_ph:
            score += 15
            factors.append(f"Optimal pH level ({ph})")
        elif min_ph - 0.5 <= ph <= max_ph + 0.5:
            score += 10
            factors.append(f"Acceptable pH level ({ph})")
        else:
            factors.append(f"pH {ph} outside optimal range ({min_ph}-{max_ph})")
    
    # Climate zone (20 points)
    max_score += 20
    if user_conditions.get('climate_zone') in crop_data['climate_zones']:
        score += 20
        factors.append(f"Perfect climate match ({user_conditions.get('climate_zone')})")
    
    # Rainfall (15 points)
    max_score += 15
    if user_conditions.get('average_rainfall_mm'):
        rainfall = user_conditions['average_rainfall_mm']
        min_rain, max_rain = crop_data['rainfall_mm']
        if min_rain <= rainfall <= max_rain:
            score += 15
            factors.append(f"Ideal rainfall ({rainfall}mm)")
        elif min_rain * 0.8 <= rainfall <= max_rain * 1.2:
            score += 10
            factors.append(f"Acceptable rainfall ({rainfall}mm)")
        elif user_conditions.get('irrigation_available') and rainfall < min_rain:
            score += 12
            factors.append(f"Low rainfall ({rainfall}mm) but irrigation available")
    
    # Temperature (15 points)
    max_score += 15
    if user_conditions.get('average_temperature_celsius'):
        temp = user_conditions['average_temperature_celsius']
        min_temp, max_temp = crop_data['temperature_range']
        if min_temp <= temp <= max_temp:
            score += 15
            factors.append(f"Optimal temperature ({temp}°C)")
        elif min_temp - 3 <= temp <= max_temp + 3:
            score += 10
            factors.append(f"Acceptable temperature ({temp}°C)")
    
    # Season (10 points)
    max_score += 10
    if user_conditions.get('season') in crop_data['seasons']:
        score += 10
        factors.append(f"Right season ({user_conditions.get('season')})")
    
    # Experience level (5 points)
    max_score += 5
    if user_conditions.get('experience_level'):
        user_exp = user_conditions['experience_level']
        crop_diff = crop_data['difficulty']
        if crop_diff == 'beginner' or user_exp in ['intermediate', 'expert']:
            score += 5
        elif user_exp == 'beginner' and crop_diff == 'intermediate':
            score += 3
            factors.append(f"Moderate difficulty for beginner")
    
    # Budget (5 points)
    max_score += 5
    if user_conditions.get('budget_category'):
        user_budget = user_conditions['budget_category']
        crop_budget = crop_data['budget']
        budget_levels = {'low': 1, 'medium': 2, 'high': 3}
        if budget_levels.get(user_budget, 2) >= budget_levels.get(crop_budget, 2):
            score += 5
    
    # Irrigation requirement (5 points)
    max_score += 5
    if user_conditions.get('irrigation_available') or not crop_data.get('irrigation_tolerance'):
        score += 5
    elif not user_conditions.get('irrigation_available') and crop_data.get('irrigation_tolerance'):
        factors.append(f"May need irrigation for best results")
    
    # Normalize to 100
    final_score = int((score / max_score) * 100) if max_score > 0 else 0
    
    return {
        'score': final_score,
        'factors': factors,
        'market_demand': crop_data.get('market_demand', 'medium'),
        'yield_range': crop_data.get('yield_kg_per_hectare'),
        'difficulty': crop_data.get('difficulty', 'intermediate')
    }


def get_crop_recommendations(user_conditions):
    """
    Get top crop recommendations based on user's land and climate conditions.
    
    Args:
        user_conditions (dict): User's land, climate, and preference data
        
    Returns:
        dict: Top recommendations, confidence, and analysis
    """
    crop_scores = []
    
    # Evaluate each crop
    for crop_name, crop_data in CROP_DATABASE.items():
        result = calculate_crop_suitability(crop_name, crop_data, user_conditions)
        crop_scores.append({
            'crop_name': crop_name,
            'suitability_score': result['score'],
            'confidence_factors': result['factors'],
            'market_demand': result['market_demand'],
            'estimated_yield_kg_per_hectare': f"{result['yield_range'][0]}-{result['yield_range'][1]}",
            'difficulty_level': result['difficulty'],
            'yield_range': result['yield_range']
        })
    
    # Sort by suitability score
    crop_scores.sort(key=lambda x: x['suitability_score'], reverse=True)
    
    # Get top 5 recommendations
    top_crops = crop_scores[:5]
    alternative_crops = crop_scores[5:8]
    
    # Calculate overall confidence
    if top_crops:
        avg_top_score = sum(c['suitability_score'] for c in top_crops) / len(top_crops)
        confidence_score = min(avg_top_score, 100)
    else:
        confidence_score = 0
    
    # Determine market potential based on top crops
    high_demand_count = sum(1 for c in top_crops if c['market_demand'] == 'high')
    if high_demand_count >= 3:
        market_potential = 'high'
    elif high_demand_count >= 1:
        market_potential = 'medium'
    else:
        market_potential = 'low'
    
    return {
        'recommended_crops': top_crops,
        'alternative_crops': alternative_crops,
        'confidence_score': round(confidence_score, 2),
        'market_potential': market_potential
    }


def analyze_risk_factors(user_conditions, top_crops):
    """
    Analyze potential risks based on conditions and recommended crops.
    """
    risks = []
    
    # Climate risks
    if user_conditions.get('climate_zone') == 'arid':
        risks.append("Water scarcity - ensure adequate irrigation infrastructure")
    
    if not user_conditions.get('irrigation_available'):
        risks.append("No irrigation - dependent on rainfall patterns")
    
    # Soil risks
    if user_conditions.get('soil_ph'):
        ph = user_conditions['soil_ph']
        if ph < 5.5:
            risks.append("Acidic soil - may need lime treatment")
        elif ph > 7.5:
            risks.append("Alkaline soil - may need sulfur treatment")
    
    # Experience risks
    if user_conditions.get('experience_level') == 'beginner':
        intermediate_crops = [c for c in top_crops if c.get('difficulty_level') == 'intermediate']
        if intermediate_crops:
            risks.append("Some recommended crops require intermediate skills - consider training")
    
    # Budget risks
    if user_conditions.get('budget_category') == 'low':
        risks.append("Limited budget - prioritize low-input crops and phased planting")
    
    # Season risks
    if user_conditions.get('season') == 'dry_season' and not user_conditions.get('irrigation_available'):
        risks.append("Dry season without irrigation - limited crop options")
    
    return risks


def analyze_success_factors(user_conditions, top_crops):
    """
    Identify key factors for success based on conditions and crops.
    """
    factors = []
    
    # Positive conditions
    if user_conditions.get('irrigation_available'):
        factors.append("Irrigation available - enables year-round farming and higher yields")
    
    if user_conditions.get('soil_type') in ['loamy', 'sandy_loam']:
        factors.append("Excellent soil type - suitable for wide variety of crops")
    
    if user_conditions.get('climate_zone') == 'tropical':
        factors.append("Tropical climate - ideal for diverse crop production")
    
    # Market factors
    high_demand_crops = [c for c in top_crops if c.get('market_demand') == 'high']
    if len(high_demand_crops) >= 3:
        factors.append("Multiple high-demand crops suitable - strong market opportunities")
    
    # Budget alignment
    if user_conditions.get('budget_category') in ['medium', 'high']:
        factors.append("Adequate budget - can invest in quality inputs and technology")
    
    # Experience
    if user_conditions.get('experience_level') in ['intermediate', 'expert']:
        factors.append("Experienced farmer - can handle complex crops and techniques")
    
    # General success tips
    factors.append("Use certified seeds and follow recommended planting schedules")
    factors.append("Implement crop rotation to maintain soil health")
    factors.append("Monitor weather patterns and adjust practices accordingly")
    
    return factors
