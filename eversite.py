import nekoton as nt
from typing import Optional


class EverSite:

    def __init__(self, transport: nt.Transport, address: nt.Address, keypair: nt.KeyPair):
        self._address = address
        self._transport = transport
        self._keypair = keypair

        with open("abi/eversite.abi.json") as f:
            eversite_abi_text = f.read()
            eversite_abi = nt.ContractAbi(eversite_abi_text)

        self._upload = eversite_abi.get_function("upload")
        assert self._upload is not None
        self._getDetails = eversite_abi.get_function("getDetails")
        assert self._getDetails is not None
        self._owner = eversite_abi.get_function("owner")
        assert self._owner is not None

    async def _get_account_state(self) -> Optional[nt.AccountState]:
        return await self._transport.get_account_state(self._address)

    async def get_details(self) -> Optional[nt.ExecutionOutput]:
        state = await self._get_account_state()

        if state is None:
            return None
        else:
            return self._getDetails.call(state, input={})

    async def get_owner(self) -> Optional[nt.PublicKey]:
        state = await self._get_account_state()

        if state is None:
            return None
        else:
            public_key_int = self._owner.call(state, input={}).output["owner"]
            return nt.PublicKey.from_int(public_key_int)
        
    async def build_upload(self, content: nt.Cell, index: int) -> nt.Cell:
        input_params = {"index": index, "part": content}
        return self._upload.encode_internal_input(input_params)

    async def send_chunk(self, content: nt.Cell, index: int) -> nt.Transaction:
        signature_id = await self._transport.get_signature_id()

        external_message = self._upload.encode_external_message(
            self._address,
            input={
                "index": index,
                "part": content
            },
            public_key=self._keypair.public_key
        ).sign(self._keypair, signature_id)

        tx = await self._transport.send_external_message(external_message)
        if tx is None:
            raise RuntimeError("Message expired")
        return tx
