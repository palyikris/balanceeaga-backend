from .adapters.otp_csv import OtpCsvAdapter
from .adapters.revolut_csv import RevolutCsvAdapter


def get_adapter(adapter_hint: str, source_hint: str):
    if adapter_hint == "csv" and source_hint == "otp":
        return OtpCsvAdapter
    if adapter_hint == "csv" and source_hint == "revolut":
        return RevolutCsvAdapter
    raise ValueError(
        f"Unsupported adapter/source combination: {adapter_hint}, {source_hint}"
    )
