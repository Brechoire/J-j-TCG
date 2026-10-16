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

    def test_card_type_label(self):
        from collection.models import Collection

        assert Collection(
            name="X", slug="x", import_config={"card_type": "Stade"}
        ).card_type_label == "Stade"
        assert Collection(
            name="X",
            slug="x",
            import_config={"instance_of": "Q5", "occupation_qid": "Q628099"},
        ).card_type_label == "Entraîneur"
        assert Collection(
            name="X",
            slug="x",
            import_config={"instance_of": "Q483110", "occupation_qid": None},
        ).card_type_label == "Stade"
        assert Collection(name="X", slug="x").card_type_label == "Foot"
