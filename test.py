import requests
url = 'http://localhost:8501/get_chat_history'
response = requests.get(url)
print(response.text)