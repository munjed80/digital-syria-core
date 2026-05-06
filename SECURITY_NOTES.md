# SECURITY NOTES

- This MVP uses JWT for authentication and is designed to be replaceable with Keycloak/national SSO.
- Do not commit real credentials or production secrets.
- Use `.env` files locally and `.env.example` templates in the repository.
- Every important mutating action is audited in `audit_logs`.
- API failures return structured JSON to prevent leaking internals.
- Demo seed data is synthetic and non-sensitive.
