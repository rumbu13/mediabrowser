#   ---------------------------------------------------------------------------------
#   Copyright (c) Microsoft Corporation. All rights reserved.
#   Licensed under the MIT License. See LICENSE in project root for information.
#   ---------------------------------------------------------------------------------
"""This is a sample python file for testing functions from the source code."""

import json
import random
import pytest
from mediabrowser.discovery import DiscoveredServer, ServerType, discover
import socket

from conftest import load_fixture


@pytest.fixture
def server_nossl(discovery_data):
    return discovery_data["server_nossl"]


@pytest.fixture
def server_ssl(discovery_data):
    return discovery_data["server_ssl"]


@pytest.fixture
def server_without_id(discovery_data):
    return discovery_data["server_without_id"]


@pytest.fixture
def server_without_address(discovery_data):
    return discovery_data["server_without_address"]


def test_server_nossl(server_nossl):
    server = DiscoveredServer(server_nossl["data"], server_nossl["type"])
    assert server.name == "name1"
    assert server.host == "server1"
    assert server.port == 1
    assert not server.use_ssl
    assert server.type == ServerType.EMBY


def test_server_ssl(server_ssl):
    server = DiscoveredServer(server_ssl["data"], server_ssl["type"])
    assert server.name == "name2"
    assert server.host == "server2"
    assert server.port == 2
    assert server.use_ssl
    assert server.type == ServerType.JELLYFIN


def test_server_without_id(server_without_id):
    server = DiscoveredServer(server_without_id["data"], server_without_id["type"])
    with pytest.raises(KeyError):
        _ = server.id


def test_server_without_address(server_without_address):
    server = DiscoveredServer(server_without_address["data"], server_without_address["type"])
    with pytest.raises(KeyError):
        _ = server.address


class MonkeySocket:
    def __init__(self, a, b, c):
        data = load_fixture("discovery")
        self.serverdata = [bytes(json.dumps(data[server_key]["data"]), "utf-8") for server_key in data]

    def setsockopt(self, a, b, c):
        pass

    def settimeout(self, a):
        pass

    def bind(self, a):
        pass

    def sendto(self, a, b):
        pass

    def recv(self, a):
        return random.choice(self.serverdata)

    def close(self):
        pass


def socket_get(a, b, c):
    return MonkeySocket(a, b, c)


def test_random_discovery(monkeypatch):
    with monkeypatch.context() as m:
        m.setattr(socket, "socket", socket_get)
        for _ in range(1, 5):
            discoveries = discover()
            for discovery in discoveries:
                _ = discovery.id
                _ = discovery.address
    pass
