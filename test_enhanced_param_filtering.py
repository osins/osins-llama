"""
验证增强的参数过滤功能的测试脚本
"""
import asyncio
from src.llama.core.model_manager import filter_llama_params, LLAMA_VALID_PARAMS


def test_grammar_filtering():
    """测试grammar参数过滤功能"""
    print("Testing grammar parameter filtering...")
    
    # 测试空字符串grammar
    params_with_empty_grammar = {
        'max_tokens': 100,
        'grammar': "",  # 空字符串
        'temperature': 0.7
    }
    
    result = filter_llama_params(params_with_empty_grammar)
    assert 'grammar' not in result, "空字符串grammar应该被移除"
    assert result['max_tokens'] == 100
    assert result['temperature'] == 0.7
    print("√ 空字符串grammar测试通过！")
    
    # 测试None grammar（应该保留）
    params_with_none_grammar = {
        'max_tokens': 100,
        'grammar': None,
        'temperature': 0.7
    }
    
    result = filter_llama_params(params_with_none_grammar)
    assert 'grammar' in result, "None grammar应该被保留"
    print("√ None grammar测试通过！")


def test_logit_bias_filtering():
    """测试logit_bias参数过滤功能"""
    print("Testing logit_bias parameter filtering...")
    
    # 测试空列表logit_bias
    params_with_empty_logit_bias = {
        'max_tokens': 100,
        'logit_bias': [],  # 空列表
        'temperature': 0.7
    }
    
    result = filter_llama_params(params_with_empty_logit_bias)
    assert 'logit_bias' not in result, "空列表logit_bias应该被移除"
    print("√ 空列表logit_bias测试通过！")
    
    # 测试正常的logit_bias列表，应该转换为字典
    params_with_list_logit_bias = {
        'max_tokens': 100,
        'logit_bias': [[123, 1.0], [456, -1.0]],  # 列表格式
        'temperature': 0.7
    }
    
    result = filter_llama_params(params_with_list_logit_bias)
    assert 'logit_bias' in result, "非空logit_bias列表应该被转换"
    expected_dict = {123: 1.0, 456: -1.0}
    assert result['logit_bias'] == expected_dict, f"列表应该转换为字典 {expected_dict}, 实际是 {result['logit_bias']}"
    print("√ logit_bias列表转字典测试通过！")
    
    # 测试格式错误的logit_bias列表
    params_with_bad_logit_bias = {
        'max_tokens': 100,
        'logit_bias': [["not_a_number", 1.0]],  # 格式错误
        'temperature': 0.7
    }
    
    result = filter_llama_params(params_with_bad_logit_bias)
    assert 'logit_bias' not in result, "格式错误的logit_bias应该被移除"
    print("√ 格式错误logit_bias测试通过！")


def test_stop_filtering():
    """测试stop参数过滤功能"""
    print("Testing stop parameter filtering...")
    
    # 测试包含空字符串的stop列表
    params_with_empty_strings_in_stop = {
        'max_tokens': 100,
        'stop': ['\n', '', 'END', ''],  # 包含空字符串
        'temperature': 0.7
    }
    
    result = filter_llama_params(params_with_empty_strings_in_stop)
    expected_stop = ['\n', 'END']
    assert result['stop'] == expected_stop, f"stop应该去除空字符串为 {expected_stop}，实际是 {result['stop']}"
    print("√ stop参数去空字符串测试通过！")
    
    # 测试全是空字符串的stop列表
    params_with_all_empty_stop = {
        'max_tokens': 100,
        'stop': ['', '', ''],  # 全是空字符串
        'temperature': 0.7
    }
    
    result = filter_llama_params(params_with_all_empty_stop)
    assert 'stop' not in result, "全是空字符串的stop列表应该被移除"
    print("√ 全空stop列表测试通过！")


def test_comprehensive_filtering():
    """综合测试：模拟SillyTavern的真实请求"""
    print("Testing comprehensive parameter filtering (simulating SillyTavern request)...")
    
    # 模拟SillyTavern的真实请求参数
    sillytavern_params = {
        'prompt': "Write Seraphina's next reply...",
        'model': 'Qwen2.5-7B-Instruct-Uncensored.Q4_K_M.gguf',
        'max_new_tokens': 300,
        'max_tokens': 200,  # 同义参数，应该取最大值
        'temperature': 1.5,
        'top_p': 0.95,
        'n': 1,  # 不支持的参数
        'best_of': 1,  # 不支持的参数
        'grammar': "",  # 空字符串，会导致崩溃
        'logit_bias': [],  # 空列表
        'stop': ['\nRichard:', '\n***', ''],  # 包含空字符串
        'stopping_strings': ['STOP'],  # 同义参数，应该合并
        'repetition_penalty': 1.1,
        'rep_pen': 1.2,  # 同义参数，应该取最大值
        'cache_prompt': True,  # 不支持的参数
        'stream': True
    }
    
    print(f"Original params: {list(sillytavern_params.keys())}")
    
    result = filter_llama_params(sillytavern_params)
    
    print(f"Filtered params: {list(result.keys())}")
    
    # 验证过滤结果
    for param in result:
        assert param in LLAMA_VALID_PARAMS, f"参数 {param} 不在白名单中"
    
    # 验证同义参数处理
    assert result['max_tokens'] == 300, f"max_tokens 应该是最大值 300，实际是 {result['max_tokens']}"
    assert result['repeat_penalty'] == 1.2, f"repeat_penalty 应该是最大值 1.2，实际是 {result['repeat_penalty']}"
    
    # 验证stop参数合并和去空
    expected_stop = ['\nRichard:', '\n***', 'STOP']
    assert result['stop'] == expected_stop, f"stop 应该合并并去空为 {expected_stop}，实际是 {result['stop']}"
    
    # 验证危险参数被移除
    dangerous_params = ['grammar', 'logit_bias']  # grammar是空字符串，logit_bias是空列表
    for param in dangerous_params:
        assert param not in result, f"危险参数 {param} 应该被移除"
    
    # 验证不支持的参数被移除
    unsupported_params = ['n', 'best_of', 'model', 'cache_prompt']
    for param in unsupported_params:
        assert param not in result, f"不支持的参数 {param} 应该被过滤掉"
    
    print("√ 综合测试通过！")


if __name__ == "__main__":
    test_grammar_filtering()
    test_logit_bias_filtering()
    test_stop_filtering()
    test_comprehensive_filtering()
    print("\n所有测试通过！增强的参数过滤功能正常工作。")