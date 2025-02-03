import base64
from groq import AsyncGroq
import os
from dotenv import load_dotenv

load_dotenv()

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

async def analyze_plant_image(image_bytes):
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        completion = await client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "As a plant analysis expert, please analyze this plant image and provide:\n1. Plant identification\n2. Care tips\n3. Health assessment"
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ]
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Error in analyze_plant_image: {e}")
        raise