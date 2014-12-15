from service import BookerCustomerClient


class BookerMiddleware(object):

    def process_request(self, request):
        request.session['client'] = request.session.get('client', BookerCustomerClient())
