from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .models import Order

def _send_email(subject, html_template, text_template, context, recipient):
    """
    Envía un email HTML y texto plano.
    """

    html_content = render_to_string(html_template, context)

    text_content = render_to_string(text_template, context)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient],
    )

    email.attach_alternative(html_content, "text/html")

    email.send()


def send_order_confirmation(order):

    _send_email(
        subject=f"Pedido #{order.id} recibido",
        html_template="emails/order_confirmation.html",
        text_template="emails/order_confirmation.txt",
        context={"order": order},
        recipient=order.customer_email,
    )


def send_order_status_email(order):

    status_messages = {

        Order.Status.CONFIRMED:
            "Tu pedido ha sido confirmado.",

        Order.Status.PREPARING:
            "Estamos preparando tu pedido.",

        Order.Status.SHIPPED:
            "Tu pedido ya ha sido enviado.",

        Order.Status.DELIVERED:
            "Tu pedido ha sido entregado. ¡Esperamos que lo disfrutes!",

        Order.Status.CANCELLED:
            "Tu pedido ha sido cancelado.",

    }

    _send_email(

        subject=f"Actualización del pedido #{order.id}",

        html_template="emails/order_status.html",

        text_template="emails/order_status.txt",

        context={
            "order": order,
            "status_message": status_messages.get(
                order.status,
                "El estado del pedido ha cambiado.",
            ),
        },

        recipient=order.customer_email,

    )