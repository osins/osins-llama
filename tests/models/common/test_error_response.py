import pytest
from pydantic import ValidationError
from llama.models.common.error_response import ErrorResponse
from llama.models.common.error_model import ErrorModel


class TestErrorResponse:
    def test_valid_error_response_creation(self):
        """验证有效的ErrorResponse创建"""
        data = {
            "message": "An error occurred",
            "type": "invalid_request_error"
        }
        error_response = ErrorResponse(**data)

        assert error_response.message == "An error occurred"
        assert error_response.type == "invalid_request_error"
        assert error_response.param is None
        assert error_response.code is None

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "message": "Error message",
            "type": "error_type",
            "param": "test_param",
            "code": "test_code"
        }
        error_response = ErrorResponse(**data)

        assert error_response.message == "Error message"
        assert error_response.type == "error_type"
        assert error_response.param == "test_param"
        assert error_response.code == "test_code"

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "message": "Error message",
            "type": "error_type",
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ErrorResponse(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "message": "Serialization test error",
            "type": "serialization_error",
            "param": "test_param",
            "code": "test_code"
        }
        original = ErrorResponse(**data)
        json_str = original.model_dump_json()
        restored = ErrorResponse.model_validate_json(json_str)

        assert original.message == restored.message
        assert original.type == restored.type
        assert original.param == restored.param
        assert original.code == restored.code

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试最小长度消息
        data = {
            "message": "a",
            "type": "error_type"
        }
        error_response = ErrorResponse(**data)
        assert error_response.message == "a"

        # 测试长消息
        long_message = "a" * 1000
        data = {
            "message": long_message,
            "type": "long_message_error"
        }
        error_response = ErrorResponse(**data)
        assert error_response.message == long_message

        # 测试各种类型的消息
        for error_type in ["invalid_request_error", "authentication_error", "rate_limit_exceeded"]:
            data = {
                "message": "Test error",
                "type": error_type
            }
            error_response = ErrorResponse(**data)
            assert error_response.type == error_type


class TestErrorModel:
    def test_valid_error_model_creation(self):
        """验证有效的ErrorModel创建"""
        error_data = {
            "message": "An error occurred",
            "type": "invalid_request_error"
        }
        error_response = ErrorResponse(**error_data)

        data = {
            "error": error_response
        }
        error_model = ErrorModel(**data)

        assert error_model.error.message == "An error occurred"
        assert error_model.error.type == "invalid_request_error"

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        error_data = {
            "message": "Error message",
            "type": "error_type",
            "param": "test_param",
            "code": "test_code"
        }
        error_response = ErrorResponse(**error_data)

        data = {
            "error": error_response
        }
        error_model = ErrorModel(**data)

        assert error_model.error.param == "test_param"
        assert error_model.error.code == "test_code"

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        error_data = {
            "message": "Error message",
            "type": "error_type"
        }
        error_response = ErrorResponse(**error_data)

        data = {
            "error": error_response,
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ErrorModel(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        error_data = {
            "message": "Serialization test error",
            "type": "serialization_error",
            "param": "test_param",
            "code": "test_code"
        }
        error_response = ErrorResponse(**error_data)

        data = {
            "error": error_response
        }
        original = ErrorModel(**data)
        json_str = original.model_dump_json()
        restored = ErrorModel.model_validate_json(json_str)

        assert original.error.message == restored.error.message
        assert original.error.type == restored.error.type
        assert original.error.param == restored.error.param
        assert original.error.code == restored.error.code

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试长错误消息
        long_message = "a" * 1000
        error_data = {
            "message": long_message,
            "type": "long_error_message"
        }
        error_response = ErrorResponse(**error_data)

        data = {
            "error": error_response
        }
        error_model = ErrorModel(**data)
        assert error_model.error.message == long_message

        # 测试最小长度错误消息
        min_error_data = {
            "message": "a",
            "type": "min_message_error"
        }
        error_response = ErrorResponse(**min_error_data)

        data = {
            "error": error_response
        }
        error_model = ErrorModel(**data)
        assert error_model.error.message == "a"