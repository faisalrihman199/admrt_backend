from django.conf import settings


def generate_username_from_email(email: str):
    return email.strip().lower().replace('@', '_')

def get_profile_image_url(img):
    img = str(img)
    if img is not None and img != "":
        return f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{img}"
    else:
        return None
    