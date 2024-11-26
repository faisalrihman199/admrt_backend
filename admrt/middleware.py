class LogRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Print request details to console
        self.print_request(request)

        # Call the next middleware or view
        response = self.get_response(request)

        return response

    def print_request(self, request):
        pass
        # Print useful information like method, path, and IP address
        # print(f"Request Method: {request.method}, Path: {request.path}")