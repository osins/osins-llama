from typing import Union, List
from src.llama.models.chat.chat_message import ChatMessage
from src.llama.exceptions import ValidationError
from src.llama.core.logger_manager import logger


def count_tokens(text: Union[str, None]) -> int:
    """
    计算文本的token数量

    Args:
        text: 输入文本

    Returns:
        token数量

    Raises:
        ValidationError: 当输入无效时抛出异常
    """
    if text is None:
        return 0
        
    if not isinstance(text, str):
        text = str(text)
        
    # 处理空字符串
    if not text:
        return 0
    
    # 对于非常大的文本，我们可以使用近似估算以避免性能问题
    if len(text) > 1000000:  # 1MB 以上
        logger.warning(f"Processing very large text ({len(text)} chars), using estimation")
        # 简单估算：英文平均3个字符一个token，中文平均1.5个字符一个token
        # 这里使用保守估计
        return min(len(text) // 2, 500000)
    
    try:
        # 使用Python内置方法进行简单估算
        # 实际上llama.cpp有自己的tokenizer，这里简化处理
        # 在实际应用中，应该使用llama.cpp的tokenizer
        token_estimate = len(text.encode('utf-8')) // 4
        return max(token_estimate, 1)  # 至少返回1个token
    except Exception as e:
        logger.error(f"Error counting tokens for text: {str(e)}")
        raise ValidationError(f"Error processing token count: {str(e)}")


def count_tokens_in_messages(messages: List[Union[dict, ChatMessage]]) -> int:
    """
    计算消息列表的token数量

    Args:
        messages: 消息列表

    Returns:
        token数量

    Raises:
        ValidationError: 当输入无效时抛出异常
    """
    if not messages:
        return 0
    
    if not isinstance(messages, list):
        raise ValidationError("Messages must be a list")
    
    total_tokens = 0
    for i, message in enumerate(messages):
        try:
            if isinstance(message, dict):
                role = message.get("role", "")
                content = message.get("content", "")

                total_tokens += count_tokens(role)

                if isinstance(content, str):
                    total_tokens += count_tokens(content)
                elif isinstance(content, list):
                    for j, part in enumerate(content):
                        if isinstance(part, dict) and "text" in part:
                            total_tokens += count_tokens(part["text"])
                        elif isinstance(part, str):
                            total_tokens += count_tokens(part)
                        else:
                            logger.warning(f"Unknown content part type at message {i}, part {j}: {type(part)}")
                else:
                    logger.warning(f"Unknown content type at message {i}: {type(content)}")
            elif isinstance(message, ChatMessage):
                role_value = message.role.value if hasattr(message.role, 'value') else str(message.role)
                total_tokens += count_tokens(role_value)
                
                if isinstance(message.content, str):
                    total_tokens += count_tokens(message.content)
                elif isinstance(message.content, list):
                    for j, part in enumerate(message.content):
                        if hasattr(part, 'text'):
                            total_tokens += count_tokens(part.text)
                        elif isinstance(part, str):
                            total_tokens += count_tokens(part)
                        else:
                            logger.warning(f"Unknown content part type at message {i}, part {j}: {type(part)}")
                else:
                    logger.warning(f"Unknown content type at message {i}: {type(message.content)}")
            else:
                logger.warning(f"Unknown message type at index {i}: {type(message)}")
                total_tokens += count_tokens(str(message))
        except Exception as e:
            logger.error(f"Error processing message at index {i}: {str(e)}")
            raise ValidationError(f"Error processing message at index {i}: {str(e)}")

    return total_tokens


def count_completion_tokens(prompt: Union[str, List[str], None]) -> int:
    """
    计算completion请求的prompt token数量

    Args:
        prompt: Prompt文本或文本列表

    Returns:
        token数量

    Raises:
        ValidationError: 当输入无效时抛出异常
    """
    if prompt is None:
        return 0
    
    total_tokens = 0
    if isinstance(prompt, str):
        total_tokens = count_tokens(prompt)
    elif isinstance(prompt, list):
        for i, p in enumerate(prompt):
            try:
                total_tokens += count_tokens(p)
            except Exception as e:
                logger.error(f"Error processing prompt at index {i}: {str(e)}")
                raise ValidationError(f"Error processing prompt at index {i}: {str(e)}")
    else:
        raise ValidationError(f"Prompt must be string or list of strings, got {type(prompt)}")

    return total_tokens