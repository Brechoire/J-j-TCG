"""Drapeaux de nationalité + garde anti-QID (affichage cartes)."""

FR = "\U0001f1eb\U0001f1f7"
NL = "\U0001f1f3\U0001f1f1"


def test_country_display_france():
    from cards.country_flags import country_display

    assert country_display("France") == f"{FR} France"


def test_country_display_wikidata_label():
    from cards.country_flags import country_display

    out = country_display("Royaume des Pays-Bas")
    assert out == f"{NL} Royaume des Pays-Bas"


def test_country_display_qid_never_leaks():
    from cards.country_flags import country_display

    assert country_display("Q142") == ""
    assert country_display("Q29999") == ""
    assert country_display("") == ""
    assert country_display(None) == ""


def test_country_display_unknown_country_keeps_label():
    from cards.country_flags import country_display

    # État historique sans drapeau : libellé seul, jamais vide.
    assert country_display("Tchécoslovaquie") == "Tchécoslovaquie"


def test_is_qid():
    from cards.country_flags import is_qid

    assert is_qid("Q27") is True
    assert is_qid("France") is False
    assert is_qid("") is False


def test_flag_img_url():
    from cards.country_flags import flag_img_url

    assert flag_img_url("France") == "https://flagcdn.com/w40/fr.png"
    assert flag_img_url("Royaume des Pays-Bas") == "https://flagcdn.com/w40/nl.png"
    assert flag_img_url("Q142") == ""
    assert flag_img_url("") == ""
    # Subdivisions sans code ISO : pas d'URL FlagCDN.
    assert flag_img_url("Angleterre") == ""


def _unsaved_card(nationality):
    from cards.models import Card, Rarity
    from collection.models import Collection
    from encyclopedia.models import EncyclopediaEntity

    col = Collection(name="Football", slug="football")
    ent = EncyclopediaEntity(
        wikidata_id="QX",
        label_fr="Testeur",
        props={"nationality": nationality, "club": ""},
    )
    rar = Rarity(code="common", name="Commune", sale_value=5, order=1)
    return Card(collection=col, entity=ent, rarity=rar)


def test_card_caption_shows_flag_not_qid():
    from django.template.loader import render_to_string

    html = render_to_string(
        "cards/_pk_card.html",
        {
            "card": _unsaved_card("France"),
            "quantity": 1,
            "discovered": True,
            "size": "xs",
            "number": 1,
            "total": 100,
        },
    )
    assert "https://flagcdn.com/w40/fr.png" in html
    assert "Q142" not in html


def test_card_caption_qid_falls_back_without_leak():
    from django.template.loader import render_to_string

    html = render_to_string(
        "cards/_pk_card.html",
        {
            "card": _unsaved_card("Q142"),
            "quantity": 1,
            "discovered": True,
            "size": "xs",
            "number": 1,
            "total": 100,
        },
    )
    assert "Q142" not in html
    assert "Football" in html
