from ingestion.models import Rule
from ingestion.categories.factory import seed_default_categories


def seed_default_rules(user_id: str):
    """
    Alapértelmezett szabályok új felhasználókhoz (hu).
    """
    categories = seed_default_categories(user_id)

    default_rules = [
        # --- Bevétel ---
        {
            "name": "Fizetés",
            "match_type": "contains",
            "match_value": "fizetés",
            "cat": "Fizetés és bér",
        },
        {
            "name": "Munkahelyi utalás",
            "match_type": "contains",
            "match_value": "bt.",
            "cat": "Fizetés és bér",
        },
        {
            "name": "Revolut bejövő",
            "match_type": "contains",
            "match_value": "revolut",
            "cat": "Átutalások (bejövő)",
        },
        {
            "name": "Wise bejövő",
            "match_type": "contains",
            "match_value": "wise",
            "cat": "Átutalások (bejövő)",
        },
        {
            "name": "Kamatjóváírás",
            "match_type": "contains",
            "match_value": "kamat",
            "cat": "Kamat / Befektetési bevétel",
        },
        # --- Élelmiszer és étkezés ---
        {
            "name": "Lidl",
            "match_type": "contains",
            "match_value": "lidl",
            "cat": "Bevásárlás",
        },
        {
            "name": "Spar",
            "match_type": "contains",
            "match_value": "spar",
            "cat": "Bevásárlás",
        },
        {
            "name": "Tesco",
            "match_type": "contains",
            "match_value": "tesco",
            "cat": "Bevásárlás",
        },
        {
            "name": "Penny",
            "match_type": "contains",
            "match_value": "penny",
            "cat": "Bevásárlás",
        },
        {
            "name": "McDonald’s",
            "match_type": "contains",
            "match_value": "mcdonald",
            "cat": "Étterem és kávézó",
        },
        {
            "name": "Wolt",
            "match_type": "contains",
            "match_value": "wolt",
            "cat": "Étterem és kávézó",
        },
        {
            "name": "Bolt Food",
            "match_type": "contains",
            "match_value": "bolt food",
            "cat": "Étterem és kávézó",
        },
        {
            "name": "Starbucks",
            "match_type": "contains",
            "match_value": "starbucks",
            "cat": "Étterem és kávézó",
        },
        # --- Előfizetések ---
        {
            "name": "Netflix",
            "match_type": "contains",
            "match_value": "netflix",
            "cat": "Előfizetések",
        },
        {
            "name": "Spotify",
            "match_type": "contains",
            "match_value": "spotify",
            "cat": "Előfizetések",
        },
        {
            "name": "YouTube Premium",
            "match_type": "contains",
            "match_value": "youtube",
            "cat": "Előfizetések",
        },
        {
            "name": "Apple szolgáltatások",
            "match_type": "contains",
            "match_value": "apple",
            "cat": "Előfizetések",
        },
        # --- Szórakozás ---
        {
            "name": "Steam",
            "match_type": "contains",
            "match_value": "steam",
            "cat": "Szórakozás",
        },
        {
            "name": "Mozi / Jegy",
            "match_type": "contains",
            "match_value": "mozi",
            "cat": "Szórakozás",
        },
        # --- Közlekedés ---
        {
            "name": "BKK / tömegközlekedés",
            "match_type": "contains",
            "match_value": "bkk",
            "cat": "Közlekedés",
        },
        {
            "name": "Parkolás",
            "match_type": "contains",
            "match_value": "parkolás",
            "cat": "Közlekedés",
        },
        {
            "name": "MOL töltés",
            "match_type": "contains",
            "match_value": "mol",
            "cat": "Közlekedés",
        },
        {
            "name": "Bolt / Uber utazás",
            "match_type": "contains",
            "match_value": "uber",
            "cat": "Közlekedés",
        },
        # --- Vásárlás ---
        {
            "name": "Zara",
            "match_type": "contains",
            "match_value": "zara",
            "cat": "Ruházat és vásárlás",
        },
        {
            "name": "H&M",
            "match_type": "contains",
            "match_value": "h&m",
            "cat": "Ruházat és vásárlás",
        },
        {
            "name": "Decathlon",
            "match_type": "contains",
            "match_value": "decathlon",
            "cat": "Ruházat és vásárlás",
        },
        {
            "name": "Amazon",
            "match_type": "contains",
            "match_value": "amazon",
            "cat": "Ruházat és vásárlás",
        },
        {
            "name": "MediaMarkt",
            "match_type": "contains",
            "match_value": "mediamarkt",
            "cat": "Elektronika",
        },
        {
            "name": "IKEA",
            "match_type": "contains",
            "match_value": "ikea",
            "cat": "Otthon és rezsi",
        },
        # --- Szolgáltatók ---
        {
            "name": "E.ON",
            "match_type": "contains",
            "match_value": "e.on",
            "cat": "Otthon és rezsi",
        },
        {
            "name": "MVM",
            "match_type": "contains",
            "match_value": "mvm",
            "cat": "Otthon és rezsi",
        },
        {
            "name": "Telekom",
            "match_type": "contains",
            "match_value": "telekom",
            "cat": "Otthon és rezsi",
        },
        {
            "name": "Vodafone",
            "match_type": "contains",
            "match_value": "vodafone",
            "cat": "Otthon és rezsi",
        },
        {
            "name": "Biztosítás",
            "match_type": "contains",
            "match_value": "biztosító",
            "cat": "Biztosítás és egészség",
        },
        {
            "name": "Gyógyszertár",
            "match_type": "contains",
            "match_value": "gyógyszertár",
            "cat": "Biztosítás és egészség",
        },
        {
            "name": "Klinika / Fogorvos",
            "match_type": "contains",
            "match_value": "klinika",
            "cat": "Biztosítás és egészség",
        },
        # --- Lakhatás ---
        {
            "name": "Lakbér",
            "match_type": "amount_range",
            "match_value": "-400000,-100000",
            "cat": "Lakhatás és bérlés",
        },
        {
            "name": "Közös költség",
            "match_type": "contains",
            "match_value": "közös költség",
            "cat": "Lakhatás és bérlés",
        },
        # --- Oktatás ---
        {
            "name": "Egyetem / tandíj",
            "match_type": "contains",
            "match_value": "egyetem",
            "cat": "Oktatás és könyvek",
        },
        {
            "name": "Könyv",
            "match_type": "contains",
            "match_value": "book",
            "cat": "Oktatás és könyvek",
        },
        # --- Utazás ---
        {
            "name": "Ryanair repülőjegy",
            "match_type": "contains",
            "match_value": "ryanair",
            "cat": "Utazás",
        },
        {
            "name": "Szállás / Airbnb",
            "match_type": "contains",
            "match_value": "airbnb",
            "cat": "Utazás",
        },
        {
            "name": "Booking.com",
            "match_type": "contains",
            "match_value": "booking.com",
            "cat": "Utazás",
        },
        # --- Megtakarítás / befektetés ---
        {
            "name": "Megtakarítási utalás",
            "match_type": "contains",
            "match_value": "megtakarítás",
            "cat": "Megtakarítások és befektetések",
        },
        {
            "name": "Értékpapír számla",
            "match_type": "contains",
            "match_value": "értékpapír",
            "cat": "Megtakarítások és befektetések",
        },
    ]

    created = 0
    for idx, rule in enumerate(default_rules, start=1):
        category_obj = categories[rule["cat"]]
        _, created_flag = Rule.objects.get_or_create(
            user_id=user_id,
            name=rule["name"],
            defaults={
                "priority": idx,
                "enabled": True,
                "match_type": rule["match_type"],
                "match_value": rule["match_value"],
                "action_set_category": str(category_obj.id),
            },
        )
        if created_flag:
            created += 1

    return created
