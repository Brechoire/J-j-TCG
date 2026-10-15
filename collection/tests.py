from django.db import IntegrityError
from django.test import TestCase


class CollectionModelTests(TestCase):
    def test_create_collection(self):
        from collection.models import Collection

        col = Collection.objects.create(
            name="Football", slug="football", status="active", display_order=1
        )
        assert col.slug == "football"
        assert str(col) != ""

    def test_slug_unique(self):
        from collection.models import Collection

        Collection.objects.create(name="Football", slug="football")
        with self.assertRaises(IntegrityError):
            Collection.objects.create(name="Autre", slug="football")
