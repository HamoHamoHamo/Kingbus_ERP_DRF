from rest_framework.response import Response
from rest_framework import status

class StandardResponse:
    @staticmethod
    def get_response(result: bool, data, message, status_code):
        # result는 문자열로 "true" or "false"
        result = 'true' if result else 'false'

        response_data = {
            'result': result,
            'data': data,
            'message': message
        }
        return Response(response_data, status=status_code)


def set_response_false(data, message):
    # {
    #     'result': 'false',
    #     'data': '3',
    #     'message': {
    #         'error' : f"{e}"
    #     }
    # }
    response = {
        'result': 'false',
        'data': data,
        'message': message
    }
    return response

def set_response_true(data, message=""):
    # {
    #     'result': 'true',
    #     'data': estimate_data,
    #     'message': ''
    # }
    response = {
        'result': 'true',
        'data': data,
        'message': message
    }
    return response