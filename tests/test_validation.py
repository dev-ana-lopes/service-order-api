from pydantic import ValidationError

from src.domain.validation import is_valid_br_plate, is_valid_cpf_cnpj
from src.presentation.schemas.admin_schema import (
    CustomerCreateRequest,
    VehicleCreateRequest,
)


def test_cpf_and_cnpj_validation_accepts_valid_documents():
    assert is_valid_cpf_cnpj("111.444.777-35") is True
    assert is_valid_cpf_cnpj("04.252.011/0001-10") is True


def test_cpf_and_cnpj_validation_rejects_invalid_documents():
    assert is_valid_cpf_cnpj("111.111.111-11") is False
    assert is_valid_cpf_cnpj("12.345.678/0001-00") is False


def test_plate_validation_accepts_legacy_and_mercosul_formats():
    assert is_valid_br_plate("ABC1234") is True
    assert is_valid_br_plate("BRA2A34") is True


def test_customer_and_vehicle_schemas_normalize_valid_inputs():
    customer = CustomerCreateRequest(
        name="Maria",
        cpf_cnpj="111.444.777-35",
        email="maria@example.com",
        phone="11999999999",
    )
    vehicle = VehicleCreateRequest(
        customer_id="00000000-0000-0000-0000-000000000001",
        brand="Ford",
        model="Ka",
        year=2020,
        plate="bra2a34",
    )

    assert customer.cpf_cnpj == "11144477735"
    assert vehicle.plate == "BRA2A34"


def test_customer_and_vehicle_schemas_reject_invalid_inputs():
    try:
        CustomerCreateRequest(
            name="Maria",
            cpf_cnpj="123",
            email="maria@example.com",
            phone="11999999999",
        )
    except ValidationError as exc:
        assert "Invalid CPF/CNPJ" in str(exc)
    else:
        raise AssertionError("Expected invalid CPF/CNPJ to fail")

    try:
        VehicleCreateRequest(
            customer_id="00000000-0000-0000-0000-000000000001",
            brand="Ford",
            model="Ka",
            year=2020,
            plate="123",
        )
    except ValidationError as exc:
        assert "Invalid vehicle plate" in str(exc)
    else:
        raise AssertionError("Expected invalid plate to fail")
