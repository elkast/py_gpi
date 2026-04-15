# gpi/utils/network.py
"""Détection de l'adresse IP réseau locale.

Conservé de la v0.1 — permet de tester l'API depuis un mobile sur le même réseau Wi-Fi.
"""

import socket


def detecter_ip() -> str:
    """Détecte l'adresse IP locale de la machine.

    Ne nécessite pas de connexion internet — utilise socket.gethostbyname().

    Returns:
        Adresse IP locale (ex: "192.168.1.42"), ou "127.0.0.1" en cas d'échec
    """
    try:
        # Connexion UDP fictive pour obtenir l'IP locale
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"
