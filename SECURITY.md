# Security and privacy

TrueMe is in development and has no supported release yet. The CLI processes photos locally and exports reports only on explicit request.
This implementation has not undergone a security audit.

Do not include personal photos, embeddings, credentials, or full private paths
in public issues. Use synthetic data and minimal reproduction steps where
possible. Treat model files as untrusted unless their source and integrity
have been verified. Keep runtime and image-decoding dependencies updated.

For a potential vulnerability, contact the repository maintainer through a
private channel they explicitly publish. No dedicated security address or
private reporting service is configured here yet; do not assume one exists.
Until a private channel is available, avoid publishing sensitive exploit
details or private data. No response-time commitment is made.

`trueme web` listens on 127.0.0.1 by default. Binding another address exposes
the reference and camera frames to that network without authentication or
TLS; do so only on networks you trust. The page keeps data in server memory
only during comparison, but the browser and operating system may still cache
camera access state. Reference-photo export sends an in-memory crop to the same
local backend and saves JPEG or PNG only through an explicit browser download. The
backend does not save export files or modify the original photo. Users control
the downloaded files' storage and sharing.

The application does not provide identity verification, guarantee
third-party acceptance, or guarantee secure memory erasure. Reports may still
contain sensitive filenames and scores; users control their storage and sharing.
