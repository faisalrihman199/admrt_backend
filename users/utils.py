from rest_framework import status
from rest_framework.response import Response


def object_is_not_related(cls, attribute: str):
    
    if not hasattr(cls, attribute):
        return Response(status=status.HTTP_403_FORBIDDEN, data={"details": "wrong profile element"})
    return


# For S3
def change_filename(instance, filename):
    return filename
