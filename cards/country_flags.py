"""Drapeaux des nationalités (P27) — libellé FR → emoji.

Données : libellés FR résolus à l'import (repli QID si échec réseau).
Un QID ou un pays inconnu ne s'affiche JAMAIS (pas de fuite « Q123 »).
Note Windows : les emoji drapeaux s'y affichent en code lettres (« FR »),
vrais drapeaux sur macOS/iOS/Android.
"""

import re
import unicodedata

_QID_RE = re.compile(r"^Q\d+$")


def is_qid(value: str) -> bool:
    return bool(_QID_RE.match((value or "").strip()))


def normalize(name: str) -> str:
    """Minuscules, sans accents, traits d'union → espaces, espaces resserrés."""
    text = unicodedata.normalize("NFD", name or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.lower().replace("-", " ")
    return " ".join(text.split())


# Clés normalisées (sans accents) → ISO alpha-2.
# États historiques sans drapeau actuel : absents volontairement (libellé seul).
COUNTRY_ISO = {
    "france": "FR",
    "allemagne": "DE",
    "allemagne de l'ouest": "DE",  # même drapeau noir-rouge-or
    "argentine": "AR",
    "belgique": "BE",
    "bresil": "BR",
    "cameroun": "CM",
    "coree": "KR",
    "coree du nord": "KP",
    "coree du sud": "KR",
    "espagne": "ES",
    "finlande": "FI",
    "ghana": "GH",
    "inde": "IN",
    "irlande": "IE",
    "islande": "IS",
    "italie": "IT",
    "jamaique": "JM",
    "mali": "ML",
    "mexique": "MX",
    "nouvelle zelande": "NZ",
    "oman": "OM",
    "pologne": "PL",
    "portugal": "PT",
    "danemark": "DK",
    "royaume de danemark": "DK",
    "pays bas": "NL",
    "royaume des pays bas": "NL",
    "hollande": "NL",
    "royaume uni": "GB",
    "grande bretagne": "GB",
    "russie": "RU",
    "republique democratique du congo": "CD",
    "slovenie": "SI",
    "suisse": "CH",
    "suede": "SE",
    "senegal": "SN",
    "tchequie": "CZ",
    "republique tcheque": "CZ",
    "trinite et tobago": "TT",
    "uruguay": "UY",
    "etats unis": "US",
    "etats unis d'amerique": "US",
    "croatie": "HR",
    "serbie": "RS",
    "grece": "GR",
    "turquie": "TR",
    "norvege": "NO",
    "autriche": "AT",
    "hongrie": "HU",
    "roumanie": "RO",
    "ukraine": "UA",
    "maroc": "MA",
    "algerie": "DZ",
    "tunisie": "TN",
    "egypte": "EG",
    "nigeria": "NG",
    "cote d'ivoire": "CI",
    "japon": "JP",
    "australie": "AU",
    "colombie": "CO",
    "chili": "CL",
    "perou": "PE",
    "paraguay": "PY",
    "equateur": "EC",
    "venezuela": "VE",
    "canada": "CA",
    "chine": "CN",
    "afrique du sud": "ZA",
    "luxembourg": "LU",
    "bulgarie": "BG",
    "slovaquie": "SK",
    "costa rica": "CR",
    "panama": "PA",
    "bolivie": "BO",
    "qatar": "QA",
    "cuba": "CU",
    "haiti": "HT",
}

# Nations sans ISO alpha-2 (drapeaux de subdivision, lettres sur Windows).
_SUBDIVISION_FLAGS = {
    "angleterre": "\U0001f3f4\U000e0067\U000e0062\U000e0065\U000e006e\U000e007f",
    "ecosse": "\U0001f3f4\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f",
    "pays de galles": "\U0001f3f4\U000e0067\U000e0062\U000e0077\U000e006c\U000e0073\U000e007f",
}


def flag_emoji(iso: str) -> str:
    """Emoji drapeau depuis un code ISO alpha-2 (ex. 'FR')."""
    iso = (iso or "").strip().upper()
    if len(iso) != 2 or not iso.isalpha():
        return ""
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in iso)


def flag_for_country(label: str) -> str:
    """Emoji drapeau pour un libellé FR de pays, '' si inconnu (repli local)."""
    key = normalize(label)
    if key in _SUBDIVISION_FLAGS:
        return _SUBDIVISION_FLAGS[key]
    return flag_emoji(COUNTRY_ISO.get(key, ""))


def iso_for_country(label: str) -> str:
    """Code ISO alpha-2 pour un libellé FR, '' si inconnu ou sans code (subdivisions)."""
    iso = COUNTRY_ISO.get(normalize(label), "")
    return iso if len(iso) == 2 else ""


def flag_img_url(label: str, width: int = 40) -> str:
    """URL FlagCDN du drapeau (« https://flagcdn.com/w40/fr.png »), '' si inconnu."""
    iso = iso_for_country(label)
    if not iso or width not in (20, 40, 80, 160, 320):
        return ""
    return f"https://flagcdn.com/w{width}/{iso.lower()}.png"


def country_display(value: str) -> str:
    """« 🇫🇷 France » ; '' si vide ou QID. Jamais de QID."""
    label = (value or "").strip()
    if not label or is_qid(label):
        return ""
    flag = flag_for_country(label)
    return f"{flag} {label}".strip() if flag else label
