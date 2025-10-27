import csv
import io
import re


class UnknownProfileError(Exception):
    pass


def detect_profile(raw_bytes: bytes) -> str:
    """
    Extended: supports OTP 'headerless' CSV (v2) even if fields are lowercase.
    """
    print("Detecting profile...")

    text = raw_bytes.decode("utf-8-sig", errors="ignore")
    first_2kb = text[:2048]

    # OFX/QIF formátum kizárása
    if first_2kb.lstrip().startswith("<OFX>") or first_2kb.lstrip().upper().startswith(
        "!TYPE:"
    ):
        raise UnknownProfileError("Nem CSV formátumú fájl.")

    # 1) Try header-based CSV (OTP v1 / Revolut)
    sample = io.StringIO(text)
    for delimiter in (";", ","):
        sample.seek(0)
        reader = csv.reader(sample, delimiter=delimiter)
        try:
            headers = next(reader)
        except StopIteration:
            continue
        header_line = " ".join(h.lower().strip() for h in headers)

        # Revolut
        if all(
            k in header_line
            for k in ["completed date", "description", "amount", "currency"]
        ):
            return "Revolut"

        # OTP (v1 with headers)
        if any("könyvelés" in h for h in headers) or "közlemény" in header_line:
            return "OTP"

    # 2) Fallback: OTP v2 headerless — inspect the first parsed row
    sample2 = io.StringIO(text)
    reader2 = csv.reader(sample2, delimiter=";", quotechar='"')
    first_row = next(reader2, None)

    if first_row and len(first_row) >= 6:
        acc = (first_row[0] or "").strip().strip('"')
        typ = (first_row[1] or "").strip().lower()
        amt = (first_row[2] or "").strip()
        curr = (first_row[3] or "").strip().lower()
        d1 = (first_row[4] or "").strip()
        d2 = (first_row[5] or "").strip()

        import re

        if (
            re.fullmatch(r"\d{10,20}", acc)
            and typ in {"t", "j"}
            and re.fullmatch(r"-?\d+(?:[.,]\d+)?", amt)
            and re.fullmatch(r"[a-z]{3}", curr)
            and re.fullmatch(r"\d{8}", d1)
            and re.fullmatch(r"\d{8}", d2)
        ):
            return "OTP"

    # 3) Soft fallbacks
    if "completed date" in first_2kb.lower():
        return "Revolut"
    if "könyvelés dátuma" in first_2kb.lower() or "értéknap" in first_2kb.lower():
        return "OTP"

    print("Nem sikerült profil detektálás.")
    raise UnknownProfileError(
        "Ismeretlen vagy nem támogatott profil (csak OTP és Revolut CSV támogatott)."
    )
