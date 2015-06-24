import json
from requests import Request, Session
from django.conf import settings


class BookerRequest(Request):
    """
    Sets up, sends, and processes a single request to the Booker API
    """
    base_url = 'https://app.secure-booker.com/webservice4/json/CustomerService.svc'
    path = None
    method = None
    params = {}
    original_params = None
    needs_user_token = False
    token = None

    def __init__(self, path, token, params={}):
        headers = {'content-type': 'application/json'}
        super(BookerRequest, self).__init__(params=params, headers=headers)
        self.path = path
        if token:
            self.token = token

    def send(self):
        self.url = "%s%s" % (self.base_url, self.path)
        prepped = self.prepare()
        s = Session()
        # print(self.data)
        print(self.url)
        h = s.get_adapter(url)
        h.max_retries = 10
        response = s.send(prepped)
        response.needs_user_token = self.needs_user_token
        response.original_request = self
        return response

    def post(self):
        self.method = 'POST'
        if self.token:
            self.params['access_token'] = self.token
        self.data = json.dumps(self.params)
        self.original_params = self.params
        self.params = None
        # print("post data: %s" % self.data)
        return self.send()

    def put(self):
        self.method = 'PUT'
        if self.token:
            self.params['access_token'] = self.token
        self.data = json.dumps(self.params)
        self.original_params = self.params
        self.params = None
        return self.send()

    def get(self, params=None):
        self.method = 'GET'
        if self.token:
            self.params['access_token'] = self.token
        if params is not None:
            self.params.update(params)
        # print("params in get is %s" % self.params)
        return self.send()

    def delete(self):
        self.method = 'DELETE'
        if self.token:
            self.params['access_token'] = self.token
        self.data = json.dumps(self.params)
        self.original_params = self.params
        self.params = None
        return self.send()


class BookerAuthedRequest(BookerRequest):
    needs_user_token = True


class BookerMerchantRequest(BookerRequest):
    base_url = 'https://app.secure-booker.com/webservice4/json/BusinessService.svc'
