"""
Tests for marketplace/listing functionality
"""
import pytest


def test_create_listing(client):
    """Test creating a marketplace listing"""
    # Create a realtor
    realtor_data = {
        "full_name": "Alice Realtor",
        "email": "alice.listing@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    
    r = client.post('/register', json=realtor_data)
    realtor_id = r.get_json()['id']
    
    # Create a land listing
    listing_data = {
        "owner_id": realtor_id,
        "listing_type": "land_sale",
        "title": "10 Hectares Farmland in Ogun State",
        "description": "Fertile farmland suitable for crops",
        "location_state": "Ogun",
        "location_area": "Ijebu-Ode",
        "size_value": 10,
        "size_unit": "hectares",
        "price": 5000000.0,  # 5,000,000 NGN
        "price_type": "sale",
        "images": ["image1.jpg", "image2.jpg"]
    }
    
    r = client.post('/listings/create', json=listing_data)
    assert r.status_code == 201
    
    data = r.get_json()
    assert data['title'] == "10 Hectares Farmland in Ogun State"
    assert data['owner_id'] == realtor_id
    assert data['listing_type'] == 'land_sale'
    assert data['status'] == 'active'
    assert data['price'] == 5000000.0
    assert data['images'] == ["image1.jpg", "image2.jpg"]
    assert 'id' in data
    assert 'created_at' in data


def test_create_listing_missing_fields(client):
    """Test creating a listing with missing required fields"""
    incomplete_data = {
        "owner_id": 1,
        "title": "Test Listing"
        # Missing listing_type and price
    }
    
    r = client.post('/listings/create', json=incomplete_data)
    assert r.status_code == 400
    assert 'missing required fields' in r.get_json()['error']


def test_create_listing_invalid_type(client):
    """Test creating a listing with invalid listing_type"""
    # Create a user first
    user_data = {
        "full_name": "Bob User",
        "email": "bob.listing@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    listing_data = {
        "owner_id": user_id,
        "listing_type": "invalid_type",
        "title": "Test",
        "price": 10000.0
    }
    
    r = client.post('/listings/create', json=listing_data)
    assert r.status_code == 400
    assert 'Invalid listing_type' in r.get_json()['error']


def test_get_all_listings(client):
    """Test retrieving all listings"""
    # Create a user
    user_data = {
        "full_name": "Charlie Farmer",
        "email": "charlie.listing@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    # Create multiple listings
    listings = [
        {
            "owner_id": user_id,
            "listing_type": "land_sale",
            "title": "Land 1",
            "price": 1000000
        },
        {
            "owner_id": user_id,
            "listing_type": "land_rent",
            "title": "Land for Rent",
            "price": 2000000
        }
    ]
    
    for listing in listings:
        client.post('/listings/create', json=listing)
    
    # Get all listings
    r = client.get('/listings')
    assert r.status_code == 200
    
    data = r.get_json()
    assert len(data) >= 2
    assert any(l['title'] == 'Land 1' for l in data)
    assert any(l['title'] == 'Land for Rent' for l in data)


def test_get_listings_with_filters(client):
    """Test retrieving listings with filters"""
    # Create a user
    user_data = {
        "full_name": "Diana Realtor",
        "email": "diana.listing@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    # Create listings in different states
    listing1 = {
        "owner_id": user_id,
        "listing_type": "land_sale",
        "title": "Lagos Land",
        "location_state": "Lagos",
        "price": 10000000
    }
    listing2 = {
        "owner_id": user_id,
        "listing_type": "land_sale",
        "title": "Ogun Land",
        "location_state": "Ogun",
        "price": 5000000
    }
    
    client.post('/listings/create', json=listing1)
    client.post('/listings/create', json=listing2)
    
    # Filter by state
    r = client.get('/listings?location_state=Ogun')
    assert r.status_code == 200
    
    data = r.get_json()
    assert all(l['location_state'] == 'Ogun' for l in data if l['location_state'])


def test_get_listings_price_range_filter(client):
    """Test filtering listings by price range"""
    # Create a user
    user_data = {
        "full_name": "Eve Farmer",
        "email": "eve.listing@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    # Create listings with different prices
    prices = [1000000, 5000000, 10000000]
    for i, price in enumerate(prices):
        listing = {
            "owner_id": user_id,
            "listing_type": "land_sale",
            "title": f"Land {i}",
            "price": price
        }
        client.post('/listings/create', json=listing)
    
    # Filter by price range
    r = client.get('/listings?min_price=2000000&max_price=7000000')
    assert r.status_code == 200
    
    data = r.get_json()
    for listing in data:
        if listing['title'].startswith('Land'):
            assert 2000000 <= listing['price'] <= 7000000


def test_get_single_listing(client):
    """Test retrieving a single listing by ID"""
    # Create a user and listing
    user_data = {
        "full_name": "Frank Realtor",
        "email": "frank.listing@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    listing_data = {
        "owner_id": user_id,
        "listing_type": "land_sale",
        "title": "Premium Land",
        "price": 20000000
    }
    
    r = client.post('/listings/create', json=listing_data)
    listing_id = r.get_json()['id']
    initial_views = r.get_json()['views']
    
    # Get the listing
    r = client.get(f'/listings/{listing_id}')
    assert r.status_code == 200
    
    data = r.get_json()
    assert data['id'] == listing_id
    assert data['title'] == 'Premium Land'
    assert data['views'] == initial_views + 1  # Views incremented


def test_get_nonexistent_listing(client):
    """Test retrieving a nonexistent listing"""
    r = client.get('/listings/9999')
    assert r.status_code == 404
    assert 'not found' in r.get_json()['error']


def test_update_listing(client):
    """Test updating a listing"""
    # Create a user and listing
    user_data = {
        "full_name": "George Farmer",
        "email": "george.listing@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    listing_data = {
        "owner_id": user_id,
        "listing_type": "land_rent",
        "title": "Old Tractor",
        "price": 3000000
    }
    
    r = client.post('/listings/create', json=listing_data)
    listing_id = r.get_json()['id']
    
    # Update the listing
    update_data = {
        "user_id": user_id,
        "title": "New Tractor",
        "price": 3500000,
        "description": "Updated description"
    }
    
    r = client.put(f'/listings/{listing_id}', json=update_data)
    assert r.status_code == 200
    
    data = r.get_json()
    assert data['title'] == 'New Tractor'
    assert data['price'] == 3500000
    assert data['description'] == 'Updated description'


def test_update_listing_unauthorized(client):
    """Test that non-owners cannot update a listing"""
    # Create two users
    user1_data = {
        "full_name": "Helen User1",
        "email": "helen.listing@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    user2_data = {
        "full_name": "Ivan User2",
        "email": "ivan.listing@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    
    r1 = client.post('/register', json=user1_data)
    r2 = client.post('/register', json=user2_data)
    
    user1_id = r1.get_json()['id']
    user2_id = r2.get_json()['id']
    
    # User1 creates a listing
    listing_data = {
        "owner_id": user1_id,
        "listing_type": "land_sale",
        "title": "User1's Land",
        "price": 5000000
    }
    
    r = client.post('/listings/create', json=listing_data)
    listing_id = r.get_json()['id']
    
    # User2 tries to update User1's listing
    update_data = {
        "user_id": user2_id,
        "title": "Hacked Title"
    }
    
    r = client.put(f'/listings/{listing_id}', json=update_data)
    assert r.status_code == 403
    assert 'unauthorized' in r.get_json()['error']


def test_delete_listing(client):
    """Test deleting a listing"""
    # Create a user and listing
    user_data = {
        "full_name": "Jane Realtor",
        "email": "jane.listing@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    listing_data = {
        "owner_id": user_id,
        "listing_type": "land_sale",
        "title": "Temporary Land",
        "price": 2000000
    }
    
    r = client.post('/listings/create', json=listing_data)
    listing_id = r.get_json()['id']
    
    # Delete the listing
    r = client.delete(f'/listings/{listing_id}', json={"user_id": user_id})
    assert r.status_code == 200
    assert 'deleted successfully' in r.get_json()['message']
    
    # Verify it's deleted
    r = client.get(f'/listings/{listing_id}')
    assert r.status_code == 404


def test_delete_listing_unauthorized(client):
    """Test that non-owners cannot delete a listing"""
    # Create two users
    owner_data = {
        "full_name": "Karl Owner",
        "email": "karl.listing@test.com",
        "password": "Pass123",
        "account_type": "realtor"
    }
    other_data = {
        "full_name": "Linda Other",
        "email": "linda.listing@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    
    r1 = client.post('/register', json=owner_data)
    r2 = client.post('/register', json=other_data)
    
    owner_id = r1.get_json()['id']
    other_id = r2.get_json()['id']
    
    # Owner creates a listing
    listing_data = {
        "owner_id": owner_id,
        "listing_type": "land_sale",
        "title": "Protected Land",
        "price": 8000000
    }
    
    r = client.post('/listings/create', json=listing_data)
    listing_id = r.get_json()['id']
    
    # Other user tries to delete
    r = client.delete(f'/listings/{listing_id}', json={"user_id": other_id})
    assert r.status_code == 403
    assert 'unauthorized' in r.get_json()['error']


def test_get_user_listings(client):
    """Test retrieving all listings for a specific user"""
    # Create a user
    user_data = {
        "full_name": "Mike Farmer",
        "email": "mike.listing@test.com",
        "password": "Pass123",
        "account_type": "farmer"
    }
    r = client.post('/register', json=user_data)
    user_id = r.get_json()['id']
    
    # Create multiple listings
    for i in range(3):
        listing = {
            "owner_id": user_id,
            "listing_type": "land_sale",
            "title": f"Land {i}",
            "price": 1000000 * (i + 1)
        }
        client.post('/listings/create', json=listing)
    
    # Get user's listings
    r = client.get(f'/listings/user/{user_id}')
    assert r.status_code == 200
    
    data = r.get_json()
    assert len(data) == 3
    assert all(l['owner_id'] == user_id for l in data)
