import re


def only_numbers(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\D", "", value)


def is_valid_brazilian_phone(phone: str | None) -> bool:
    phone = only_numbers(phone)

    if len(phone) not in [10, 11]:
        return False

    if len(set(phone)) == 1:
        return False

    fake_numbers = {
        "0000000000",
        "9999999999",
        "00000000000",
        "99999999999",
        "1234567890",
        "12345678901",
        "0123456789",
        "01234567890",
    }

    if phone in fake_numbers:
        return False

    if len(phone) == 11 and phone[2] != "9":
        return False

    return True