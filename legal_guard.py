import os
import json
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pdfplumber import open as pdf_open
import time

app = FastAPI()

# 从环境变量获取API密钥
LANYUN_API_KEY = os.getenv("LANYUN_API_KEY")

# 关键法律条款清单
CRITICAL_CLAUSES = [
    "不可抗力", "争议解决", "保密条款", 
    "违约责任", "知识产权", "合同终止",
    "付款条件", "法律适用", "通知送达"
]

# MCP协议端点
@app.get("/tools")
async def list_tools():
    return [{
        "name": "legal_review",
        "description": "基于Qwen3模型的法律文件审查工具",
        "parameters": {
            "contract_file": {"type": "file", "description": "上传的PDF合同文件"},
            "jurisdiction": {"type": "string", "description": "管辖区域", "default": "中国大陆"},
            "critical_clauses": {"type": "array", "description": "自定义关键条款", "optional": True}
        }
    }]

@app.post("/execute")
async def execute_tool(
    tool_name: str = Form(...),
    parameters: str = Form("{}"),
    contract_file: UploadFile = File(...),
    jurisdiction: str = Form("中国大陆")
):
    if tool_name != "legal_review":
        raise HTTPException(status_code=404, detail="工具未找到")
    
    start_time = time.time()
    file_path = f"temp_{contract_file.filename}"
    
    try:
        # 保存并提取PDF文本
        with open(file_path, "wb") as f:
            content = await contract_file.read()
            f.write(content)
        
        text = ""
        with pdf_open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=1, y_tolerance=1)
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        return {"error": f"文件处理失败: {str(e)}"}
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    if not text:
        return {"error": "未提取到有效文本"}
    
    # 解析可选参数
    try:
        params = json.loads(parameters)
        custom_clauses = params.get("critical_clauses", CRITICAL_CLAUSES)
    except:
        custom_clauses = CRITICAL_CLAUSES
    
    # 构建Qwen3专用提示
    prompt = f"""
    <|im_start|>system
        你是一名精通{jurisdiction}法律体系的资深律师，请严格按以下JSON格式输出合同审查报告：
        {{
        "missing_clauses": [缺少的关键条款列表（对照：{", ".join(custom_clauses)}],
        "high_risk_terms": ["高风险条款描述及法律依据"],
        "overall_risk": "低/中/高"
        }}

        特别注意：
        - 引用具体法律条文时注明出处
        - 区分强制性条款和推荐性条款
        - 评估条款缺失的实际法律后果
    <|im_end|>

    <|im_start|>user
        合同摘要：
        {text[:15000]}
        请分析并输出JSON报告<|im_end|>
    """
    
    try:
        # 调用蓝耘Qwen3-235B-A22B模型
        response = requests.post(
            "https://maas-api.lanyun.net/v1/chat/completions",
            headers={"Authorization": f"Bearer {LANYUN_API_KEY}"},
            json={
                "model": "qwen3-235b-a22b",  # 使用Qwen3模型
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一名资深法律专家，擅长识别合同中的法律风险和条款缺失。请用严谨的法律语言进行分析，并引用具体法律条文。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2,  # 降低随机性
                "max_tokens": 2000
            },
            timeout=30
        )
        
        # 处理响应
        result = response.json()
        if "choices" not in result or not result["choices"]:
            return {"error": "蓝耘API返回无效响应"}
        
        content = result['choices'][0]['message']['content']
        analysis_time = round(time.time() - start_time, 2)
        
        # 解析并添加元数据
        try:
            report = json.loads(content)
            report["analysis_time"] = analysis_time
            report["model_used"] = "Qwen3-235B-A22B"
            report["jurisdiction"] = jurisdiction
            return report
        except json.JSONDecodeError:
            return {
                "error": "JSON解析失败",
                "raw_response": content,
                "analysis_time": analysis_time
            }
            
    except requests.exceptions.Timeout:
        return {"error": "蓝耘API请求超时"}
    except Exception as e:
        return {"error": f"蓝耘API错误: {str(e)}"}

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "LegalGuard-Qwen",
        "version": "1.1",
        "model": "Qwen3-235B-A22B"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)