"""
验证参数过滤功能的测试脚本
"""
import asyncio
from src.llama.core.model_manager import filter_llama_params, LLAMA_VALID_PARAMS


def test_param_filtering():
    """测试参数过滤功能"""
    print("Testing parameter filtering...")
    
    # 模拟来自SillyTavern的请求参数
    request_params = {
        'prompt': 'Test prompt',
        'max_tokens': 200,
        'max_new_tokens': 300,  # 同义参数
        'n_predict': 400,       # 同义参数
        'temperature': 0.7,
        'top_p': 0.9,
        'n': 1,                 # llama-cpp-python不支持的参数
        'best_of': 1,           # llama-cpp-python不支持的参数
        'model': 'test-model',  # llama-cpp-python不支持的参数
        'stop': ['\n', 'END'],
        'stopping_strings': ['STOP'],  # 同义参数
        'repetition_penalty': 1.1,
        'rep_pen': 1.2,         # 同义参数
        'cache_prompt': True,   # llama-cpp-python不支持的参数
        'stream': True
    }
    
    print(f"Original params: {list(request_params.keys())}")
    
    # 应用过滤
    filtered_params = filter_llama_params(request_params)
    
    print(f"Filtered params: {list(filtered_params.keys())}")
    
    # 验证过滤结果
    for param in filtered_params:
        assert param in LLAMA_VALID_PARAMS, f"参数 {param} 不在白名单中"
    
    # 验证同义参数处理
    assert filtered_params['max_tokens'] == 400, f"max_tokens 应该是最大值 400，实际是 {filtered_params['max_tokens']}"
    
    # 验证stop参数合并
    expected_stops = ['\n', 'END', 'STOP']
    assert filtered_params['stop'] == expected_stops, f"stop 应该是 {expected_stops}，实际是 {filtered_params['stop']}"
    
    # 验证不支持的参数被移除
    unsupported_params = ['n', 'best_of', 'model', 'cache_prompt']
    for param in unsupported_params:
        assert param not in filtered_params, f"参数 {param} 应该被过滤掉"
    
    print("√ 参数过滤测试通过！")


def test_empty_and_none_params():
    """测试空参数和None值"""
    print("Testing empty and None params...")
    
    # 测试空参数
    empty_result = filter_llama_params({})
    assert empty_result == {}, "空参数应该返回空字典"
    
    # 测试None值（虽然在实际使用中不太可能出现）
    result_with_none = filter_llama_params({'temperature': 0.7, 'top_p': None})
    # None值应该被保留，因为我们只过滤不支持的参数名，而不是值
    assert 'top_p' in result_with_none, "top_p应该在结果中，即使值为None"
    
    print("√ 空参数和None值测试通过！")


def test_stop_parameter_processing():
    """测试stop参数处理"""
    print("Testing stop parameter processing...")
    
    # 测试stop参数去重
    params_with_duplicates = {
        'max_tokens': 100,
        'stop': ['\n', 'END', '\n', 'STOP'],  # 包含重复项
    }
    
    result = filter_llama_params(params_with_duplicates)
    expected_stop = ['\n', 'END', 'STOP']
    assert result['stop'] == expected_stop, f"stop 应该去重为 {expected_stop}，实际是 {result['stop']}"
    
    # 测试空stop参数
    params_with_empty_stop = {
        'max_tokens': 100,
        'stop': []  # 空列表
    }
    
    result = filter_llama_params(params_with_empty_stop)
    assert 'stop' not in result, "空stop列表应该被移除"
    
    # 测试包含空字符串的stop参数
    params_with_empty_strings = {
        'max_tokens': 100,
        'stop': ['', '\n', '', 'END']  # 包含空字符串
    }
    
    result = filter_llama_params(params_with_empty_strings)
    expected_stop = ['\n', 'END']
    assert result['stop'] == expected_stop, f"stop 应该去除空字符串为 {expected_stop}，实际是 {result['stop']}"
    
    print("√ stop参数处理测试通过！")


if __name__ == "__main__":
    test_param_filtering()
    test_empty_and_none_params()
    test_stop_parameter_processing()
    print("\n所有测试通过！参数过滤功能正常工作。")