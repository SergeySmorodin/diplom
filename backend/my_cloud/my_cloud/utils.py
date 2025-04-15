from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        if 'detail' in response.data:
            return Response(
                {"message": response.data['detail']},
                status=response.status_code
            )        
        else:
            errors = []
            for field, messages in response.data.items():
                errors.extend(messages)
            return Response(
                {"message": " ".join(errors)},
                status=response.status_code
            )
    
    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {"message": "Объект не найден"},
            status=404
        )

    return Response(
        {"message": "Произошла ошибка сервера"},
        status=500
    )