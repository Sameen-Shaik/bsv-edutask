import pytest
import unittest.mock as mock
from unittest.mock import patch, MagicMock

from src.controllers.usercontroller import UserController


@pytest.mark.unit
class TestGetUserByEmail:
    @pytest.fixture
    def mocked_dao(self):
        return MagicMock()

    @pytest.fixture
    def sut(self, mocked_dao):
        return UserController(dao=mocked_dao)

    # Test Case 1: Invalid email format (missing @)
    def test_invalid_email_missing_at(self, sut):
        with pytest.raises(ValueError, match="Error: invalid email address"):
            sut.get_user_by_email("invalidemail.com")

    # Test Case 2: Invalid email format (empty string)
    def test_invalid_email_empty(self, sut):
        with pytest.raises(ValueError, match="Error: invalid email address"):
            sut.get_user_by_email("")

    # Test Case 3: No user found with valid email
    def test_no_user_found(self, sut, mocked_dao):
        mocked_dao.find.return_value = []
        
        result = sut.get_user_by_email("notfound@example.com")
        
        assert result is None
        mocked_dao.find.assert_called_once_with({'email': 'notfound@example.com'})

    # Test Case 4: Single user found (happy path)
    def test_single_user_found(self, sut, mocked_dao):
        expected_user = {
            '_id': {'$oid': '123456789012345678901234'},
            'email': 'user@example.com',
            'firstName': 'John',
            'lastName': 'Doe'
        }
        mocked_dao.find.return_value = [expected_user]
        
        result = sut.get_user_by_email("user@example.com")
        
        assert result == expected_user
        mocked_dao.find.assert_called_once_with({'email': 'user@example.com'})

 