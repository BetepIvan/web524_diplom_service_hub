from django.conf import settings
from django.core.mail import send_mail


def send_register_email(email):
    send_mail(
        subject='Добро пожаловать в Сервис Мастеров!',
        message='Вы успешно зарегистрировались на платформе Сервис Мастеров. Удачи в работе!',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email]
    )


def send_new_password(email, new_password):
    send_mail(
        subject='Вы успешно изменили пароль',
        message=f'Ваш новый пароль: {new_password}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email]
    )


def send_service_creation(email, service_obj):
    send_mail(
        subject='Вы добавили новую услугу',
        message=f'Вы успешно добавили услугу: {service_obj}',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email]
    )
