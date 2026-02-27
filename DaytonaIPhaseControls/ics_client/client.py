import requests

class ICS_Client:
    def __init__(self, base_url, timeout = 10):
        self.base_url = base_url
        self.timeout = timeout
        self.token = None

        self.headers = {
            'Content-Type': 'application/json'
        }

    def send_request(self, endpoint, port, method='GET', data=None):
        url = f"http://{self.base_url}:{port}/{endpoint}"
        print(url)
        try:
            if method == 'GET':
                params = {'channels': data}
                response = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=self.headers, timeout=self.timeout)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=self.headers, timeout=self.timeout)
            else:
                raise ValueError("Unsupported HTTP method")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None