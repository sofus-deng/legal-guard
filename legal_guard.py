import os
import json
import requests
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from pdfplumber import open as pdf_open

app = FastAPI()

# 从环境变量获取API密钥
LANYUN_API_KEY = os.getenv("LANYUN_API_KEY", "YOUR_API_KEY")  # 替换为您的实际密钥

# 关键法律条款清单
CRITICAL_CLAUSES = [
    "不可抗力", "争议解决", "保密条款", 
    "违约责任", "知识产权", "合同终止",
    "付款条件", "法律适用", "通知送达"
]

# MCP协议端点
@app.get("/tools")
async def list_tools():
    """MCP协议要求：列出可用工具"""
    return [{
        "name": "legal_review",
        "description": "法律文件自动审查工具",
        "parameters": {
            "contract_file": {"type": "file", "description": "上传的PDF合同文件"}
        }
    }]

@app.post("/execute")
async def execute_tool(
    tool_name: str = Form(...),
    parameters: str = Form("{}"),
    contract_file: UploadFile = File(...)
):
    """MCP协议要求：执行工具端点"""
    if tool_name != "legal_review":
        raise HTTPException(status_code=404, detail="工具未找到")
    
    # 1. 保存并提取PDF文本
    file_path = f"temp_{contract_file.filename}"
    try:
        # 保存上传的文件
        with open(file_path, "wb") as f:
            content = await contract_file.read()
            f.write(content)
        
        # 提取文本
        text = ""
        with pdf_open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=1, y_tolerance=1)
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return {"error": f"文件处理失败: {str(e)}"}
    finally:
        # 清理临时文件
        if os.path.exists(file_path):
            os.remove(file_path)
    
    if not text:
        return {"error": "未提取到有效文本"}
    
    # 2. 调用蓝耘API进行法律分析
    prompt = f"""
    作为资深法律AI助手，请严格按以下JSON格式输出合同审查报告：
    {{
      "missing_clauses": [缺少的关键条款列表，对照：{", ".join(CRITICAL_CLAUSES)}],
      "high_risk_terms": ["高风险条款1", "高风险条款2"],
      "overall_risk": "低/中/高"
    }}
    
    合同内容摘要：
    {text[:10000]}
    """
    
    try:
        # 调用蓝耘API
        response = requests.post(
            "https://maas-api.lanyun.net/v1/chat/completions",
            headers={"Authorization": f"Bearer {LANYUN_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "/maas/qwen/Qwen3-235B-A22B",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.3  # 降低随机性
            },
            timeout=30
        )
        
        # 处理响应
        result = response.json()
        print(result)
        if "choices" not in result or not result["choices"]:
            return {"error": "蓝耘API返回无效响应"}
        
        content = result['choices'][0]['message']['content']
        
        # 尝试解析JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果返回的不是有效JSON，直接返回原始内容
            return {"raw_response": content}
            
    except requests.exceptions.Timeout:
        return {"error": "蓝耘API请求超时"}
    except Exception as e:
        return {"error": f"蓝耘API错误: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)