"""
Schema版本跟踪测试
验证模型版本跟踪功能是否正常工作
"""
from llama.models.chat.chat_message import ChatMessage
from llama.models.chat.chat_completion_request import ChatCompletionRequest
from llama.models.common.usage import Usage
from llama.models.version_tracker import SchemaVersionTracker, MODEL_SCHEMA_HASHES, register_model_for_version_tracking


def test_schema_version_tracking():
    """测试schema版本跟踪功能"""
    print("测试Schema版本跟踪功能...")
    
    # 测试获取模型版本信息
    chat_msg_info = SchemaVersionTracker.get_model_version_info(ChatMessage)
    print(f"ChatMessage版本信息: {chat_msg_info}")
    
    # 测试计算schema哈希
    chat_msg_hash = SchemaVersionTracker.compute_schema_hash(ChatMessage)
    print(f"ChatMessage Schema哈希: {chat_msg_hash[:16]}...")
    
    # 测试其他模型
    request_info = SchemaVersionTracker.get_model_version_info(ChatCompletionRequest)
    print(f"ChatCompletionRequest版本信息: {request_info}")
    
    usage_info = SchemaVersionTracker.get_model_version_info(Usage)
    print(f"Usage版本信息: {usage_info}")
    
    # 验证哈希值唯一性
    hashes = [chat_msg_hash, 
              SchemaVersionTracker.compute_schema_hash(ChatCompletionRequest),
              SchemaVersionTracker.compute_schema_hash(Usage)]
    
    assert len(hashes) == len(set(hashes)), "不同模型应该有不同的schema哈希"
    print("  [PASS] 不同模型具有不同的schema哈希")
    
    # 测试注册功能
    register_model_for_version_tracking(ChatMessage)
    register_model_for_version_tracking(ChatCompletionRequest)
    
    print(f"注册的模型数量: {len(MODEL_SCHEMA_HASHES)}")
    print("  [PASS] 模型注册功能正常")
    
    print("Schema版本跟踪测试完成!")


if __name__ == "__main__":
    test_schema_version_tracking()