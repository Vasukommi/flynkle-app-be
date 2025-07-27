# OAuth and OIDC Support (Planned)

Flynkle currently uses a simple username/password login with JWTs. The project aims to support OAuth and OpenID Connect providers such as Google or Azure AD in the future. This document will outline the approach once implementation begins.

Expected steps:

1. Add an OAuth library (e.g. `Authlib`) and configure providers.
2. Allow users to link external accounts during signup.
3. Issue the same JWT tokens after a successful OAuth/OIDC login.
4. Update tests and documentation.

This is a placeholder until the feature is implemented.
