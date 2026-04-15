"""Détection de l'IP locale pour tests réseau."""
import socket


def detecter_ips() -> list[str]:
    """Retourne la liste des IPs locales non-loopback."""
    ips = []
    try:
        # Méthode socket : connexion UDP sans envoi pour trouver l'IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            if not ip.startswith("127.") and not ip.startswith("169.254."):
                ips.append(ip)
    except OSError:
        pass

    # Fallback via hostname
    if not ips:
        try:
            hostname = socket.gethostname()
            for ip in socket.getaddrinfo(hostname, None, socket.AF_INET):
                addr = ip[4][0]
                if not addr.startswith("127.") and not addr.startswith("169.254."):
                    ips.append(addr)
        except OSError:
            pass

    return list(dict.fromkeys(ips))  # Dédupliquer en gardant l'ordre
