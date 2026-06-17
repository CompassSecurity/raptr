# Release Notes

## 0.1.0-beta.4 (2026-06-17)

### New Features

- Redesigned asset display in the activity Detection section for a consistent look with the activity Details ([pull 26](https://github.com/CompassSecurity/raptr/pull/26))

### Fixes

- Blue Team members can now view and restore soft-deleted assets ([pull 26](https://github.com/CompassSecurity/raptr/pull/26))
- Sandboxed the Jinja2 environment used to render report templates to prevent server-side template injection (SSTI), with clearer error handling and logging for rejected templates ([pull 22](https://github.com/CompassSecurity/raptr/pull/22))
- Sanitized file names during assessment import and export to prevent path traversal (zip-slip) and `Content-Disposition` header injection ([pull 23](https://github.com/CompassSecurity/raptr/pull/23))
- The activity `state` is now required on update, so a partial request can no longer silently reset the workflow state ([pull 24](https://github.com/CompassSecurity/raptr/pull/24))
- Restricted Blue Team file upload and deletion behind the activity update permission (activity must be visible, not deleted, and in a Waiting state) ([pull 25](https://github.com/CompassSecurity/raptr/pull/25))
- Hardened file upload against polyglot files by normalizing the stored file extension to the detected content type ([pull 27](https://github.com/CompassSecurity/raptr/pull/27))
- Anaglyph mode improvements ([b7712db](https://github.com/CompassSecurity/raptr/commit/b7712db))
- Removed a duplicate event binding surfaced by the updated Vue tooling ([pull 28](https://github.com/CompassSecurity/raptr/pull/28))
- Fixed broken documentation links and anchors ([d279562](https://github.com/CompassSecurity/raptr/commit/d279562))

### Chore

- Updated frontend and backend dependencies ([pull 28](https://github.com/CompassSecurity/raptr/pull/28))
  - Biome → 2.5.0
  - vue → 3.5.38, vue-tsc → 3.3.5
  - tailwindcss / @tailwindcss/vite → 4.3.1
  - reka-ui → 2.9.10, @lucide/vue → 1.20.0
  - dompurify → 3.4.10, marked → 18.0.5, axios → 1.18.0
  - @hey-api/openapi-ts → 0.98.2, @types/node → 25.9.3
- Earlier dependency and Biome version bumps ([6c2e2e7](https://github.com/CompassSecurity/raptr/commit/6c2e2e7), [3b08058](https://github.com/CompassSecurity/raptr/commit/3b08058))
- Scoped the release and pull-request CI workflows with `paths-ignore` and removed the unused sandbox workflow ([8206d27](https://github.com/CompassSecurity/raptr/commit/8206d27), [00ae160](https://github.com/CompassSecurity/raptr/commit/00ae160))


## 0.1.0-beta.3 (2026-05-11)

### New Features

- Add "Anaglyph" accessibility mode ([pull 16](https://github.com/CompassSecurity/raptr/pull/16))

### Fixes

- Fix for unsaved changes dialog ([pull 9](https://github.com/CompassSecurity/raptr/pull/9))
- Resolved missing Timezone for timestamps in SQLLite ([pull 15](https://github.com/CompassSecurity/raptr/pull/15))

### Chore

- Updated frontend dependencies ([pull 8](https://github.com/CompassSecurity/raptr/pull/8))
  - vue-router: 4.6.4 → 5.0.6
  - types/node: 24.12.2 → 25.0.6
  - vue/tsconfig: 0.8.1 → 0.9.1
  - vite: 7.3.2 → 8.0.10
  - marked: 17.0.6 → 18.0.3
- Updated frontend dependencies ([pull 13](https://github.com/CompassSecurity/raptr/pull/13))
  - TypeScript 5.9.3 → 6.0.3
  - Lucide Vue next → @lucide/vue 1.14.0
  - Zod 3.25.76 → 4.4.3
- Removed old frontend type and zod schema generators. Replaced with hey-api ([pull 13](https://github.com/CompassSecurity/raptr/pull/13))


## 0.1.0-beta.2 (2026-05-04)

### New Features

- Add warning dialog for unsaved changes when leaving an activity
- Add autocomplete for the key and value fields of asset properties (frontend only - no API endpoint)
- Add support for a welcome message banner on login via a backend environment variable
- Add dynamic software version through Git actions via tags or latest builds

### Fixes

- Improved blue and spectator read-only behavior (disabled buttons are replaced with labels)
- Improved markdown edit and preview layout (tabs instead of toggle)

## 0.1.0-beta.1 (2026-05-01)

### New Features

- Public beta release of RAPTR

### Fixes

- Implemented fixes after alpha tests

## 0.1.0-alpha.1 (2026-03-02)

### New Features

- Initial release of RAPTR 🚀

### Fixes

- Many to come