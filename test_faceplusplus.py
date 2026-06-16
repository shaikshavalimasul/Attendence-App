import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FACEPP_API_KEY")
API_SECRET = os.getenv("FACEPP_API_SECRET")

url = "https://api-us.faceplusplus.com/facepp/v3/compare"

data = {
    "api_key": API_KEY,
    "api_secret": API_SECRET,
    "image_url1": "https://cdn.siasat.com/wp-content/uploads/2023/02/shahrukhkhan.jpg",
    "image_url2": "https://tse2.mm.bing.net/th/id/OIP.VwRg5xKBhG1eKmfcSoPg-QHaFU?pid=Api&P=0&h=180"
}

response = requests.post(url, data=data)
result = response.json()

print(result)

if "confidence" in result:
    confidence = result["confidence"]

    print("Confidence:", confidence)

    if confidence > 80:
        print("Same person")
    else:
        print("Different person")
else:
    print("Error:", result)