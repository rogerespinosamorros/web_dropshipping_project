from django.core.management.base import BaseCommand

from store.category_mapping import ROOT_MAPPING
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

            if not main:
                continue

            try:
                category.main_category = MainCategory.objects.get(name=main)
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

        unmapped = Category.objects.filter(
            parent__isnull=True,
            main_category__isnull=True,
        ).count()

        self.stdout.write(
            self.style.WARNING(
                f"{unmapped} categorías raíz sin clasificar."
            )
        )