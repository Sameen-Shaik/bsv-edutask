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


    # Test Case 8: Valid todo creation
    def test_create_valid_todo(self, todo_dao):
        todo_data = {
            'description': 'Complete assignment 3',
            'done': False
        }
        
        result = todo_dao.create(todo_data)
        
        assert result is not None
        assert '_id' in result
        assert result['description'] == 'Complete assignment 3'
        assert result['done'] == False

    # Test Case 9: Todo without optional done field
    def test_create_todo_without_done(self, todo_dao):
        todo_data = {
            'description': 'Test todo without done status'
        }
        
        result = todo_dao.create(todo_data)
        
        assert result is not None
        assert '_id' in result
        assert result['description'] == 'Test todo without done status'

    # Test Case 10: Missing required todo field - description
    def test_create_todo_missing_description(self, todo_dao):
        todo_data = {
            'done': True
        }
        
        with pytest.raises(WriteError):
            todo_dao.create(todo_data)

    # Test Case 11: Wrong data type - description as integer
    def test_create_todo_wrong_description_type(self, todo_dao):
        todo_data = {
            'description': 12345,  # Should be string
            'done': False
        }
        
        with pytest.raises(WriteError):
            todo_dao.create(todo_data)

    # Test Case 12: Wrong data type - done as string
    def test_create_todo_wrong_done_type(self, todo_dao):
        todo_data = {
            'description': 'Test wrong done type',
            'done': 'true'  # Should be boolean
        }
        
        with pytest.raises(WriteError):
            todo_dao.create(todo_data)

    # Test Case 13: Duplicate unique todo description
    def test_create_todo_duplicate_description(self, todo_dao):
        todo_data = {
            'description': 'Unique todo description',
            'done': False
        }
        
        # Create first todo successfully
        result1 = todo_dao.create(todo_data)
        assert result1 is not None
        
        # Try to create second todo with same description
        todo_data2 = {
            'description': 'Unique todo description',
            'done': True
        }
        
        with pytest.raises(WriteError):
            todo_dao.create(todo_data2)

    # Test Case 14: User with optional tasks field as array
    def test_create_user_with_tasks_array(self, user_dao):
        user_data = {
            'firstName': 'With',
            'lastName': 'Tasks',
            'email': 'with.tasks@example.com',
            'tasks': []
        }
        
        result = user_dao.create(user_data)
        
        assert result is not None
        assert '_id' in result
        assert result['tasks'] == []

    # Test Case 15: Valid user with extra fields not in validator
    def test_create_user_with_extra_fields(self, user_dao):
        user_data = {
            'firstName': 'Extra',
            'lastName': 'Fields',
            'email': 'extra.fields@example.com',
            'phone': '123-456-7890'  # Not in validator
        }
        
        result = user_dao.create(user_data)
        
        assert result is not None
        assert '_id' in result
        assert result['phone'] == '123-456-7890'
