"""
验证脚本 - 确认所有数据模型都能正常工作
"""
from src.llama.models.common.usage import Usage
from src.llama.models.common.error_response import ErrorResponse
from src.llama.models.common.error_model import ErrorModel
from src.llama.models.legacy.completion_params import CompletionParams
from src.llama.models.legacy.completion_request import CompletionRequest
from src.llama.models.legacy.completion_choice import CompletionChoice
from src.llama.models.legacy.completion_response import CompletionResponse
from src.llama.models.legacy.completion_finish_reason import CompletionFinishReason
from src.llama.models.legacy.completion_stream_delta import CompletionStreamDelta
from src.llama.models.chat.chat_role import ChatRole
from src.llama.models.chat.chat_content_part import ChatContentPart
from src.llama.models.chat.content_type import ContentType
from src.llama.models.chat.image_url import ImageUrl
from src.llama.models.chat.image_detail import ImageDetail
from src.llama.models.chat.tool_call_function import FunctionCall
from src.llama.models.chat.tool_call import ToolCall
from src.llama.models.chat.chat_message import ChatMessage
from src.llama.models.chat.chat_finish_reason import ChatFinishReason
from src.llama.models.chat.chat_completion_choice import ChatCompletionChoice
from src.llama.models.chat.chat_completion_request import ChatCompletionRequest
from src.llama.models.chat.chat_completion_response import ChatCompletionResponse
from src.llama.models.chat.chat_completion_delta import ChatCompletionDelta
from src.llama.models.chat.chat_completion_chunk import ChatCompletionChunk
from src.llama.models.chat.chat_completion_chunk_choice import ChatCompletionChunkChoice


def test_common_models():
    print("Testing Common Models...")

    # 测试Usage
    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    print(f"Usage: {usage}")
    print(f"Schema Version: {usage.schema_version}")

    # 测试ErrorResponse
    error_resp = ErrorResponse(message="Error occurred", type="test_error")
    error_model = ErrorModel(error=error_resp)
    print(f"ErrorResponse: {error_resp}")
    print(f"ErrorModel: {error_model}")
    print(f"Schema Version: {error_resp.schema_version}")


def test_legacy_models():
    print("\nTesting Legacy Models...")

    # 测试CompletionParams
    params = CompletionParams(model="gpt-3.5-turbo", prompt="Hello")
    print(f"CompletionParams: {params}")
    print(f"Schema Version: {params.schema_version}")

    # 测试CompletionRequest
    request = CompletionRequest(model="gpt-3.5-turbo", prompt="Hello")
    print(f"CompletionRequest: {request}")
    print(f"Schema Version: {request.schema_version}")

    # 测试CompletionChoice
    choice = CompletionChoice(text="Generated text", index=0, finish_reason=CompletionFinishReason.STOP)
    print(f"CompletionChoice: {choice}")
    print(f"Schema Version: {choice.schema_version}")

    # 测试CompletionResponse
    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    response = CompletionResponse(id="test-id", created=1234567890, model="gpt-3.5-turbo", choices=[choice], usage=usage)
    print(f"CompletionResponse: {response}")
    print(f"Schema Version: {response.schema_version}")

    # 测试CompletionStreamDelta
    delta = CompletionStreamDelta(text="Stream text", index=0, finish_reason=CompletionFinishReason.STOP)
    print(f"CompletionStreamDelta: {delta}")


def test_chat_models():
    print("\nTesting Chat Models...")

    # 测试ChatRole枚举
    print(f"ChatRole values: {[role.value for role in ChatRole]}")

    # 测试ChatContentPart
    content_part = ChatContentPart(type=ContentType.TEXT, text="Hello")
    print(f"ChatContentPart: {content_part}")
    print(f"Schema Version: {content_part.schema_version}")

    # 测试ImageUrl
    image_url = ImageUrl(url="https://example.com/image.jpg", detail=ImageDetail.HIGH)
    print(f"ImageUrl: {image_url}")

    # 测试FunctionCall
    func_call = FunctionCall(name="get_weather", arguments='{"location": "Boston"}')
    print(f"FunctionCall: {func_call}")
    print(f"Schema Version: {func_call.schema_version}")

    # 测试ToolCall
    tool_call = ToolCall(id="call_123", function=func_call)
    print(f"ToolCall: {tool_call}")
    print(f"Schema Version: {tool_call.schema_version}")

    # 测试ChatMessage
    message = ChatMessage(role=ChatRole.USER, content="Hello, how are you?")
    print(f"ChatMessage: {message}")
    print(f"Schema Version: {message.schema_version}")

    # 测试ChatFinishReason枚举
    print(f"ChatFinishReason values: {[reason.value for reason in ChatFinishReason]}")

    # 测试ChatCompletionChoice
    choice = ChatCompletionChoice(index=0, message=message, finish_reason=ChatFinishReason.STOP)
    print(f"ChatCompletionChoice: {choice}")
    print(f"Schema Version: {choice.schema_version}")

    # 测试ChatCompletionRequest
    request = ChatCompletionRequest(messages=[message], model="gpt-3.5-turbo")
    print(f"ChatCompletionRequest: {request}")
    print(f"Schema Version: {request.schema_version}")

    # 测试ChatCompletionResponse
    usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    response = ChatCompletionResponse(id="test-id", created=1234567890, model="gpt-3.5-turbo", choices=[choice], usage=usage)
    print(f"ChatCompletionResponse: {response}")
    print(f"Schema Version: {response.schema_version}")

    # 测试ChatCompletionDelta
    delta = ChatCompletionDelta(role=ChatRole.ASSISTANT, content="Hello back!")
    print(f"ChatCompletionDelta: {delta}")

    # 测试ChatCompletionChunk
    chunk_choice = ChatCompletionChunkChoice(index=0, delta=delta)
    chunk = ChatCompletionChunk(id="test-id", created=1234567890, model="gpt-3.5-turbo", choices=[chunk_choice])
    print(f"ChatCompletionChunk: {chunk}")


if __name__ == "__main__":
    print("Validating all data models...")

    test_common_models()
    test_legacy_models()
    test_chat_models()

    print("\nAll models validated successfully!")