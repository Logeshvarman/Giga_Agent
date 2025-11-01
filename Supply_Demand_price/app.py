from langchain_ollama import OllamaLLM

llm = OllamaLLM(
    model="llama3.2:1b",
    temperature=0.2,
    top_p=0.9
)

def recommend_price(product_name, demand_level, supply_level, base_cost):
    """
    Uses the LLM to recommend a price based on demand and supply.
    """
    prompt = f"""
    You are a pricing decision AI.
    Analyze the following information and recommend an optimal price.

    Product: {product_name}
    Demand level: {demand_level}  (e.g. High, Medium, Low)
    Supply level: {supply_level}  (e.g. High, Medium, Low)
    Base production cost: ₹{base_cost}

    Rules:
    - If demand > supply, increase the price.
    - If supply > demand, decrease the price.
    - Maintain a reasonable profit margin.
    - Return only the final price and reasoning in concise form.
    """

    # LLM reasoning
    result = llm.invoke(prompt)
    return result

# Example usage
response = recommend_price("Premium Rice", "High", "Low", 80)
print(response)
