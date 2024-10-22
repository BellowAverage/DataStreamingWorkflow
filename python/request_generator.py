import requests
from fake_useragent import UserAgent

def send_requests():
    proxies = [
        {'http': 'http://hadoop102:3128', 'https': 'http://hadoop102:3128'},
        {'http': 'http://hadoop103:3128', 'https': 'http://hadoop103:3128'},
        {'http': 'http://hadoop104:3128', 'https': 'http://hadoop104:3128'}
    ]
    
    nginx_url = 'http://localhost:80'
    user_agent = UserAgent()

    for proxy in proxies:
        headers = {'User-Agent': user_agent.random}
        try:
            response = requests.get(nginx_url, headers=headers, proxies=proxy)
            print(f"Request sent via proxy {proxy['http']} - Status: {response.status_code}")
        except requests.RequestException as e:
            print(f"Error accessing {nginx_url} via proxy {proxy['http']}: {e}")

if __name__ == '__main__':
    for _ in range(100):
        send_requests()
