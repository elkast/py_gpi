"""Tests unitaires – Détection réseau."""
from gpi.core.network import detecter_ips


class TestNetwork:
    def test_retourne_liste(self):
        """La fonction retourne toujours une liste."""
        result = detecter_ips()
        assert isinstance(result, list)

    def test_pas_loopback(self):
        """Aucune IP loopback dans les résultats."""
        for ip in detecter_ips():
            assert not ip.startswith("127.")
            assert not ip.startswith("169.254.")

    def test_ips_uniques(self):
        """Pas de doublons dans les IPs."""
        ips = detecter_ips()
        assert len(ips) == len(set(ips))

    def test_format_ip(self):
        """Chaque IP a un format valide (4 octets)."""
        for ip in detecter_ips():
            parts = ip.split(".")
            assert len(parts) == 4
            for p in parts:
                assert 0 <= int(p) <= 255
