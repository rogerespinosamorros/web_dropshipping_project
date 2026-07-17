from logging import root
from unicodedata import category, name

from django.utils import text

from store.category_mapping import ROOT_MAPPING
from django.core.management.base import BaseCommand
from store.models import Category, MainCategory

def get_root_category(category):

    current = category

    while current.parent is not None:
        current = current.parent

    return current


class Command(BaseCommand):

    help = "Asigna automáticamente las categorías principales."

    def handle(self, *args, **options):

        assigned = 0

        for category in Category.objects.all():

            root = get_root_category(category)

            main = ROOT_MAPPING.get(root.name.strip())
            name = category.name.lower()

            parent = (
                category.parent.name.lower()
                if category.parent
                else ""
            )

            text = f"{parent} {name}"

            if main is None:

                if any(word in text for word in [
                    "riego",
                    "gotero",
                    "tubería",
                    "tuberia",
                    "manguera",
                    "programador",
                    "pulverizador",
                    "regadera",
                    "difusor",
                    "bomba",
                ]):
                    main = "Riego"

            elif any(word in text for word in [
                "led",
                "lec",
                "bombilla",
                "reflector",
                "balastro",
                "portalámpara",
                "portalampara",
                "luminaria",
                "fluorescente",
                "halogenuro",
                "sodio",
                "temporizador",
            ]):
                main = "Iluminación"

            elif any(word in text for word in [
                "fertilizante",
                "abono",
                "bio",
                "nutriente",
            ]):
                main = "Fertilizantes"

            elif any(word in text for word in [
                "maceta",
                "bandeja",
                "plato",
                "propagador",
                "air pot",
                "air-pot",
                "rejilla",
                "roll tray",
                "jiffy",
            ]):
                main = "Macetas y Bandejas"

            elif any(word in text for word in [
                "sustrato",
                "coco",
                "lana de roca",
                "tierra",
                "perlita",
                "vermiculita",
            ]):
                main = "Sustratos"

            if main:

                try:

                    category.main_category = MainCategory.objects.get(
                        name=main
                    )

                    category.save(update_fields=["main_category"])

                    assigned += 1

                except MainCategory.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No existe MainCategory: {main}"
                        )
                    )


        self.stdout.write(
            self.style.SUCCESS(
                f"{assigned} categorías asignadas."
            )
        )