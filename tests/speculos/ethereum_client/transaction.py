from io import BytesIO
from typing import Union

from ethereum_client.utils import (read, read_uint, read_varint,
                                      write_varint, UINT64_MAX)


class TransactionError(Exception):
    pass

EIP2930 = 1
EIP1559 = 2

# e0 + 08 + 00 + 00 + 38 + 05 + 8000002c 8000003c 80000000 00000000 00000000 + 0000001f + 4578616d706c652060706572736f6e616c5f7369676e60206d657373616765
# E0 + 08 + 00 + 00 + 34 + 05 + 8000002C 8000003C 80000000 00000000 00000000 + 4578616D706C652060706572736F6E616C5F7369676E60206D657373616765
# E0   08   00   00   35058000002C8000003C8000000000000000000000001F4578616D706C652060706572736F6E616C5F7369676E60206D657373616765

class PersonalTransaction:
    def __init__(self, msg: Union[str, bytes]) -> None:
        # If you want to send bytes directly you have to put "0x" before the string
        if msg[0:2] == "0x":
            self.msg: bytes = bytes.fromhex(msg[2:])
        else:
            self.msg: bytes = bytes(msg, "utf-8")

    def serialize(self) -> bytes:
        return b"".join([
            len(self.msg).to_bytes(4, byteorder="big"),
            self.msg,
        ])

class Transaction:
    def __init__(self, txType: int, nonce: int, gasPrice: int, gasLimit: int, to: Union[str, bytes], value: int, data: Union[str, bytes] = "", chainID: int = -1) -> None:
        self.txType: int = txType
        self.nonce: int = nonce
        self.gasPrice: int = gasPrice
        self.gasLimit: int = gasLimit
        self.to: bytes = bytes.fromhex(to[2:]) if isinstance(to, str) else to
        self.value: int = value
        self.data: bytes = bytes(data, "utf-8")
        self.chainID = b''

        if not (0 <= self.nonce <= UINT64_MAX):
            raise TransactionError(f"Bad nonce: '{self.nonce}'!")

        if not (0 <= self.value <= UINT64_MAX):
            raise TransactionError(f"Bad value: '{self.value}'!")

        if len(self.to) != 20:
            raise TransactionError(f"Bad address: '{self.to}'!")

        self.lenNonce = int((len(hex(self.nonce)) - 1) / 2)
        self.lenGP = int((len(hex(self.gasPrice)) - 1) / 2)
        self.lenGL = int((len(hex(self.gasLimit)) - 1) / 2)
        self.lenValue = int((len(hex(self.value)) - 1) / 2)

        self.lenChainID = int((len(hex(chainID)) - 1) / 2)

        if chainID != -1:
            self.chainID = b"".join([
                b'' if self.lenChainID == 1 else (self.lenChainID + 0x80).to_bytes(1, byteorder="big"),
                chainID.to_bytes(self.lenChainID, byteorder="big"),
                write_varint(0 + 0x80),
                write_varint(0 + 0x80),
            ])

    def serialize(self) -> bytes:
        return b"".join([
            self.txType.to_bytes(1, byteorder="big"),

            b'' if self.lenNonce == 1 else write_varint(self.lenNonce + 0x80),
            self.nonce.to_bytes(self.lenNonce, byteorder="big"),

            write_varint(self.lenGP + 0x80),
            self.gasPrice.to_bytes(self.lenGP, byteorder="big"),

            write_varint(self.lenGL + 0x80),
            self.gasLimit.to_bytes(self.lenGL, byteorder="big"),

            write_varint(len(self.to) + 0x80),
            self.to,

            write_varint(self.lenValue + 0x80),
            self.value.to_bytes(self.lenValue, byteorder="big"),

            write_varint(len(self.data) + 0x80),
            self.data,

            self.chainID,

        ])
