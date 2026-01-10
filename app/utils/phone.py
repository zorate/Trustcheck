import phonenumbers
from phonenumbers import NumberParseException

def normalize_phone(phone: str) -> str:
    return "".join(ch for ch in phone if ch.isdigit())


def normalize_phone_number(phone: str, region: str = "NG") -> str:
    """
    Normalize a phone number to E.164 format.
    Defaults to Nigerian numbers.
    """
    try:
        parsed = phonenumbers.parse(phone, region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        else:
            raise ValueError("Invalid phone number")
    except NumberParseException:
        raise ValueError("Unable to parse phone number")


def validate_phone_number(phone: str, region: str = "NG") -> bool:
    """
    Validate a phone number.
    """
    try:
        parsed = phonenumbers.parse(phone, region)
        return phonenumbers.is_valid_number(parsed)
    except NumberParseException:
        return False