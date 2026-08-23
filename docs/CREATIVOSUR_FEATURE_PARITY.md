# CreativoSur feature parity checklist

Legend: `verified` means that the target path is implemented and backed by an executable check or retained source evidence. Optional providers can be verified in their unavailable/fallback state when the original application also treated them as optional.

| Capability | Target evidence | Status |
|---|---|---|
| One ALSEMA login and shell | Native protected `/creativo` route and E2E login/session test | verified |
| Brands and brand policies | `creative_brands`, brand API/UI, imported profiles | verified |
| Cometa G real-logo/no-price policy | Policy service, negative tests, real A/B/C renders | verified |
| Manual/JSON/CSV catalog ingestion | Catalog adapters, upload API and UI | verified |
| Google Sheets read-only boundary | CSV-export sync adapter and UI; no write scope | verified |
| Product image preparation and thumbnails | Durable cutout task, indexed source images and authenticated assets | verified |
| Transparent cutout detection and `rembg` | Worker task and compositor tests | verified |
| Deterministic Pillow rendering | `alsema.creative.pillow.v1`, checksum manifests | verified |
| Template A: Product Hero | Real 1080×1350 output `e1a774b3859b…` | verified |
| Template B: Gaming/Performance | Real 1080×1350 output `c2ea0c657de7…` | verified |
| Template C: Clean Tech | Real 1080×1350 output `7926f4c023b7…` | verified |
| Feed, story, square and horizontal formats | Validated compositor format catalog and UI | verified |
| Layer positioning/scaling and up to three images | Migrated editor controls and indexed preparation flow | verified |
| Professional template layer editor | Native editor under `/creativo`, no iframe | verified |
| Text/image/shape layers | Migrated `CreativeTemplateEditor` | verified |
| Undo/redo, duplicate, z-order, lock/visibility | Migrated editor commands | verified |
| Fonts, color, alignment and transforms | Migrated properties panel | verified |
| JSON import/export and PNG export | Native editor commands using `html-to-image` | verified |
| Saved template library | Versioned PostgreSQL records and editor library | verified |
| Production preview/final asset inspection | Authenticated PNG asset endpoint and production history UI | verified |
| Durable generation and manifests | ARQ `creative.generate`, six final/manifest assets in proof job | verified |
| QA validation and checksums | Per-variant QA plus immutable SHA-256 metadata | verified |
| Pending approval by default | Proof job `fdf3280d-…` remains `pending_approval` | verified |
| Human approve/reject | Permission-protected decision endpoint and UI controls | verified |
| History and asset inspection/export | Production tab and authenticated content endpoint | verified |
| ComfyUI optional enhancement boundary | Health adapter reports unavailable and deterministic fallback is active | verified |
| SSD/FLUX configuration compatibility | ComfyUI stays provider/configuration driven; no hard dependency | verified |
| Ollama text assistance | Healthy `qwen3:8b`; structured analysis/brief used in proof job | verified |
| LM Studio optional fallback | Configurable adapter reports disabled when unset | verified |
| No automatic social publishing | Creative module has no publisher dependency; proof job was not published | verified |
| Durable progress/retry/cancel | Shared ALSEMA tasks/ARQ mappings and cancellation checks | verified |
| Import SQLite/templates/catalog/assets | Idempotent import: 5 brands, 1,434 items, 1 template, 56 legacy jobs | verified |
| RBAC and audit | Ten `creative.*` permissions seeded; actions audited | verified |
| Unit, integration and E2E coverage | 56 backend tests; frontend build/typecheck; Playwright E2E | verified |
| Docker-only ALSEMA deployment | Six services up; migration `0022` at head; readiness green | verified |

The original repository remains clean at `a5632926a7f613c80b1a92a5ec7c737ec1f8d876`, so rollback does not depend on reconstructing source code.
