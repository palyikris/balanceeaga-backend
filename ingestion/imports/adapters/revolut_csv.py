from decimal import Decimal
from .base import BaseCsvAdapter


class RevolutCsvAdapter(BaseCsvAdapter):
    def parse(self):
        rows = self.read_csv(delimiter=",")
        txns = []

        for row in rows:
            try:
                booking_date = self.try_parse_date(
                    row.get("Completed Date") or row.get("Date")
                )
                amount = Decimal(row.get("Amount", "0"))
                currency = row.get("Currency", "EUR").strip().upper()
                description = row.get("Description", "").strip()
                counterparty = row.get("Merchant", "") or row.get("Reference", "")

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
