from decimal import Decimal
import csv
import io
from datetime import datetime
from .base import BaseCsvAdapter


class OtpCsvAdapter(BaseCsvAdapter):
    def parse(self):
        text = self.raw_bytes.decode("utf-8-sig", errors="ignore")

        # Try header-based first
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        rows = list(reader)
        if rows and any(k for k in rows[0].keys() if "könyvelés" in k.lower()):
            return self._parse_with_headers(rows)

        # Fallback: headerless OTP (v2)
        reader = csv.reader(io.StringIO(text), delimiter=";", quotechar='"')
        return self._parse_headerless(reader)

    # --- V1 (fejléces OTP) ---
    def _parse_with_headers(self, rows):
        txns = []
        for row in rows:
            try:
                booking_date = self.try_parse_date(
                    row.get("Könyvelés dátuma") or row.get("Könyvelés")
                )
                amount = Decimal(row.get("Összeg", "0").replace(",", "."))
                currency = row.get("Devizanem", "HUF").strip().upper()
                description = row.get("Közlemény", "").strip() or row.get(
                    "Megjegyzés", ""
                )
                counterparty = row.get("Ellenoldal neve", "")

                txns.append(
                    {
                        "user_id": self.user_id,
                        "import_file_id": self.import_id,
                        "booking_date": booking_date,
                        "amount": amount,
                        "currency": currency,
                        "description_raw": description,
                        "counterparty": counterparty,
                    }
                )
            except Exception:
                continue
        return txns

    # --- V2 (headerless OTP) ---
    def _parse_headerless(self, reader):
        txns = []
        for row in reader:
            if not row or len(row) < 10:
                continue
            try:
                txn_type = (row[1] or "").strip().upper()  # <- handles 't'/'j'
                amount = Decimal((row[2] or "0").replace(",", "."))
                if txn_type == "T":
                    amount = -abs(amount)
                elif txn_type == "J":
                    amount = abs(amount)

                currency = (row[3] or "HUF").strip().upper()

                booking_date = self._parse_date_otp_v2(row[4])
                value_date = self._parse_date_otp_v2(row[5])
                counterparty = row[8].strip() if len(row) > 8 else None
                description = row[9].strip() if len(row) > 9 else None
                reference = row[-2].strip() if len(row) > 13 else None

                txns.append(
                    {
                        "user_id": self.user_id,
                        "import_file_id": self.import_id,
                        "booking_date": booking_date,
                        "value_date": value_date,
                        "amount": amount,
                        "currency": currency,
                        "description_raw": description,
                        "counterparty": counterparty,
                        "reference": reference,
                    }
                )
            except Exception:
                continue
        return txns

    def _parse_date_otp_v2(self, raw):
        if not raw:
            return None
        try:
            return datetime.strptime(raw.strip(), "%Y%m%d").date()
        except ValueError:
            return None
