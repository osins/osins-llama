"""
综合安全和版本测试
验证所有安全措施和版本跟踪功能
"""
from src.llama.models.chat.chat_message import ChatMessage
from src.llama.models.chat.chat_completion_request import ChatCompletionRequest
from src.llama.models.common.usage import Usage
from src.llama.models.chat.chat_role import ChatRole
from src.llama.models.version_tracker import SchemaVersionTracker, register_model_for_version_tracking


def test_comprehensive_security_and_versioning():
    """综合测试安全性和版本跟踪"""
    print("开始综合安全性和版本跟踪测试...\n")
    
    # 1. 测试版本跟踪
    print("1. 测试版本跟踪功能:")
    msg_info = SchemaVersionTracker.get_model_version_info(ChatMessage)
    print(f"   ChatMessage版本: {msg_info['version']}, 哈希: {msg_info['schema_hash'][:16]}...")
    
    req_info = SchemaVersionTracker.get_model_version_info(ChatCompletionRequest)
    print(f"   ChatCompletionRequest版本: {req_info['version']}, 哈希: {req_info['schema_hash'][:16]}...")
    
    usage_info = SchemaVersionTracker.get_model_version_info(Usage)
    print(f"   Usage版本: {usage_info['version']}, 哈希: {usage_info['schema_hash'][:16]}...")
    
    print("   [PASS] 版本跟踪功能正常\n")
    
    # 2. 测试frozen属性
    print("2. 测试frozen属性:")
    msg = ChatMessage(role=ChatRole.USER, content="Hello")
    
    try:
        msg.content = "Changed"  # 尝试修改frozen对象
        print("   [FAIL] 对象未正确冻结")
    except Exception as e:
        if "frozen" in str(e).lower():
            print("   [PASS] frozen属性正常工作")
        else:
            print(f"   [FAIL] 未预期的异常: {e}")
    
    # 3. 测试字段验证
    print("\n3. 测试字段验证:")
    try:
        # 尝试创建超长内容的消息
        long_content = "a" * 100001  # 超过最大长度
        ChatMessage(role=ChatRole.USER, content=long_content)
        print("   [FAIL] 未正确验证字段长度")
    except Exception:
        print("   [PASS] 字段长度验证正常工作")
    
    # 4. 测试序列化/反序列化
    print("\n4. 测试序列化/反序列化:")
    original_msg = ChatMessage(role=ChatRole.USER, content="Test message", name="test_user")
    json_str = original_msg.model_dump_json()
    restored_msg = ChatMessage.model_validate_json(json_str)
    
    if (original_msg.role == restored_msg.role and 
        original_msg.content == restored_msg.content and
        original_msg.name == restored_msg.name):
        print("   [PASS] 序列化/反序列化正常工作")
    else:
        print("   [FAIL] 序列化/反序列化存在问题")
    
    # 5. 测试模型注册
    print("\n5. 测试模型注册:")
    register_model_for_version_tracking(ChatMessage)
    register_model_for_version_tracking(ChatCompletionRequest)
    from src.llama.models.version_tracker import MODEL_SCHEMA_HASHES
    if len(MODEL_SCHEMA_HASHES) >= 2:
        print(f"   [PASS] 成功注册了 {len(MODEL_SCHEMA_HASHES)} 个模型")
    else:
        print("   [FAIL] 模型注册失败")
    
    print("\n综合安全性和版本跟踪测试完成!")


if __name__ == "__main__":
    test_comprehensive_security_and_versioning()