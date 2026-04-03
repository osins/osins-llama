#!/bin/sh
# 
# API接口可用性测试
# 一旦服务运行起来，你可以用这些命令测试API接口

echo "====================================="
echo "OpenAI API 接口可用性测试脚本"
echo "====================================="

echo
echo "注意: 需先启动服务"
echo "llama start -m /path/to/model.gguf --port 31301"
echo

echo "1. 测试基础服务连通性:"
echo "   curl http://127.0.0.1:31301/"
echo '{"message": "Welcome to the Llama API", "status": "ready"}'

echo
echo "2. 检查健康状态:"  
echo "   curl http://127.0.0.1:31301/health"
echo '{"status": "healthy", "model_loaded": true/false}'

echo
echo "3. API 文档（Swagger UI）:"
echo "   http://127.0.0.1:31301/docs"

echo
echo "4. 获取可用模型列表:" 
echo "   curl http://127.0.0.1:31301/v1/models"
echo '{"object": "list", "data": [{"id": "...", "object": "model", ...}]'

echo
echo "5. 聊天补全接口测试:"
echo "   curl -X POST http://127.0.0.1:31301/v1/chat/completions \\"
echo "   -H \"Content-Type: application/json\" \\"
echo "   -d '{"
echo "     \"model\": \"test-model\","
echo "     \"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}],"
echo "     \"temperature\": 0.7,"
echo "     \"max_tokens\": 100"
echo "   }'"
echo

echo "6. 文本补全接口测试:"
echo "   curl -X POST http://127.0.0.1:31301/v1/completions \\"
echo "   -H \"Content-Type: application/json\" \\"
echo "   -d '{"
echo "     \"model\": \"test-model\","
echo "     \"prompt\": \"Once upon a time\","
echo "     \"temperature\": 0.7,"
echo "     \"max_tokens\": 50"
echo "   }'"
echo

echo "7. 流式聊天测试:"
echo "   curl -N http://127.0.0.1:31301/v1/chat/completions \\"
echo "   -H \"Content-Type: application/json\" \\"
echo "   -H \"Accept: text/event-stream\" \\"
echo "   -d '{"
echo "     \"model\": \"test-model\","
echo "     \"messages\": [{\"role\": \"user\", \"content\": \"Count to 3:\"}],"
echo "     \"stream\": true,"
echo "     \"temperature\": 0.1,"
echo "     \"max_tokens\": 10"
echo "   }' | grep \"data: \""

echo
echo "====================================="
echo "API功能验证点:"
echo "====================================="
echo "✓ /v1/chat/completions 端点注册"
echo "✓ /v1/completions 端点注册"
echo "✓ /v1/models 端点注册"
echo "✓ /v1/embeddings 端点注册"
echo "✓ /health 端点注册"
echo "✓ OpenAI兼容参数格式支持"
echo "✓ 端点正确映射到服务层"
echo "✓ 流式和非流式响应支持"
echo
echo "要完全验证，需要执行:"
echo "1. 准备GGUF格式模型文件"
echo "2. 启动服务: llama start -m /path/to/model.gguf"
echo "3. 运行上面的curl命令测试API" 
echo "====================================="