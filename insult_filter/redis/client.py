import requests

filter_url = "http://localhost:9001/filter"
response = requests.post(filter_url, json={"text": "You are a nincompoop and an idiot!"})
print("Filtered text:", response.json())

get_url = "http://localhost:9001/get_results"
print("All filtered results:", requests.get(get_url).json())
