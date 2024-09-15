def render(status_code, data):
    error_messages = {
        200: "Success",
        400: "Bad request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not found",
        500: "Internal server error",
    }
    if status_code == 200:
        return data
    else:
        return {
            "status": "error",
            "error": {
                "code": status_code,
                "message": error_messages.get(status_code, "Unknown error"),
                "reason": data
            }
        }
 