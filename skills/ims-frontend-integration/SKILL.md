---
name: ims-frontend-integration
description: Integrate the aims-front Vue frontend with the ims Laravel backend, including registration Email OTP, JWT login token persistence, API Bearer headers, production builds, and dist synchronization. Use when changing frontend authentication, rebuilding aims-front, or deploying frontend assets into ims.
---

# IMS Frontend Integration

## Repositories

- Backend: the current `ims` repository.
- Frontend source: sibling `aims-front` repository, normally `../aims-front`.
- Deployment artifact: backend root `dist/`.

Do not edit only `dist/`; change `aims-front/src` first, then rebuild.

## Authentication contract

Use the current IMS flow:

1. `POST /api/register` creates an enterprise member with `status=pending`, stores the hashed password, creates the fundraising draft, and sends a 6-digit Email OTP.
2. `POST /api/register/verify-email` with `email`, `member_type=enterprise`, and `otp` activates the member and returns `data.access_token`.
3. `POST /api/auth/login` accepts `username`, `password`, and `loginType`; the backend maps them to `email` and `member_type` and returns `data.access_token`.
4. Save the token in `localStorage` and add `Authorization: Bearer <token>` to authenticated API requests.

Do not mark `email_verified_at` during registration. Do not remove OTP to work around token handling.

## Implementation workflow

1. Inspect both repositories before changing the API contract.
2. Update `aims-front/src/api/register.ts` and `Register.vue` for registration OTP.
3. Update `aims-front/src/api/auth.ts`, `src/stores/auth.ts`, and `src/api/client.ts` for token parsing, persistence, and headers.
4. Build from `aims-front`:

   ```bash
   npm run build
   ```

5. Synchronize the generated `aims-front/dist/` to `ims/dist/`. Prefer:

   ```bash
   ./bin/build-frontend
   ```

6. Verify `dist/index.html`, `dist/assets/index.js`, `dist/assets/index.css`, and the public static links exist.
7. Run backend tests with the project test database configuration; when local MySQL is unavailable, use the repository's SQLite test setup rather than changing `.env`.

## Hosting paths

- `routes/web.php` serves `dist/index.html` for `/login` and `/register`.
- `routes/web.php` has an `/assets/{path}` fallback.
- `public/assets`, `public/favicon.svg`, and `public/icons.svg` link to root `dist/` so a web server using `public/` as document root can serve Vite assets directly.
