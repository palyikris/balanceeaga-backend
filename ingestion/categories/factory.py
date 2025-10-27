from ingestion.models import Category


def seed_default_categories(user_id: str):
    """
    Alap kategóriák minden új felhasználónak.
    """
    default_categories = {
        # --- Bevétel ---
        "Fizetés és bér": "income",
        "Átutalások (bejövő)": "income",
        "Kamat / Befektetési bevétel": "income",
        # --- Kiadás ---
        "Bevásárlás": "expense",
        "Étterem és kávézó": "expense",
        "Előfizetések": "expense",
        "Szórakozás": "expense",
        "Közlekedés": "expense",
        "Ruházat és vásárlás": "expense",
        "Elektronika": "expense",
        "Otthon és rezsi": "expense",
        "Biztosítás és egészség": "expense",
        "Lakhatás és bérlés": "expense",
        "Oktatás és könyvek": "expense",
        "Utazás": "expense",
        "Egyéb kiadások": "expense",
        # --- Átvezetés / megtakarítás ---
        "Átvezetések (kimenő)": "transfer",
        "Megtakarítások és befektetések": "transfer",
    }

    created_map = {}
    for name, ctype in default_categories.items():
        category, _ = Category.objects.get_or_create(
            user_id=user_id,
            name=name,
            defaults={"type": ctype},
        )
        created_map[name] = category

    return created_map
