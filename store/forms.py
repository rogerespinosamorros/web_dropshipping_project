from django import forms


class CheckoutForm(forms.Form):

    customer_name = forms.CharField(
        label="Nombre completo",
        max_length=200,
    )

    customer_email = forms.EmailField(
        label="Correo electrónico",
    )

    customer_phone = forms.CharField(
        label="Teléfono",
        max_length=30,
        required=False,
    )

    shipping_address = forms.CharField(
        label="Dirección",
        max_length=255,
    )

    shipping_city = forms.CharField(
        label="Ciudad",
        max_length=120,
    )

    shipping_postcode = forms.CharField(
        label="Código postal",
        max_length=20,
    )

    shipping_country = forms.CharField(
        label="País",
        max_length=80,
        initial="España",
    )