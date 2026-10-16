import uuid

from django.test import TestCase


def make_pack_world(nationalities=("France", "Brésil"), per_nat=6):
    from cards.models import Card, Rarity
    from collection.models import Collection, Pack
    from encyclopedia.models import EncyclopediaEntity

    col = Collection.objects.create(
        name=f"P {uuid.uuid4().hex[:6]}", slug=f"p-{uuid.uuid4().hex[:8]}", status="active"
    )
    rar, _ = Rarity.objects.get_or_create(
        code="common",
        defaults={
            "name": "Commune",
            "color": "#000",
            "draw_weight": 55,
            "sale_value": 5,
            "order": 1,
        },
    )
    cards = []
    for nat in nationalities:
        for i in range(per_nat):
            ent = EncyclopediaEntity.objects.create(
                wikidata_id=f"QP{uuid.uuid4().hex[:8]}",
                label_fr=f"Joueur {nat} {i}",
                props={"nationality": nat, "club": "Olympique de Marseille"},
            )
            cards.append(Card.objects.create(collection=col, entity=ent, rarity=rar))
    pack = Pack.objects.create(
        collection=col,
        name="Français",
        slug="nationality-francais",
        kind=Pack.Kind.NATIONALITY,
        filter_params={"nationality": "France"},
    )
    return col, pack, cards


class PackMatchingTests(TestCase):
    def test_rule_match_normalized_accents(self):
        from collection.packs import pack_matches_card

        _col, pack, cards = make_pack_world()
        french = [c for c in cards if c.entity.props["nationality"] == "France"]
        brazil = [c for c in cards if c.entity.props["nationality"] == "Brésil"]
        assert all(pack_matches_card(pack, c) for c in french)
        assert not any(pack_matches_card(pack, c) for c in brazil)

    def test_explicit_members_join_without_rule(self):
        from collection.models import Pack
        from collection.packs import pack_matches_card

        col, pack, cards = make_pack_world()
        season = Pack.objects.create(
            collection=col, name="Saison", slug="saison", kind=Pack.Kind.SEASON
        )
        season.cards.add(cards[0])
        assert pack_matches_card(season, cards[0])
        assert not pack_matches_card(season, cards[1])

    def test_pack_counts(self):
        from collection.packs import pack_counts

        col, pack, cards = make_pack_world()
        assert pack_counts([pack], cards) == {pack.pk: 6}

    def test_packs_for_card_multiple(self):
        from collection.models import Pack
        from collection.packs import packs_for_card

        col, pack, cards = make_pack_world()
        om = Pack.objects.create(
            collection=col,
            name="OM",
            slug="club-om",
            kind=Pack.Kind.CLUB,
            filter_params={"club": "Olympique de Marseille"},
        )
        packs = [pack, om]
        found = packs_for_card(cards[0], packs)
        assert {p.pk for p in found} == {pack.pk, om.pk}


class PackDrawTests(TestCase):
    def test_draw_limited_to_pack(self):
        from accounts.models import User
        from boosters.services import BoosterOpeningService

        user = User.objects.create_user(
            username=f"pk_{uuid.uuid4().hex[:8]}",
            email=f"{uuid.uuid4().hex}@ex.com",
            password="x" * 12,
        )
        col, pack, _cards = make_pack_world(per_nat=6)
        opening = BoosterOpeningService().open_free(
            user, col, idempotency_key=uuid.uuid4(), pack=pack
        )
        assert opening.pack_id == pack.pk
        assert opening.cards.count() == 5
        nats = {c.entity.props["nationality"] for c in opening.cards.all()}
        assert nats == {"France"}

    def test_draw_too_small_pack_raises(self):
        from accounts.models import User
        from boosters.services import BoosterOpeningService, NotEnoughCards

        user = User.objects.create_user(
            username=f"pk_{uuid.uuid4().hex[:8]}",
            email=f"{uuid.uuid4().hex}@ex.com",
            password="x" * 12,
        )
        col, pack, _cards = make_pack_world(per_nat=1)
        with self.assertRaises(NotEnoughCards):
            BoosterOpeningService().open_free(user, col, idempotency_key=uuid.uuid4(), pack=pack)


class SyncPacksCommandTests(TestCase):
    def test_sync_creates_nationality_packs(self):
        from django.core.management import call_command

        from collection.models import Pack

        col, _pack, _cards = make_pack_world()
        Pack.objects.all().delete()
        call_command("sync_packs", col.slug)
        packs = Pack.objects.filter(collection=col)
        assert {p.slug for p in packs} == {
            "nationality-france",
            "nationality-bresil",
            "club-olympique-de-marseille",
        }
        assert all(p.is_active for p in packs)

    def test_create_pack_with_qids(self):
        from django.core.management import call_command

        from collection.models import Pack

        col, _pack, cards = make_pack_world()
        qids = [cards[0].entity.wikidata_id, cards[6].entity.wikidata_id]
        call_command(
            "create_pack",
            col.slug,
            "ligue1-2001",
            "Ligue 1 2001-2002",
            kind="season",
            qids=",".join(qids),
        )
        pack = Pack.objects.get(collection=col, slug="ligue1-2001")
        assert pack.cards.count() == 2
