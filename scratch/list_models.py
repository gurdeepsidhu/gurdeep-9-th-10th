from openai import OpenAI
import os

client = OpenAI(
    api_key="xai-JiehwP2pZU1ziMEJsOMAYrejYUU7YlYlO3SwgeASJ9ONH21LB2y4xtIzlp6x30nFwrdcTsuuw5bJVTi9",
    base_url="https://api.x.ai/v1"
)

try:
    models = client.models.list()
    print("Available Models:")
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"Error: {e}")
