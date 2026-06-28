"""Cabeceras de seguridad HTTP (equivalente al SecurityHeaders de Gin).

Endurece la API contra ataques de navegador:
  - X-Content-Type-Options: nosniff      → evita MIME-sniffing
  - X-Frame-Options: DENY                → anti-clickjacking (navegadores viejos)
  - Referrer-Policy: no-referrer         → no filtrar URLs a terceros
  - Strict-Transport-Security            → forzar HTTPS (solo efectivo sobre TLS)
  - Content-Security-Policy              → bloquear qué puede cargar la respuesta

Una API JSON no sirve HTML, así que el CSP es muy restrictivo. Se omite SOLO en
la documentación interactiva (/docs, /redoc, /openapi.json) para que su propia
UI (scripts/estilos) pueda cargar.

Reusable: móntalo con app.add_middleware(SecurityHeadersMiddleware).
"""
_CSP = b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
_DOCS_PREFIXES = ("/docs", "/redoc", "/openapi.json")


class SecurityHeadersMiddleware:
    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        path = scope.get("path", "")
        es_docs = path.startswith(_DOCS_PREFIXES)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = message.setdefault("headers", [])
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"x-frame-options", b"DENY"))
                headers.append((b"referrer-policy", b"no-referrer"))
                headers.append(
                    (b"strict-transport-security",
                     b"max-age=63072000; includeSubDomains")
                )
                if not es_docs:
                    headers.append((b"content-security-policy", _CSP))
            await send(message)

        await self.app(scope, receive, send_wrapper)
