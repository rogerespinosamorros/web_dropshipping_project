from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_order_confirmation(order):

    subject = f"Pedido #{order.id} recibido"

    html_content = render_to_string(
        "emails/order_confirmation.html",
        {
            "order": order,
        },
    )

    text_content = render_to_string(
        "emails/order_confirmation.txt",
        {
            "order": order,
        },
    )
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.customer_email],
    )

    email.attach_alternative(
        html_content,
        "text/html",
    )

    email.send()