from testwithirods.proxies import ProxyController


class BatonProxyController(ProxyController):
    """
    Controller for baton proxy binaries that execute baton commands in a transparent Docker container.
    """
    _BATON_BINARIES = {"baton", "baton-metaquery", "baton-get", "baton-chmod", "baton-list", "baton-metamod",
                       "baton-specificquery"}

    def create_proxy_binaries(self) -> str:
        container_directory = self._create_temp_container_directory("baton-proxies-")
        for binary in BatonProxyController._BATON_BINARIES:
            self._create_proxy(container_directory, binary)
        return container_directory
