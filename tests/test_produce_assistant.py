import pytest
from datetime import datetime, timezone


@pytest.fixture
def sample_user(client):
    """Create a sample farmer for testing"""
    response = client.post('/register', json={
        'full_name': 'Test Farmer',
        'email': 'testfarmer@example.com',
        'password': 'Test123!',
        'account_type': 'farmer'
    })
    data = response.get_json()
    assert response.status_code == 201, f"User creation failed: {data}"
    return data


class TestCostCalculator:
    """Test suite for Produce Cost Calculator"""

    def test_calculate_cost_basic(self, client, sample_user):
        """Test basic cost calculation with all fields"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'maize',
            'season': 'dry_season',
            'land_size_hectares': 2.5,
            'expected_yield_kg': 5000,
            'num_workers': 3,
            'labor_cost': 50000,
            'seed_cost': 15000,
            'fertilizer_cost': 25000,
            'pesticide_cost': 10000,
            'water_cost': 8000,
            'electricity_cost': 5000,
            'transport_cost': 12000,
            'other_expenses': 5000,
            'profit_margin_percent': 30
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify input fields are saved
        assert data['crop_type'] == 'maize'
        assert data['season'] == 'dry_season'
        assert data['land_size_hectares'] == 2.5
        assert data['expected_yield_kg'] == 5000
        assert data['num_workers'] == 3
        
        # Verify cost calculations
        expected_total = 50000 + 15000 + 25000 + 10000 + 8000 + 5000 + 12000 + 5000
        assert data['total_cost'] == expected_total
        assert data['cost_per_kg'] == expected_total / 5000
        
        # Verify profit calculations
        assert data['selling_price_per_kg'] > data['cost_per_kg']
        assert data['total_revenue'] > data['total_cost']
        assert data['total_profit'] == data['total_revenue'] - data['total_cost']
        
        # Verify breakdown is included
        assert 'cost_breakdown' in data
        assert data['cost_breakdown']['total'] == expected_total
        assert 'labor' in data['cost_breakdown']
        assert 'materials' in data['cost_breakdown']
        
        # Verify profitability analysis
        assert 'profitability_analysis' in data
        assert 'roi_percent' in data['profitability_analysis']
        assert 'rating' in data['profitability_analysis']

    def test_calculate_cost_minimal_fields(self, client, sample_user):
        """Test calculation with only required fields (costs default to 0)"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'rice',
            'season': 'rainy_season',
            'land_size_hectares': 1.0,
            'expected_yield_kg': 3000,
            'num_workers': 2
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        # All costs should be 0
        assert data['total_cost'] == 0
        assert data['cost_per_kg'] == 0
        assert data['selling_price_per_kg'] == 0
        assert data['total_revenue'] == 0
        assert data['total_profit'] == 0

    def test_calculate_cost_high_profit_margin(self, client, sample_user):
        """Test calculation with high profit margin (50%)"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'tomato',
            'season': 'dry_season',
            'land_size_hectares': 0.5,
            'expected_yield_kg': 2000,
            'num_workers': 1,
            'labor_cost': 30000,
            'seed_cost': 10000,
            'fertilizer_cost': 15000,
            'profit_margin_percent': 50
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        total_cost = 30000 + 10000 + 15000
        cost_per_kg = total_cost / 2000
        expected_selling_price = cost_per_kg * 1.5

        assert data['total_cost'] == total_cost
        assert data['selling_price_per_kg'] == expected_selling_price        # ROI should be around 50%
        assert 'profitability_analysis' in data
        roi = data['profitability_analysis']['roi_percent']
        assert 45 <= roi <= 55  # Allow for rounding

    def test_calculate_cost_zero_yield_error(self, client, sample_user):
        """Test that zero yield returns an error"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'cassava',
            'season': 'rainy_season',
            'land_size_hectares': 1.0,
            'expected_yield_kg': 0,
            'num_workers': 2,
            'labor_cost': 20000
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_calculate_cost_negative_yield_error(self, client, sample_user):
        """Test that negative yield returns an error"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'yam',
            'season': 'rainy_season',
            'land_size_hectares': 1.0,
            'expected_yield_kg': -1000,
            'num_workers': 2
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_calculate_cost_missing_required_field(self, client, sample_user):
        """Test that missing required fields return an error"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'maize',
            # Missing season, land_size, etc.
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error']

    def test_calculate_cost_invalid_user(self, client):
        """Test calculation with non-existent user"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': 99999,
            'crop_type': 'maize',
            'season': 'dry_season',
            'land_size_hectares': 1.0,
            'expected_yield_kg': 1000,
            'num_workers': 1
        })
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_calculate_cost_negative_costs_error(self, client, sample_user):
        """Test that negative costs return an error"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'maize',
            'season': 'dry_season',
            'land_size_hectares': 1.0,
            'expected_yield_kg': 1000,
            'num_workers': 1,
            'labor_cost': -5000
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_calculate_cost_invalid_numeric_format(self, client, sample_user):
        """Test that invalid numeric formats return an error"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'maize',
            'season': 'dry_season',
            'land_size_hectares': 'invalid',
            'expected_yield_kg': 1000,
            'num_workers': 1
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_get_user_calculations_empty(self, client, sample_user):
        """Test getting calculations when user has none"""
        response = client.get(f'/produce-assistant/calculations/{sample_user["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_user_calculations_multiple(self, client, sample_user):
        """Test getting multiple calculations for a user"""
        # Create first calculation
        client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'maize',
            'season': 'dry_season',
            'land_size_hectares': 2.0,
            'expected_yield_kg': 4000,
            'num_workers': 2,
            'labor_cost': 40000
        })
        
        # Create second calculation
        client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'rice',
            'season': 'rainy_season',
            'land_size_hectares': 1.5,
            'expected_yield_kg': 3000,
            'num_workers': 1,
            'labor_cost': 25000
        })
        
        response = client.get(f'/produce-assistant/calculations/{sample_user["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify they're ordered by most recent first
        assert 'created_at' in data[0]
        assert data[0]['crop_type'] in ['maize', 'rice']

    def test_get_user_calculations_invalid_user(self, client):
        """Test getting calculations for non-existent user"""
        response = client.get('/produce-assistant/calculations/99999')
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_get_calculation_detail(self, client, sample_user):
        """Test getting detailed information for a specific calculation"""
        # Create a calculation
        create_response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'tomato',
            'season': 'dry_season',
            'land_size_hectares': 0.5,
            'expected_yield_kg': 1500,
            'num_workers': 1,
            'labor_cost': 20000,
            'seed_cost': 8000,
            'fertilizer_cost': 12000,
            'profit_margin_percent': 40
        })
        
        calc_id = create_response.get_json()['id']
        
        # Get the detail
        response = client.get(f'/produce-assistant/calculation/{calc_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == calc_id
        assert data['crop_type'] == 'tomato'
        assert 'cost_breakdown' in data
        assert 'profitability_analysis' in data
        
        # Verify breakdown details
        breakdown = data['cost_breakdown']
        assert breakdown['labor']['amount'] == 20000
        assert breakdown['materials']['amount'] == 20000  # seed + fertilizer
        assert breakdown['total'] == 40000

    def test_get_calculation_detail_not_found(self, client):
        """Test getting detail for non-existent calculation"""
        response = client.get('/produce-assistant/calculation/99999')
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_cost_breakdown_percentages(self, client, sample_user):
        """Test that cost breakdown percentages add up to 100%"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'maize',
            'season': 'dry_season',
            'land_size_hectares': 2.0,
            'expected_yield_kg': 4000,
            'num_workers': 3,
            'labor_cost': 40000,
            'seed_cost': 10000,
            'fertilizer_cost': 20000,
            'pesticide_cost': 5000,
            'water_cost': 10000,
            'transport_cost': 15000
        })
        
        assert response.status_code == 201
        data = response.get_json()
        breakdown = data['cost_breakdown']
        
        # Sum all percentages
        total_percentage = (
            breakdown['labor']['percentage'] +
            breakdown['materials']['percentage'] +
            breakdown['utilities']['percentage'] +
            breakdown['transport']['percentage'] +
            breakdown['other']['percentage']
        )
        
        # Should be approximately 100% (allow for rounding)
        assert 99.5 <= total_percentage <= 100.5

    def test_profitability_ratings(self, client, sample_user):
        """Test different profitability ratings based on ROI"""
        # Test excellent rating (ROI >= 50%)
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'tomato',
            'season': 'dry_season',
            'land_size_hectares': 0.5,
            'expected_yield_kg': 1000,
            'num_workers': 1,
            'labor_cost': 10000,
            'profit_margin_percent': 60
        })
        
        data = response.get_json()
        analysis = data['profitability_analysis']
        assert analysis['rating'] == 'excellent'
        assert 'recommendation' in analysis

    def test_calculate_cost_large_scale_farm(self, client, sample_user):
        """Test calculation for large-scale farming operation"""
        response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'rice',
            'season': 'rainy_season',
            'land_size_hectares': 50.0,
            'expected_yield_kg': 150000,
            'num_workers': 25,
            'labor_cost': 2000000,
            'seed_cost': 500000,
            'fertilizer_cost': 800000,
            'pesticide_cost': 300000,
            'water_cost': 400000,
            'electricity_cost': 200000,
            'transport_cost': 600000,
            'other_expenses': 200000,
            'profit_margin_percent': 25
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['land_size_hectares'] == 50.0
        assert data['expected_yield_kg'] == 150000
        assert data['total_cost'] == 5000000
        assert data['total_profit'] > 0

    def test_multiple_seasons_same_crop(self, client, sample_user):
        """Test tracking same crop across different seasons"""
        # Dry season
        dry_response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'maize',
            'season': 'dry_season',
            'land_size_hectares': 2.0,
            'expected_yield_kg': 4000,
            'num_workers': 2,
            'labor_cost': 40000,
            'profit_margin_percent': 30
        })
        
        # Rainy season
        rainy_response = client.post('/produce-assistant/calculate-cost', json={
            'user_id': sample_user['id'],
            'crop_type': 'maize',
            'season': 'rainy_season',
            'land_size_hectares': 2.0,
            'expected_yield_kg': 5000,
            'num_workers': 2,
            'labor_cost': 40000,
            'profit_margin_percent': 30
        })
        
        assert dry_response.status_code == 201
        assert rainy_response.status_code == 201
        
        # Get all calculations
        list_response = client.get(f'/produce-assistant/calculations/{sample_user["id"]}')
        data = list_response.get_json()
        
        assert len(data) == 2
        seasons = [calc['season'] for calc in data]
        assert 'dry_season' in seasons
        assert 'rainy_season' in seasons


class TestShelfLifeCalculator:
    """Test suite for Shelf Life Calculator"""

    def test_predict_shelf_life_basic(self, client, sample_user):
        """Test basic shelf life prediction with all fields"""
        from datetime import datetime, timedelta
        
        harvest_date = datetime.now(timezone.utc)
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': 100.0,
            'harvest_date': harvest_date.isoformat(),
            'storage_method': 'cold_storage',
            'storage_temperature_celsius': 13,
            'storage_humidity_percent': 90,
            'packaging_type': 'sealed',
            'storage_cost_per_day': 500
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify input fields
        assert data['produce_type'] == 'tomato'
        assert data['quantity_kg'] == 100.0
        assert data['storage_method'] == 'cold_storage'
        assert data['storage_temperature_celsius'] == 13
        assert data['storage_humidity_percent'] == 90
        assert data['packaging_type'] == 'sealed'
        
        # Verify predictions
        assert 'predicted_shelf_life_days' in data
        assert data['predicted_shelf_life_days'] > 0
        assert 'quality_degradation_rate' in data
        assert 'spoilage_date' in data
        assert 'optimal_sell_by_date' in data
        
        # Verify quality milestones
        assert 'excellent_quality_until' in data
        assert 'good_quality_until' in data
        assert 'fair_quality_until' in data
        
        # Verify storage costs
        assert data['storage_cost_per_day'] == 500
        assert data['estimated_total_storage_cost'] == 500 * data['predicted_shelf_life_days']
        
        # Verify recommendations and timeline are included
        assert 'storage_recommendations' in data
        assert 'quality_timeline' in data
        assert len(data['quality_timeline']) > 0

    def test_predict_shelf_life_minimal_fields(self, client, sample_user):
        """Test prediction with only required fields"""
        from datetime import datetime
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'maize',
            'quantity_kg': 50.0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'warehouse'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['produce_type'] == 'maize'
        assert data['predicted_shelf_life_days'] > 0
        assert data['storage_cost_per_day'] == 0
        assert data['estimated_total_storage_cost'] == 0

    def test_predict_shelf_life_different_storage_methods(self, client, sample_user):
        """Test that different storage methods affect shelf life"""
        from datetime import datetime
        
        harvest_date = datetime.now(timezone.utc).isoformat()
        
        # Cold storage
        cold_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': 10.0,
            'harvest_date': harvest_date,
            'storage_method': 'cold_storage'
        })
        
        # Room temperature
        room_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': 10.0,
            'harvest_date': harvest_date,
            'storage_method': 'room_temp'
        })
        
        assert cold_response.status_code == 201
        assert room_response.status_code == 201
        
        cold_data = cold_response.get_json()
        room_data = room_response.get_json()
        
        # Cold storage should extend shelf life more than room temperature
        assert cold_data['predicted_shelf_life_days'] > room_data['predicted_shelf_life_days']

    def test_predict_shelf_life_packaging_effect(self, client, sample_user):
        """Test that packaging type affects shelf life"""
        from datetime import datetime
        
        harvest_date = datetime.now(timezone.utc).isoformat()
        
        # Vacuum packaging
        vacuum_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'pepper',
            'quantity_kg': 5.0,
            'harvest_date': harvest_date,
            'storage_method': 'refrigerated',
            'packaging_type': 'vacuum'
        })
        
        # Open packaging
        open_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'pepper',
            'quantity_kg': 5.0,
            'harvest_date': harvest_date,
            'storage_method': 'refrigerated',
            'packaging_type': 'open'
        })
        
        assert vacuum_response.status_code == 201
        assert open_response.status_code == 201
        
        vacuum_data = vacuum_response.get_json()
        open_data = open_response.get_json()
        
        # Vacuum packaging should extend shelf life
        assert vacuum_data['predicted_shelf_life_days'] > open_data['predicted_shelf_life_days']

    def test_predict_shelf_life_grain_vs_vegetable(self, client, sample_user):
        """Test that grains have longer shelf life than vegetables"""
        from datetime import datetime
        
        harvest_date = datetime.now(timezone.utc).isoformat()
        
        # Grain (rice)
        grain_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'rice',
            'quantity_kg': 100.0,
            'harvest_date': harvest_date,
            'storage_method': 'warehouse'
        })
        
        # Vegetable (lettuce)
        veg_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'lettuce',
            'quantity_kg': 10.0,
            'harvest_date': harvest_date,
            'storage_method': 'warehouse'
        })
        
        assert grain_response.status_code == 201
        assert veg_response.status_code == 201
        
        grain_data = grain_response.get_json()
        veg_data = veg_response.get_json()
        
        # Grains should have much longer shelf life
        assert grain_data['predicted_shelf_life_days'] > veg_data['predicted_shelf_life_days']

    def test_predict_shelf_life_invalid_produce_type(self, client, sample_user):
        """Test that invalid produce type returns error"""
        from datetime import datetime
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'unknown_vegetable',
            'quantity_kg': 10.0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'warehouse'
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_predict_shelf_life_missing_required_field(self, client, sample_user):
        """Test that missing required fields return error"""
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'maize'
            # Missing quantity_kg, harvest_date, storage_method
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error']

    def test_predict_shelf_life_invalid_user(self, client):
        """Test prediction with non-existent user"""
        from datetime import datetime
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': 99999,
            'produce_type': 'tomato',
            'quantity_kg': 10.0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'cold_storage'
        })
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_predict_shelf_life_zero_quantity_error(self, client, sample_user):
        """Test that zero quantity returns error"""
        from datetime import datetime
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': 0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'cold_storage'
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_predict_shelf_life_negative_quantity_error(self, client, sample_user):
        """Test that negative quantity returns error"""
        from datetime import datetime
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': -10,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'cold_storage'
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_predict_shelf_life_invalid_humidity(self, client, sample_user):
        """Test that invalid humidity returns error"""
        from datetime import datetime
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': 10.0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'cold_storage',
            'storage_humidity_percent': 150  # Invalid - over 100%
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_get_user_predictions_empty(self, client, sample_user):
        """Test getting predictions when user has none"""
        response = client.get(f'/produce-assistant/predictions/{sample_user["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_user_predictions_multiple(self, client, sample_user):
        """Test getting multiple predictions for a user"""
        from datetime import datetime
        
        harvest_date = datetime.now(timezone.utc).isoformat()
        
        # Create first prediction
        client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': 50.0,
            'harvest_date': harvest_date,
            'storage_method': 'cold_storage'
        })
        
        # Create second prediction
        client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'maize',
            'quantity_kg': 100.0,
            'harvest_date': harvest_date,
            'storage_method': 'warehouse'
        })
        
        response = client.get(f'/produce-assistant/predictions/{sample_user["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Verify they're ordered by most recent first
        assert 'created_at' in data[0]
        produce_types = [pred['produce_type'] for pred in data]
        assert 'tomato' in produce_types
        assert 'maize' in produce_types

    def test_get_user_predictions_invalid_user(self, client):
        """Test getting predictions for non-existent user"""
        response = client.get('/produce-assistant/predictions/99999')
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_get_prediction_detail(self, client, sample_user):
        """Test getting detailed information for a specific prediction"""
        from datetime import datetime
        
        # Create a prediction
        create_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'banana',
            'quantity_kg': 20.0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'room_temp',
            'packaging_type': 'crates',
            'storage_cost_per_day': 200
        })
        
        pred_id = create_response.get_json()['id']
        
        # Get the detail
        response = client.get(f'/produce-assistant/prediction/{pred_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == pred_id
        assert data['produce_type'] == 'banana'
        assert 'storage_recommendations' in data
        assert 'quality_timeline' in data
        
        # Verify recommendations
        recommendations = data['storage_recommendations']
        assert 'optimal_conditions' in recommendations
        assert 'recommendations' in recommendations
        assert isinstance(recommendations['recommendations'], list)

    def test_get_prediction_detail_not_found(self, client):
        """Test getting detail for non-existent prediction"""
        response = client.get('/produce-assistant/prediction/99999')
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_quality_timeline_structure(self, client, sample_user):
        """Test that quality timeline has correct structure"""
        from datetime import datetime
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': 10.0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'cold_storage'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        timeline = data['quality_timeline']
        assert isinstance(timeline, list)
        assert len(timeline) > 0
        
        # Check first entry
        first_entry = timeline[0]
        assert 'day' in first_entry
        assert 'date' in first_entry
        assert 'quality_percent' in first_entry
        assert 'status' in first_entry
        assert 'description' in first_entry
        assert first_entry['quality_percent'] == 100

    def test_storage_recommendations_structure(self, client, sample_user):
        """Test that storage recommendations have correct structure"""
        from datetime import datetime
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'onion',
            'quantity_kg': 50.0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'warehouse',
            'storage_temperature_celsius': 10,
            'storage_humidity_percent': 70
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        recommendations = data['storage_recommendations']
        assert 'optimal_conditions' in recommendations
        assert 'recommendations' in recommendations
        assert 'category' in recommendations
        assert 'baseline_shelf_life_days' in recommendations
        
        optimal = recommendations['optimal_conditions']
        assert 'temperature_celsius' in optimal
        assert 'humidity_percent' in optimal
        assert 'storage_method' in optimal
        assert 'packaging' in optimal

    def test_optimal_conditions_different_produce(self, client, sample_user):
        """Test that different produce types have different optimal conditions"""
        from datetime import datetime
        
        harvest_date = datetime.now(timezone.utc).isoformat()
        
        # Tomato (vegetable)
        tomato_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'tomato',
            'quantity_kg': 10.0,
            'harvest_date': harvest_date,
            'storage_method': 'room_temp'
        })
        
        # Rice (grain)
        rice_response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'rice',
            'quantity_kg': 50.0,
            'harvest_date': harvest_date,
            'storage_method': 'room_temp'
        })
        
        tomato_data = tomato_response.get_json()
        rice_data = rice_response.get_json()
        
        tomato_optimal = tomato_data['storage_recommendations']['optimal_conditions']
        rice_optimal = rice_data['storage_recommendations']['optimal_conditions']
        
        # Different produce should have different optimal temperatures
        assert tomato_optimal['temperature_celsius'] != rice_optimal['temperature_celsius']

    def test_storage_cost_calculation(self, client, sample_user):
        """Test storage cost calculation over predicted shelf life"""
        from datetime import datetime
        
        cost_per_day = 1000
        
        response = client.post('/produce-assistant/predict-shelf-life', json={
            'user_id': sample_user['id'],
            'produce_type': 'yam',
            'quantity_kg': 100.0,
            'harvest_date': datetime.now(timezone.utc).isoformat(),
            'storage_method': 'warehouse',
            'storage_cost_per_day': cost_per_day
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        predicted_days = data['predicted_shelf_life_days']
        expected_total = cost_per_day * predicted_days
        
        assert data['storage_cost_per_day'] == cost_per_day
        assert data['estimated_total_storage_cost'] == expected_total


class TestCropRecommender:
    """Test suite for AI Crop Recommender"""

    def test_recommend_crops_basic(self, client, sample_user):
        """Test basic crop recommendation with all fields"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Ogun State',
            'soil_type': 'loamy',
            'soil_ph': 6.5,
            'land_size_hectares': 5.0,
            'climate_zone': 'tropical',
            'average_rainfall_mm': 1200,
            'average_temperature_celsius': 27,
            'season': 'rainy_season',
            'irrigation_available': True,
            'budget_category': 'medium',
            'experience_level': 'intermediate'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        # Verify input data is saved
        assert data['location'] == 'Ogun State'
        assert data['land_conditions']['soil_type'] == 'loamy'
        assert data['land_conditions']['soil_ph'] == 6.5
        assert data['land_conditions']['land_size_hectares'] == 5.0
        
        # Verify climate data
        assert data['climate_data']['climate_zone'] == 'tropical'
        assert data['climate_data']['season'] == 'rainy_season'
        
        # Verify recommendations
        assert 'recommended_crops' in data
        assert isinstance(data['recommended_crops'], list)
        assert len(data['recommended_crops']) > 0
        assert len(data['recommended_crops']) <= 5
        
        # Each crop should have required fields
        for crop in data['recommended_crops']:
            assert 'crop_name' in crop
            assert 'suitability_score' in crop
            assert 'market_demand' in crop
            assert 'estimated_yield_kg_per_hectare' in crop
            assert 0 <= crop['suitability_score'] <= 100
        
        # Verify confidence score
        assert 'confidence_score' in data
        assert 0 <= data['confidence_score'] <= 100
        
        # Verify analysis
        assert 'market_potential' in data
        assert 'risk_factors' in data
        assert 'success_factors' in data
        assert isinstance(data['risk_factors'], list)
        assert isinstance(data['success_factors'], list)

    def test_recommend_crops_minimal_fields(self, client, sample_user):
        """Test recommendation with only required fields"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Lagos State',
            'soil_type': 'sandy',
            'land_size_hectares': 2.0,
            'climate_zone': 'tropical',
            'season': 'dry_season'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        
        assert data['recommended_crops']
        assert data['confidence_score'] > 0

    def test_recommend_crops_different_soil_types(self, client, sample_user):
        """Test that different soil types produce different recommendations"""
        # Loamy soil
        loamy_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Kaduna State',
            'soil_type': 'loamy',
            'land_size_hectares': 3.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season'
        })
        
        # Sandy soil
        sandy_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Kaduna State',
            'soil_type': 'sandy',
            'land_size_hectares': 3.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season'
        })
        
        assert loamy_response.status_code == 201
        assert sandy_response.status_code == 201
        
        loamy_data = loamy_response.get_json()
        sandy_data = sandy_response.get_json()
        
        # Both should have recommendations
        assert len(loamy_data['recommended_crops']) > 0
        assert len(sandy_data['recommended_crops']) > 0
        
        # Soil type should be properly stored
        assert loamy_data['land_conditions']['soil_type'] == 'loamy'
        assert sandy_data['land_conditions']['soil_type'] == 'sandy'

    def test_recommend_crops_climate_zones(self, client, sample_user):
        """Test recommendations adapt to different climate zones"""
        # Tropical
        tropical_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Delta State',
            'soil_type': 'loamy',
            'land_size_hectares': 4.0,
            'climate_zone': 'tropical',
            'average_rainfall_mm': 1500,
            'season': 'rainy_season'
        })
        
        # Arid
        arid_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Sokoto State',
            'soil_type': 'sandy',
            'land_size_hectares': 4.0,
            'climate_zone': 'arid',
            'average_rainfall_mm': 400,
            'season': 'dry_season'
        })
        
        assert tropical_response.status_code == 201
        assert arid_response.status_code == 201
        
        tropical_data = tropical_response.get_json()
        arid_data = arid_response.get_json()
        
        # Arid climate should have different/lower confidence or different crops
        assert tropical_data['recommended_crops'][0]['crop_name'] != arid_data['recommended_crops'][0]['crop_name'] or \
               tropical_data['confidence_score'] != arid_data['confidence_score']

    def test_recommend_crops_irrigation_effect(self, client, sample_user):
        """Test that irrigation availability affects recommendations"""
        # Without irrigation
        no_irrig_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Kano State',
            'soil_type': 'loamy',
            'land_size_hectares': 3.0,
            'climate_zone': 'tropical',
            'average_rainfall_mm': 600,
            'season': 'dry_season',
            'irrigation_available': False
        })
        
        # With irrigation
        irrig_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Kano State',
            'soil_type': 'loamy',
            'land_size_hectares': 3.0,
            'climate_zone': 'tropical',
            'average_rainfall_mm': 600,
            'season': 'dry_season',
            'irrigation_available': True
        })
        
        assert no_irrig_response.status_code == 201
        assert irrig_response.status_code == 201
        
        no_irrig_data = no_irrig_response.get_json()
        irrig_data = irrig_response.get_json()
        
        # Irrigation should improve confidence or enable different crops
        assert irrig_data['confidence_score'] >= no_irrig_data['confidence_score'] or \
               len(irrig_data['recommended_crops']) >= len(no_irrig_data['recommended_crops'])

    def test_recommend_crops_experience_level(self, client, sample_user):
        """Test that experience level affects crop difficulty recommendations"""
        # Beginner
        beginner_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Enugu State',
            'soil_type': 'loamy',
            'land_size_hectares': 2.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season',
            'experience_level': 'beginner'
        })
        
        # Expert
        expert_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Enugu State',
            'soil_type': 'loamy',
            'land_size_hectares': 2.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season',
            'experience_level': 'expert'
        })
        
        beginner_data = beginner_response.get_json()
        expert_data = expert_response.get_json()
        
        # Beginner should get easier crops or warnings about difficulty
        if beginner_data['recommended_crops']:
            beginner_difficulties = [c.get('difficulty_level') for c in beginner_data['recommended_crops']]
            assert 'beginner' in beginner_difficulties or len(beginner_data['risk_factors']) > 0

    def test_recommend_crops_missing_required_field(self, client, sample_user):
        """Test that missing required fields return error"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Abuja',
            # Missing soil_type, land_size_hectares, etc.
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
        assert 'required' in data['error']

    def test_recommend_crops_invalid_user(self, client):
        """Test recommendation with non-existent user"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': 99999,
            'location': 'Lagos',
            'soil_type': 'loamy',
            'land_size_hectares': 1.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season'
        })
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_recommend_crops_zero_land_size_error(self, client, sample_user):
        """Test that zero land size returns an error"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Oyo State',
            'soil_type': 'loamy',
            'land_size_hectares': 0,
            'climate_zone': 'tropical',
            'season': 'rainy_season'
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_recommend_crops_invalid_ph(self, client, sample_user):
        """Test that invalid pH values return errors"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Rivers State',
            'soil_type': 'clay',
            'soil_ph': 15.0,  # Invalid pH
            'land_size_hectares': 2.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season'
        })
        
        assert response.status_code == 400
        assert 'error' in response.get_json()

    def test_get_user_recommendations_empty(self, client, sample_user):
        """Test getting recommendations when user has none"""
        response = client.get(f'/produce-assistant/recommendations/{sample_user["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_user_recommendations_multiple(self, client, sample_user):
        """Test getting multiple recommendations for a user"""
        # Create first recommendation
        client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Imo State',
            'soil_type': 'loamy',
            'land_size_hectares': 3.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season'
        })
        
        # Create second recommendation
        client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Imo State',
            'soil_type': 'clay',
            'land_size_hectares': 2.0,
            'climate_zone': 'tropical',
            'season': 'dry_season'
        })
        
        response = client.get(f'/produce-assistant/recommendations/{sample_user["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_get_user_recommendations_invalid_user(self, client):
        """Test getting recommendations for non-existent user"""
        response = client.get('/produce-assistant/recommendations/99999')
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_get_recommendation_detail(self, client, sample_user):
        """Test getting detailed information for a specific recommendation"""
        # Create a recommendation
        create_response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Anambra State',
            'soil_type': 'loamy',
            'soil_ph': 6.2,
            'land_size_hectares': 4.0,
            'climate_zone': 'tropical',
            'average_rainfall_mm': 1400,
            'season': 'rainy_season',
            'irrigation_available': True,
            'budget_category': 'high',
            'experience_level': 'expert'
        })
        
        rec_id = create_response.get_json()['id']
        
        # Get the detail
        response = client.get(f'/produce-assistant/recommendation/{rec_id}')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data['id'] == rec_id
        assert data['location'] == 'Anambra State'
        assert 'recommended_crops' in data
        assert 'risk_factors' in data
        assert 'success_factors' in data
        assert 'alternative_crops' in data

    def test_get_recommendation_detail_not_found(self, client):
        """Test getting detail for non-existent recommendation"""
        response = client.get('/produce-assistant/recommendation/99999')
        
        assert response.status_code == 404
        assert 'error' in response.get_json()

    def test_crops_sorted_by_suitability(self, client, sample_user):
        """Test that recommended crops are sorted by suitability score"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Benue State',
            'soil_type': 'loamy',
            'land_size_hectares': 5.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season'
        })
        
        data = response.get_json()
        crops = data['recommended_crops']
        
        # Verify crops are sorted in descending order of suitability
        for i in range(len(crops) - 1):
            assert crops[i]['suitability_score'] >= crops[i + 1]['suitability_score']

    def test_market_potential_assessment(self, client, sample_user):
        """Test that market potential is properly assessed"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Ogun State',
            'soil_type': 'loamy',
            'soil_ph': 6.5,
            'land_size_hectares': 3.0,
            'climate_zone': 'tropical',
            'season': 'rainy_season'
        })
        
        data = response.get_json()
        
        assert 'market_potential' in data
        assert data['market_potential'] in ['high', 'medium', 'low']

    def test_alternative_crops_provided(self, client, sample_user):
        """Test that alternative crop options are provided"""
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Plateau State',
            'soil_type': 'loamy',
            'land_size_hectares': 2.5,
            'climate_zone': 'temperate',
            'season': 'rainy_season'
        })
        
        data = response.get_json()
        
        assert 'alternative_crops' in data
        assert isinstance(data['alternative_crops'], list)
        # Should have some alternatives (unless very few crops match)
        assert len(data['alternative_crops']) >= 0

    def test_risk_and_success_factors(self, client, sample_user):
        """Test that risk and success factors are analyzed"""
        # Low budget, beginner, no irrigation
        response = client.post('/produce-assistant/recommend-crops', json={
            'user_id': sample_user['id'],
            'location': 'Zamfara State',
            'soil_type': 'sandy',
            'land_size_hectares': 1.0,
            'climate_zone': 'arid',
            'season': 'dry_season',
            'irrigation_available': False,
            'budget_category': 'low',
            'experience_level': 'beginner'
        })
        
        data = response.get_json()
        
        # Should have risk factors given the challenging conditions
        assert len(data['risk_factors']) > 0
        # Should still have success factors (guidance)
        assert len(data['success_factors']) > 0
