import pytest

class TestRatings:
    def test_submit_rating(self, client):
        """Test submitting a rating"""
        # Create rater
        rater = client.post('/register', json={
            'full_name': 'Rater User',
            'email': 'rater@test.com',
            'password': 'password123',
            'account_type': 'farmer'
        }).get_json()

        # Create rated user
        rated = client.post('/register', json={
            'full_name': 'Rated User',
            'email': 'rated@test.com',
            'password': 'password123',
            'account_type': 'worker'
        }).get_json()

        # Submit rating
        response = client.post('/ratings', json={
            'rater_id': rater['id'],
            'rated_user_id': rated['id'],
            'rating_value': 5,
            'comment': 'Great worker!'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['new_average'] == 5.0
        assert data['rating_count'] == 1

        # Verify user profile updated
        response = client.get(f'/ratings/user/{rated["id"]}')
        data = response.get_json()
        assert data['average_rating'] == 5.0
        assert data['rating_count'] == 1
        assert len(data['ratings']) == 1
        assert data['ratings'][0]['rating_value'] == 5
        assert data['ratings'][0]['comment'] == 'Great worker!'

    def test_update_rating(self, client):
        """Test updating an existing rating"""
        # Create users
        rater = client.post('/register', json={
            'full_name': 'Rater 2',
            'email': 'rater2@test.com',
            'password': 'password123',
            'account_type': 'farmer'
        }).get_json()

        rated = client.post('/register', json={
            'full_name': 'Rated 2',
            'email': 'rated2@test.com',
            'password': 'password123',
            'account_type': 'worker'
        }).get_json()

        # Submit initial rating
        client.post('/ratings', json={
            'rater_id': rater['id'],
            'rated_user_id': rated['id'],
            'rating_value': 4,
            'comment': 'Good'
        })

        # Update rating
        response = client.post('/ratings', json={
            'rater_id': rater['id'],
            'rated_user_id': rated['id'],
            'rating_value': 2,
            'comment': 'Changed my mind'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['new_average'] == 2.0
        assert data['rating_count'] == 1

    def test_multiple_ratings(self, client):
        """Test average calculation with multiple ratings"""
        # Create rated user
        rated = client.post('/register', json={
            'full_name': 'Rated 3',
            'email': 'rated3@test.com',
            'password': 'password123',
            'account_type': 'worker'
        }).get_json()

        # Create raters
        rater1 = client.post('/register', json={
            'full_name': 'Rater A',
            'email': 'raterA@test.com',
            'password': 'password123',
            'account_type': 'farmer'
        }).get_json()

        rater2 = client.post('/register', json={
            'full_name': 'Rater B',
            'email': 'raterB@test.com',
            'password': 'password123',
            'account_type': 'farmer'
        }).get_json()

        # Submit ratings
        client.post('/ratings', json={
            'rater_id': rater1['id'],
            'rated_user_id': rated['id'],
            'rating_value': 5
        })

        client.post('/ratings', json={
            'rater_id': rater2['id'],
            'rated_user_id': rated['id'],
            'rating_value': 3
        })

        # Verify average
        response = client.get(f'/ratings/user/{rated["id"]}')
        data = response.get_json()
        assert data['average_rating'] == 4.0 # (5+3)/2
        assert data['rating_count'] == 2

    def test_self_rating_forbidden(self, client):
        """Test that users cannot rate themselves"""
        user = client.post('/register', json={
            'full_name': 'Self Rater',
            'email': 'self@test.com',
            'password': 'password123',
            'account_type': 'farmer'
        }).get_json()

        response = client.post('/ratings', json={
            'rater_id': user['id'],
            'rated_user_id': user['id'],
            'rating_value': 5
        })
        
        assert response.status_code == 400
        assert 'cannot rate yourself' in response.get_json()['error']

    def test_invalid_rating_value(self, client):
        """Test invalid rating values"""
        rater = client.post('/register', json={
            'full_name': 'Rater Inv',
            'email': 'rater_inv@test.com',
            'password': 'password123',
            'account_type': 'farmer'
        }).get_json()

        rated = client.post('/register', json={
            'full_name': 'Rated Inv',
            'email': 'rated_inv@test.com',
            'password': 'password123',
            'account_type': 'worker'
        }).get_json()

        response = client.post('/ratings', json={
            'rater_id': rater['id'],
            'rated_user_id': rated['id'],
            'rating_value': 6
        })
        assert response.status_code == 400

        response = client.post('/ratings', json={
            'rater_id': rater['id'],
            'rated_user_id': rated['id'],
            'rating_value': 0
        })
        assert response.status_code == 400
