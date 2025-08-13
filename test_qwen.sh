#!/bin/bash
# LegalGuard Qwen3 模型测试脚本

echo "测试健康检查端点:"
curl -s http://localhost:8080/health | jq

echo "\n测试法律审查功能 - 中国大陆管辖:"
curl -X POST "http://localhost:8080/execute" \
  -H "Content-Type: multipart/form-data" \
  -F "tool_name=legal_review" \
  -F 'parameters={"critical_clauses": ["不可抗力", "争议解决", "知识产权"]}' \
  -F "jurisdiction=中国大陆" \
  -F "contract_file=@./rental_contract_cn.pdf" | jq

echo "\n测试法律审查功能 - 欧盟管辖:"
curl -X POST "http://localhost:8080/execute" \
  -H "Content-Type: multipart/form-data" \
  -F "tool_name=legal_review" \
  -F "jurisdiction=欧盟" \
  -F "contract_file=@./gdpr_agreement.pdf" | jq

echo "\n测试完成!"