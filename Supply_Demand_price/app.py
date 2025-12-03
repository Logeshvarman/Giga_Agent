import os
from dotenv import load_dotenv
load_dotenv()

os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT")

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate

transport = StreamableHttpTransport("http://localhost:8001/mcp")
client = Client(transport)


llm = OllamaLLM(model="gpt-oss:120b-cloud", temperature=0.3)

template = """
You are an AI pricing expert.

Product: {name}
Grade: {grade}
Base Price: {price}
Available Quantity: {quantity}
Requested Quantity: {needed}
Demand Level: {demand}

Rules:
1. If Requested > Available:
   - HIGH: +10–25%
   - MEDIUM: +5–15%
   - LOW: +0–5%
2. If Requested < Available:
   - HIGH: +0–5%
   - MEDIUM: -5%
   - LOW: -5–20%
3. Round to nearest 0.5

Return only JSON:
{{
  "recommended_price": <number>,
  "reason": "<text>"
}}
"""

prompt = PromptTemplate(
    input_variables=["name", "grade", "price", "quantity", "needed", "demand"],
    template=template,
)

chain = prompt | llm

async def recommend_price(product_name: str, grade: str):
    product_data = None
    request_data = None

    try:
        async with client:
            result_obj = await client.call_tool(
                "get_product_info",
                arguments={
                    "product_name": product_name,
                    "grade": grade
                }
            )

            if result_obj.content and result_obj.content[0].type == "text":
                tool_output = json.loads(result_obj.content[0].text)
                product_data = tool_output.get("product")
                request_data = tool_output.get("request")
            else:
                return {"error": "Tool did not return valid text content"}

    except Exception as e:
        return {"error": f"MCP tool failed: {str(e)}"}

    if not product_data or not request_data:
        return {"error": "Missing product/request data from MCP tool"}

    try:
        response_str = await chain.ainvoke({
            "name": product_data["name"],
            "grade": product_data["grade"],
            "price": product_data["price"],
            "quantity": product_data["quantity"],
            "needed": request_data["needed_supply_count"],
            "demand": product_data["demand_level"],
        })

        clean_json = response_str.strip().replace("```json", "").replace("```", "")
        data = json.loads(clean_json)

        return {
            "recommended_price": float(data["recommended_price"]),
            "reason": data["reason"]
        }

    except Exception as e:
        return {
            "error": "failed to generate price",
            "details": str(e)
        }

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/recommend-price/")
@app.get("/recommend-price")
async def price_api(product_name: str, grade: str):
     result = await recommend_price(product_name, grade)
     print(f"[PRICE] product={product_name!r} grade={grade!r} → {result}")
     return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("agent:app", host="0.0.0.0", port=8000, reload=True)
