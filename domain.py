import nekoton as nt
from typing import Optional


class Domain:

    def __init__(self, transport: nt.Transport, address: nt.Address):
        self._address = address
        self._transport = transport

        with open("abi/domain.abi.json") as f:
            domain_abi_text = f.read()
            domain_abi = nt.ContractAbi(domain_abi_text)

        self._getInfo = domain_abi.get_function("getInfo")
        assert self._getInfo is not None
        self._setRecord = domain_abi.get_function("setRecord")
        assert self._setRecord is not None

    async def _get_account_state(self) -> Optional[nt.AccountState]:
        return await self._transport.get_account_state(self._address)

    async def get_info(self) -> Optional[dict]:
        state = await self._get_account_state()

        if state is None:
            return None
        else:
            return self._getInfo.call(state, input={'answerId': 0}).output
        
    async def get_set_record_body(self, record_key: int, content: nt.Cell) -> nt.Cell:
        input_params = {"key": record_key, "value": content}
        return self._setRecord.encode_internal_input(input_params)
