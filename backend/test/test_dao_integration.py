import pytest
import os
from pymongo.errors import WriteError

from src.util.dao import DAO


@pytest.mark.integration
class TestDAOCreateIntegration:
    @pytest.fixture(scope="function")
    def test_db_url(self):
        # Use environment variable or default to localhost with test database
        return os.environ.get('MONGO_URL', 'mongodb://localhost:27017')

    @pytest.fixture(scope="function")
    def user_dao(self, test_db_url, monkeypatch):
        # Set environment to use test database
        monkeypatch.setenv('MONGO_URL', test_db_url)
        
        # Change to backend directory for validator loading
        import os as os_module
        original_dir = os_module.getcwd()
        backend_dir = os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__)))
        os_module.chdir(backend_dir)
        
        dao = DAO(collection_name='user')
        
        # Clean up collection before test - drop existing data
        dao.drop()
        
        # Recreate collection with validator
        dao = DAO(collection_name='user')
        
        yield dao
        
        # Clean up after test
        dao.drop()
        os_module.chdir(original_dir)

    @pytest.fixture(scope="function")
    def todo_dao(self, test_db_url, monkeypatch):
        monkeypatch.setenv('MONGO_URL', test_db_url)
        
        import os as os_module
        original_dir = os_module.getcwd()
        backend_dir = os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__)))
        os_module.chdir(backend_dir)
        
        dao = DAO(collection_name='todo')
        dao.drop()
        dao = DAO(collection_name='todo')
        
        yield dao
        
        dao.drop()
        os_module.chdir(original_dir)

    # Test Case 1: Valid user creation
    def test_create_valid_user(self, user_dao):
        user_data = {
            'firstName': 'John',
            'lastName': 'Doe',
            'email': 'john.doe@example.com'
        }
        
        result = user_dao.create(user_data)
        
        assert result is not None
        assert '_id' in result
        assert result['firstName'] == 'John'
        assert result['lastName'] == 'Doe'
        assert result['email'] == 'john.doe@example.com'

    # Test Case 2: Missing required field - firstName
    def test_create_user_missing_firstname(self, user_dao):
        user_data = {
            'lastName': 'Doe',
            'email': 'missing.firstname@example.com'
        }
        
        with pytest.raises(WriteError):
            user_dao.create(user_data)

    # Test Case 3: Missing required field - email
    def test_create_user_missing_email(self, user_dao):
        user_data = {
            'firstName': 'Jane',
            'lastName': 'Smith'
        }
        
        with pytest.raises(WriteError):
            user_dao.create(user_data)

    # Test Case 4: Missing required field - lastName
    def test_create_user_missing_lastname(self, user_dao):
        user_data = {
            'firstName': 'Bob',
            'email': 'missing.lastname@example.com'
        }
        
        with pytest.raises(WriteError):
            user_dao.create(user_data)

    # Test Case 5: Wrong data type - email as integer
    def test_create_user_wrong_email_type(self, user_dao):
        user_data = {
            'firstName': 'Test',
            'lastName': 'User',
            'email': 12345  # Should be string
        }
        
        with pytest.raises(WriteError):
            user_dao.create(user_data)

    # Test Case 6: Wrong data type - firstName as boolean
    def test_create_user_wrong_firstname_type(self, user_dao):
        user_data = {
            'firstName': True,  # Should be string
            'lastName': 'User',
            'email': 'wrong.type@example.com'
        }
        
        with pytest.raises(WriteError):
            user_dao.create(user_data)

    # Test Case 7: Duplicate unique field - email
    def test_create_user_duplicate_email(self, user_dao):
        user_data = {
            'firstName': 'Original',
            'lastName': 'User',
            'email': 'duplicate@example.com'
        }
        
        # Create first user successfully
        result1 = user_dao.create(user_data)
        assert result1 is not None
        
        # Try to create second user with same email
        user_data2 = {
            'firstName': 'Duplicate',
            'lastName': 'Attempt',
            'email': 'duplicate@example.com'
        }
        
        with pytest.raises(WriteError):
            user_dao.create(user_data2)
