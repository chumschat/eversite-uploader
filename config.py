import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self
import nekoton as nt


class Configuration(BaseModel):
    seed_phrase: str = Field(..., min_length=1)
    site_address: str = Field(..., min_length=1)
    domain_address: str = Field(..., min_length=1)
    gql_transport: str
    jrpc_transport: str

    @model_validator(mode="after")
    def check_model(self) -> Self:
        if not nt.Address.validate(self.site_address):
            raise ValueError("Invalid site address is provided in environment!")
        if not nt.Address.validate(self.domain_address):
            raise ValueError("Invalid domain address is provided in environment!")
        return self

    async def get_transport(self) -> nt.Transport:
        if self.gql_transport:
            transport = nt.GqlTransport([self.gql_transport])
            await transport.check_connection()
            return transport
        elif self.jrpc_transport:
            transport = nt.JrpcTransport(endpoint=self.jrpc_transport)
            await transport.check_connection()
            return transport
        else:
            raise ValueError("No valid transport is provided in environment!")

    def get_keypair(self) -> nt.KeyPair:
        seed = nt.Bip39Seed(self.seed_phrase)
        return seed.derive()


def load_config() -> Configuration:
    load_dotenv()
    return Configuration(
        seed_phrase=os.getenv("SEED_PHRASE"),
        site_address=os.getenv("SITE_ADDRESS"),
        domain_address=os.getenv("DOMAIN_ADDRESS"),
        gql_transport=os.getenv("GQL_TRANSPORT", ""),
        jrpc_transport=os.getenv("JRPC_TRANSPORT", "")
    )
