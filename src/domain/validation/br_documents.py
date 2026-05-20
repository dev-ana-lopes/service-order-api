import re


def normalize_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def is_valid_cpf(value: str) -> bool:
    cpf = normalize_digits(value)
    if len(cpf) != 11:
        return False
    if cpf == cpf[0] * 11:
        return False

    def calc_digit(base: str, factor: int) -> str:
        total = sum(int(d) * (factor - i) for i, d in enumerate(base))
        mod = total % 11
        return "0" if mod < 2 else str(11 - mod)

    d1 = calc_digit(cpf[:9], 10)
    d2 = calc_digit(cpf[:10], 11)
    return cpf[-2:] == d1 + d2


def is_valid_cnpj(value: str) -> bool:
    cnpj = normalize_digits(value)
    if len(cnpj) != 14:
        return False
    if cnpj == cnpj[0] * 14:
        return False

    def calc_digit(base: str, weights: list[int]) -> str:
        total = sum(int(d) * w for d, w in zip(base, weights, strict=False))
        mod = total % 11
        return "0" if mod < 2 else str(11 - mod)

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = calc_digit(cnpj[:12], w1)
    d2 = calc_digit(cnpj[:13], w2)
    return cnpj[-2:] == d1 + d2


def is_valid_cpf_cnpj(value: str) -> bool:
    digits = normalize_digits(value)
    if len(digits) == 11:
        return is_valid_cpf(digits)
    if len(digits) == 14:
        return is_valid_cnpj(digits)
    return False


def normalize_plate(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def is_valid_br_plate(value: str) -> bool:
    plate = normalize_plate(value)
    if re.fullmatch(r"[A-Z]{3}[0-9]{4}", plate):
        return True
    # Mercosul: ABC1D23
    if re.fullmatch(r"[A-Z]{3}[0-9][A-Z][0-9]{2}", plate):
        return True
    return False
