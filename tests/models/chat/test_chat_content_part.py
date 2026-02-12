import pytest
from pydantic import ValidationError
from src.llama.models.chat.chat_content_part import ChatContentPart, ContentType
from src.llama.models.chat.content_type import ContentType
from src.llama.models.chat.image_url import ImageUrl
from src.llama.models.chat.image_detail import ImageDetail


class TestChatContentPart:
    def test_valid_text_content_part_creation(self):
        """验证有效的文本ContentPart创建"""
        data = {
            "type": ContentType.TEXT,
            "text": "Hello, world!"
        }
        content_part = ChatContentPart(**data)

        assert content_part.type == ContentType.TEXT
        assert content_part.text == "Hello, world!"
        assert content_part.image_url is None

    def test_valid_image_content_part_creation(self):
        """验证有效的图像ContentPart创建"""
        image_url_data = {
            "url": "https://example.com/image.jpg",
            "detail": ImageDetail.AUTO
        }
        image_url = ImageUrl(**image_url_data)

        data = {
            "type": ContentType.IMAGE_URL,
            "image_url": image_url
        }
        content_part = ChatContentPart(**data)

        assert content_part.type == ContentType.IMAGE_URL
        assert content_part.image_url is not None
        assert content_part.image_url.url == "https://example.com/image.jpg"
        assert content_part.image_url.detail == ImageDetail.AUTO
        assert content_part.text is None

    def test_optional_fields_handling(self):
        """验证可选字段为默认值的情况"""
        data = {
            "type": ContentType.TEXT,
            "text": "Hello"
        }
        content_part = ChatContentPart(**data)

        assert content_part.type == ContentType.TEXT
        assert content_part.text == "Hello"
        assert content_part.image_url is None

    def test_extra_field_rejection(self):
        """验证额外字段被拒绝"""
        data = {
            "type": ContentType.TEXT,
            "text": "Hello",
            "invalid_field": "should_fail"
        }

        with pytest.raises(ValidationError):
            ChatContentPart(**data)

    def test_json_serialization(self):
        """验证JSON序列化/反序列化"""
        data = {
            "type": ContentType.TEXT,
            "text": "Hello, world!"
        }
        original = ChatContentPart(**data)
        json_str = original.model_dump_json()
        restored = ChatContentPart.model_validate_json(json_str)

        assert original.type == restored.type
        assert original.text == restored.text

    def test_boundary_conditions(self):
        """验证边界条件"""
        # 测试最小长度文本
        data = {
            "type": ContentType.TEXT,
            "text": "a"
        }
        content_part = ChatContentPart(**data)
        assert content_part.text == "a"

        # 测试长文本
        long_text = "a" * 1000
        data["text"] = long_text
        content_part = ChatContentPart(**data)
        assert content_part.text == long_text

        # 测试不同类型
        for content_type in [ContentType.TEXT, ContentType.IMAGE_URL]:
            if content_type == ContentType.TEXT:
                data = {"type": content_type, "text": "test"}
            else:
                image_url_data = {"url": "https://example.com/img.jpg", "detail": ImageDetail.AUTO}
                image_url = ImageUrl(**image_url_data)
                data = {"type": content_type, "image_url": image_url}

            content_part = ChatContentPart(**data)
            assert content_part.type == content_type