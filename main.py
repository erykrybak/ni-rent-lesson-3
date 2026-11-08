import json
from typing import Dict, List

from pydantic import BaseModel


class Parameters(BaseModel):
    apartments_json_path: str = "data/apartments.json"
    tenants_json_path: str = "data/tenants.json"
    transfers_json_path: str = "data/transfers.json"
    bills_json_path: str = "data/bills.json"


class Room(BaseModel):
    name: str
    area_m2: float


class Apartment(BaseModel):
    key: str
    name: str
    location: str
    area_m2: float
    rooms: Dict[str, Room]

    @staticmethod
    def from_json_file(file_path: str) -> Dict[str, "Apartment"]:
        data = None
        with open(file_path, "r") as file:
            data = json.load(file)
        assert isinstance(data, dict), "Expected a dictionary of apartments"
        return {key: Apartment(**apartment) for key, apartment in data.items()}


class Tenant(BaseModel):
    name: str
    apartment: str
    room: str
    rent_pln: float
    deposit_pln: float
    date_agreement_from: str
    date_agreement_to: str

    @staticmethod
    def from_json_file(file_path: str) -> Dict[str, "Tenant"]:
        data = None
        with open(file_path, "r") as file:
            data = json.load(file)
        assert isinstance(data, dict), "Expected a dictionary of tenants"
        return {key: Tenant(**tenant) for key, tenant in data.items()}


class Transfer(BaseModel):
    amount_pln: float
    date: str
    settlement_year: int | None
    settlement_month: int | None
    tenant: str

    @staticmethod
    def from_json_file(file_path: str) -> List["Transfer"]:
        data = None
        with open(file_path, "r") as file:
            data = json.load(file)
        assert isinstance(data, list), "Expected a list of transfers"
        return [Transfer(**transfer) for transfer in data]


class Bill(BaseModel):
    amount_pln: float
    date_due: str
    apartment: str
    settlement_year: int
    settlement_month: int
    type: str

    @staticmethod
    def from_json_file(file_path: str) -> List["Bill"]:
        data = None
        with open(file_path, "r") as file:
            data = json.load(file)
        assert isinstance(data, list), "Expected a list of bills"
        return [Bill(**bill) for bill in data]


class TenantSettlement(BaseModel):
    tenant: Tenant
    flat: Apartment
    settlement_year: int
    settlement_month: int

    rent: int
    bills: int
    transfers_sum: float = 0.0

    @property
    def total(self) -> float:
        return self.rent + self.bills

    @property
    def balance(self) -> float:
        return self.transfers_sum - self.total


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []

        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)


class ApartmentSettlement(BaseModel):
    apartment_name: str
    settlement_year: int
    settlement_month: int
    total_bills: float
    total_rent: float
    total_transfers: float
    remaining_amount: float

    @staticmethod
    def calculate(manager: "Manager", apartment_name: str, year: int, month: int):
        bills = [
            b
            for b in manager.bills
            if b.apartment == apartment_name
            and b.settlement_year == year
            and b.settlement_month == month
        ]
        total_bills = sum(b.amount_pln for b in bills)

        apartment_tenants = [
            t for t in manager.tenants.values() if t.apartment == apartment_name
        ]
        total_rent = sum(t.rent_pln for t in apartment_tenants)

        tenant_names = {t.name for t in apartment_tenants}
        transfers = [
            tr
            for tr in manager.transfers
            if tr.tenant in tenant_names
            and tr.settlement_year == year
            and tr.settlement_month == month
        ]
        total_transfers = sum(tr.amount_pln for tr in transfers)

        total_due = total_bills + total_rent
        remaining_amount = total_due - total_transfers

        return ApartmentSettlement(
            apartment_name=apartment_name,
            settlement_year=year,
            settlement_month=month,
            total_bills=total_bills,
            total_rent=total_rent,
            total_transfers=total_transfers,
            remaining_amount=remaining_amount,
        )


if __name__ == "__main__":
    parameters = Parameters()
    manager = Manager(parameters)

    for apartment in manager.apartments.values():
        print(apartment.key, apartment.name, apartment.location, apartment.area_m2)
        for room in apartment.rooms.values():
            print(" - ", room.name, room.area_m2)

        for bill in manager.bills:
            if bill.apartment == apartment.key:
                print(
                    " - ",
                    bill.amount_pln,
                    bill.date_due,
                    bill.settlement_year,
                    bill.settlement_month,
                    bill.type,
                )

    for tenant in manager.tenants.values():
        print(
            tenant.name,
            tenant.apartment,
            tenant.room,
            tenant.rent_pln,
            tenant.deposit_pln,
            tenant.date_agreement_from,
            tenant.date_agreement_to,
        )
        for transfer in manager.transfers:
            if transfer.tenant == tenant.name:
                print(
                    "  ",
                    transfer.amount_pln,
                    transfer.date,
                    transfer.settlement_year,
                    transfer.settlement_month,
                )
