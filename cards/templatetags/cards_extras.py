"""Filtres cartes : nationalité + drapeau, garde anti-QID."""

from django import template

from cards import country_flags

register = template.Library()


@register.filter(name="country_display")
def country_display(value):
    """« 🇫🇷 France » ; chaîne vide si QID/vide. Jamais de QID affiché."""
    return country_flags.country_display(value)


@register.filter(name="is_qid")
def is_qid(value):
    """True si la valeur ressemble à un QID Wikidata (donnée non résolue)."""
    return country_flags.is_qid(value)


@register.filter(name="flag_img_url")
def flag_img_url(value):
    """URL FlagCDN du drapeau pour une nationalité FR, '' si inconnue."""
    return country_flags.flag_img_url(value)
