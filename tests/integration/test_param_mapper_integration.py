"""
集成测试：验证参数映射功能解决了SillyTavern参数问题
"""

import pytest
from src.llama.core.param_mapper import map_to_llama_params


def test_sillytavern_request_parameters():
    """
    测试SillyTavern请求参数是否能被正确映射和过滤
    这个测试验证了原始问题是否已解决
    """
    # 模拟来自SillyTavern的请求参数，包括导致错误的'n'参数
    sillytavern_params = {
        'prompt': "Write Seraphina's next reply in a fictional chat between Seraphina and Richard.",
        'model': 'Qwen2.5-7B-Instruct-Uncensored.Q4_K_M.gguf',
        'max_new_tokens': 300,
        'max_tokens': 300,
        'temperature': 1.5,
        'top_p': 0.95,
        'typical_p': 1,
        'typical': 1,
        'min_p': 0.01,
        'repetition_penalty': 1.1,
        'frequency_penalty': 0,
        'presence_penalty': 0,
        'top_k': 0,
        'skew': 0,
        'min_tokens': 0,
        'add_bos_token': True,
        'smoothing_factor': 0,
        'smoothing_curve': 1,
        'dry_allowed_length': 2,
        'dry_multiplier': 0.75,
        'dry_base': 1.75,
        'dry_sequence_breakers': ['\n', ':', '"', '*'],
        'dry_penalty_last_n': 0,
        'max_tokens_second': 0,
        'samplers': [
            'penalties', 'dry',
            'top_n_sigma', 'top_k',
            'typ_p', 'tfs_z',
            'typical_p', 'xtc',
            'top_p', 'min_p',
            'temperature'
        ],
        'stopping_strings': ['\nRichard:', '\n***'],
        'stop': ['\nRichard:', '\n***'],
        'truncation_length': 2048,
        'ban_eos_token': False,
        'skip_special_tokens': True,
        'include_reasoning': True,
        'top_a': 0,
        'tfs': 1,
        'mirostat_mode': 0,
        'mirostat_tau': 5,
        'mirostat_eta': 0.1,
        'custom_token_bans': '',
        'banned_strings': [],
        'api_type': 'llamacpp',
        'api_server': 'http://192.168.50.2:31301/v1',
        'xtc_threshold': 0.1,
        'xtc_probability': 0,
        'nsigma': 0,
        'top_n_sigma': 0,
        'min_keep': 0,
        'n': 1,  # ← 这是导致原始错误的参数
        'rep_pen': 1.1,
        'rep_pen_range': 0,
        'repetition_penalty_range': 0,
        'guidance_scale': 1,
        'negative_prompt': '',
        'repeat_penalty': 1.1,
        'repeat_last_n': 0,
        'n_predict': 300,
        'num_predict': 300,
        'num_ctx': 2048,
        'mirostat': 0,
        'ignore_eos': False,
        'rep_pen_slope': 1,
        'logit_bias': [],
        'grammar': '',
        'cache_prompt': True,
        'stream': True
    }

    # 应用参数映射和过滤
    result = map_to_llama_params(sillytavern_params)

    # 验证关键参数被正确映射
    assert 'max_tokens' in result
    # max_tokens应该是300（因为max_new_tokens、n_predict、num_predict都是300）
    assert result['max_tokens'] == 300

    assert result['temperature'] == 1.5
    assert result['top_p'] == 0.95

    # 验证导致原始错误的'n'参数被移除
    assert 'n' not in result

    # 验证stop参数被正确合并去重
    assert 'stop' in result
    expected_stops = ['\nRichard:', '\n***']
    assert result['stop'] == expected_stops

    # 验证其他被忽略的参数也被正确移除
    ignored_params = ['model', 'api_type', 'api_server', 'truncation_length', 'add_bos_token']
    for param in ignored_params:
        assert param not in result, f"Parameter {param} should be filtered out"

    print("✓ SillyTavern参数映射测试通过！原始问题已解决")


def test_specific_error_case():
    """
    测试特定的错误案例，确保'n'参数被正确过滤
    """
    problematic_params = {
        "prompt": "Test prompt",
        "n": 1,  # 这是导致Llama.__call__()错误的参数
        "max_tokens": 100,
        "temperature": 0.7
    }

    result = map_to_llama_params(problematic_params)

    # 验证'n'参数被移除
    assert 'n' not in result, "'n'参数应该被过滤掉"

    # 验证其他参数保留
    assert 'max_tokens' in result
    assert 'temperature' in result
    assert result['max_tokens'] == 100
    assert result['temperature'] == 0.7

    print("✓ 特定错误案例测试通过！")


if __name__ == "__main__":
    test_sillytavern_request_parameters()
    test_specific_error_case()
    print("所有集成测试通过！")