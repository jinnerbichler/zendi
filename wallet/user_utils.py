from django.contrib.auth.models import User


def get_user_safe(email):

    try:
        return False, User.objects.get(username=email)
    except User.DoesNotExist:
        pass

    user = User.objects.create_user(username=email, email=email, password='')

    # ToDo create seed and store in object

    return True, user
