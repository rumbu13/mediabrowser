"""Models for MediaBrowser objects"""

from enum import IntEnum
import json
import socket
from urllib.parse import ParseResult, urlparse


class ServerType(IntEnum):
    """Server type"""

    UNKNOWN = 0
    EMBY = 1
    JELLYFIN = 2


class DiscoveredServer:
    """Represents a server found by media browser discovery"""

    def __init__(self, data: dict[str, str], server_type: ServerType) -> None:
        self._data = data
        self._type = server_type
        self._parse_result: ParseResult | None = None

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Return the unique id of the server."""
        return self._data["Id"]

    @property
    def address(self) -> str:
        """Return the address of the server."""
        return self._data["Address"]

    @property
    def name(self) -> str | None:
        """Return the name of the server."""
        return self._data.get("Name")

    @property
    def host(self) -> str:
        """Return the host extracted fro address of the server."""
        self._assure_parse_result()
        return self._parse_result.hostname

    @property
    def port(self) -> int:
        """Return the port extracted fro address of the server."""
        self._assure_parse_result()
        return self._parse_result.port

    @property
    def use_ssl(self) -> bool:
        """Return True if the addres schema uses SS.L"""
        self._assure_parse_result()
        return self._parse_result.scheme == "https"

    @property
    def type(self) -> ServerType:
        """Return the type of the server."""
        return self._type

    def _assure_parse_result(self) -> None:
        if self._parse_result is None:
            self._parse_result = urlparse(self.address)


_DISCOVERY_EMBY = b"who is EmbyServer?"
_DISCOVERY_JELLYFIN = b"who is JellyfinServer?"
_DISCOVERY_MAP = {ServerType.EMBY: _DISCOVERY_EMBY, ServerType.JELLYFIN: _DISCOVERY_JELLYFIN}
_DISCOVERY_TIMEOUT = 1
_DISCOVERY_BROADCAST = "255.255.255.255"
_DISCOVERY_PORT = 7359


def discover() -> list[DiscoveredServer]:
    """Discover available Emby or Jellyfin servers in the local network"""
    result: list[dict[str, str]] = []
    interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
    all_ip_addresses = [ip[-1][0] for ip in interfaces]

    for server_type, message in _DISCOVERY_MAP.items():
        for ip_address in all_ip_addresses:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            try:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(_DISCOVERY_TIMEOUT)
                sock.bind((ip_address, 0))
                sock.sendto(message, (_DISCOVERY_BROADCAST, _DISCOVERY_PORT))
                data = sock.recv(1024)
                discovery = json.loads(data.decode("utf-8"))
                if "Id" in discovery and "Address" in discovery:
                    result.append(DiscoveredServer(discovery, server_type))
            except (TimeoutError, json.JSONDecodeError):
                pass
            finally:
                sock.close()

    return result
