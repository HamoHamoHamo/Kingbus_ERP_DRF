

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