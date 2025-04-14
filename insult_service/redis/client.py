import requests

# Submit an insult using the HTTP endpoint.
url = "http://localhost:8001/add_insult"
response = requests.post(url, json={"insult": "Caca"})
print("Add insult response:", response.json())

# Retrieve stored insults.
get_url = "http://localhost:8001/get_insults"
print("Stored insults:", requests.get(get_url).json())
