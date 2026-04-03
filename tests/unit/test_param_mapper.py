"""
测试参数映射功能
"""

import pytest
from llama.core.param_mapper import map_to_llama_params


def test_basic_mapping():
    """测试基本参数映射"""
    raw_params = {
        "max_tokens": 100,
        "temperature": 0.7,
        "top_p": 0.9,
        "n": 1  # 这个参数会被忽略
    }
    
    result = map_to_llama_params(raw_params)
    
    # 检查有效参数被保留
    assert "max_tokens" in result
    assert "temperature" in result
    assert "top_p" in result
    
    # 检查'n'参数被忽略
    assert "n" not in result
    
    # 检查参数值正确
    assert result["max_tokens"] == 100
    assert result["temperature"] == 0.7
    assert result["top_p"] == 0.9


def test_synonymous_parameters():
    """测试同义参数映射"""
    raw_params = {
        "max_new_tokens": 200,
        "n_predict": 300,
        "num_predict": 400,
        "max_tokens": 100,
        "temperature": 0.8
    }
    
    result = map_to_llama_params(raw_params)
    
    # 所有同义参数应映射到"max_tokens"，并取最大值
    assert result["max_tokens"] == 400
    assert result["temperature"] == 0.8


def test_stop_parameter_merge():
    """测试stop参数合并去重"""
    raw_params = {
        "max_tokens": 100,
        "stop": ["\n", "END"],
        "stopping_strings": ["STOP", "\n"]  # 与上面的\n重复
    }
    
    result = map_to_llama_params(raw_params)
    
    # stop参数应合并去重
    assert result["stop"] == ["\n", "END", "STOP"]


def test_ignore_specific_parameters():
    """测试特定参数被忽略"""
    raw_params = {
        "max_tokens": 100,
        "temperature": 0.7,
        "n": 1,  # 被忽略
        "model": "some-model",  # 被忽略
        "api_type": "openai",  # 被忽略
        "ban_eos_token": True,  # 被忽略
    }
    
    result = map_to_llama_params(raw_params)
    
    # 检查有效参数
    assert "max_tokens" in result
    assert "temperature" in result
    
    # 检查被忽略的参数
    assert "n" not in result
    assert "model" not in result
    assert "api_type" not in result
    assert "ban_eos_token" not in result


def test_complex_mapping():
    """测试复杂参数映射"""
    raw_params = {
        "max_tokens": 100,
        "max_new_tokens": 200,  # 同义参数，应取最大值
        "temperature": 0.8,
        "top_p": 0.95,
        "top_k": 40,
        "min_p": 0.05,
        "typical_p": 1.0,
        "repetition_penalty": 1.1,
        "rep_pen": 1.2,  # 同义参数，应替换为repeat_penalty
        "frequency_penalty": 0.5,
        "presence_penalty": 0.3,
        "stop": ["\n"],
        "stopping_strings": ["END"],  # 应与stop合并
        "stream": True,
        "grammar": "some_grammar",
        "logit_bias": {"1": 0.5},
        "mirostat_mode": 0,
        "mirostat_tau": 5.0,
        "mirostat_eta": 0.1,
        "tfs_z": 1.0,
        "tfs": 1.0,  # 同义参数
        "n": 1,  # 被忽略
        "model": "test-model",  # 被忽略
        "api_type": "openai",  # 被忽略
    }
    
    result = map_to_llama_params(raw_params)
    
    # 检查参数映射
    assert "max_tokens" in result
    assert result["max_tokens"] == 200  # 取最大值
    assert result["temperature"] == 0.8
    assert result["top_p"] == 0.95
    assert result["top_k"] == 40
    assert result["min_p"] == 0.05
    assert result["typical_p"] == 1.0
    assert result["repeat_penalty"] == 1.2  # rep_pen映射到repeat_penalty
    assert result["frequency_penalty"] == 0.5
    assert result["presence_penalty"] == 0.3
    assert result["stop"] == ["\n", "END"]  # 合并去重
    assert result["stream"] is True
    assert result["grammar"] == "some_grammar"
    assert result["logit_bias"] == {"1": 0.5}
    assert result["mirostat_mode"] == 0
    assert result["mirostat_tau"] == 5.0
    assert result["mirostat_eta"] == 0.1
    assert result["tfs_z"] == 1.0  # tfs映射到tfs_z
    
    # 检查被忽略的参数
    assert "n" not in result
    assert "model" not in result
    assert "api_type" not in result


def test_edge_cases():
    """测试边界情况"""
    # 空参数
    result = map_to_llama_params({})
    assert result == {}
    
    # 只有被忽略的参数
    result = map_to_llama_params({"n": 1, "model": "test"})
    assert result == {}
    
    # 只有有效参数
    result = map_to_llama_params({"max_tokens": 100, "temperature": 0.7})
    assert result == {"max_tokens": 100, "temperature": 0.7}


if __name__ == "__main__":
    test_basic_mapping()
    test_synonymous_parameters()
    test_stop_parameter_merge()
    test_ignore_specific_parameters()
    test_complex_mapping()
    test_edge_cases()
    print("All tests passed!")