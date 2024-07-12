from rest_framework.response import Response


def error_response(error: str, status: int, data=None):
    resp_data = {
        "error": error
    }
    if data:
        resp_data["object"] = data
    return Response(
        data=resp_data, status=status
    )


def success_response(message: str, status: int, data=None):
    resp_data = {"message": message}
    if data:
        resp_data["object"] = data

    return Response(
        data=resp_data, status=status
    )
