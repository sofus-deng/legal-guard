# Legal Guard - 法律文件智能审查助手

## 项目简介
Legal Guard是基于蓝耘MCP平台开发的法律文件智能审查工具，专为律师、法务人员和合同管理者设计。利用基于Qwen3-235B-A22B模型的强大自然语言处理能力，自动扫描法律文件中的潜在风险、关键条款缺失和合规问题。

## 核心功能
1. **关键条款缺失检测** - 自动检查合同中是否缺少核心法律条款
2. **高风险条款识别** - 分析合同条款中的潜在法律风险
3. **合规性审查** - 对照《民法典》、GDPR等核心法规检查合规性
4. **智能风险评估** - 提供低/中/高三级整体风险评级

## 快速使用
```bash
curl -X POST "http://your-server-ip:8080/execute" \
  -H "Content-Type: multipart/form-data" \
  -F "tool_name=legal_review" \
  -F "parameters={}" \
  -F "contract_file=@/path/to/your_contract.pdf
```

## 环境要求
- Python 3.8+
- 蓝耘API密钥

## 安装步骤
```bash
# 克隆仓库
git clone https://github.com/sofus-deng/legal-guard.git
cd LegalGuard

# 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn pdfplumber requests python-multipart

# 设置环境变量 
export LANYUN_API_KEY=your_api_key_here

# 启动服务
uvicorn legal_guard:app --reload --port 8080
```