class APIException(Exception):

    """Base exception class for the Booker API error message exceptions."""

    def __init__(self, error_code, message, field='', response=None):
        super(APIException, self).__init__()
        self.error_code = error_code
        self.message = message
        self.field = field
        self.response = response
