user_prompt_template = """
Below is the weekly material cost analysis JSON contract for the parent item.
Please generate the complete CFO-ready weekly Material Cost Review in Markdown
format based on the rules in the system prompt.

Do not restate the JSON. Base all commentary strictly on the numbers provided.
Do NOT add interpretations beyond what is explicitly in the contract.

JSON:
{{jsondata}}
"""