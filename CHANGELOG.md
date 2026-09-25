<!-- version: 1.3.0 | build: 2026-09-18 | update: 2026-09-25 -->
# Changelog

Changes to the MSR JSON specification and to this repository.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/spec/v2.0.0.html), governed by the
compatibility policy at <https://msrjson.org/governance/>: a change that
alters what validates is MAJOR; a backwards-compatible addition is MINOR; a
non-normative clarification is PATCH.

## [Unreleased]

## [2.1.0] — 2026-09-25

**MSR JSON 2.1.0 is ratified.** `schemas/msr-2.1.json` is the current schema
and `https://msrjson.org/schemas/msr-2.1.json` its `$id`. It is MINOR: every
2.1 field is optional, 2.0.0 is unchanged and stays valid, and a 2.0 manifest
is valid against 2.1 when its `entity.descriptions` keys are BCP 47 tags
(RFC 0006). A 2.1 manifest that uses no 2.1 field also validates against 2.0.

### Added

- `schemas/msr-2.1.json`: the 2.0 schema plus RFC 0006, RFC 0008 and RFC 0009.
  RFC 0006, 0008 and 0009 move from working draft to Final Accepted Standard.
- RFC 0009, *Entity Category and Category Taxonomy*, proposed by Antonio
  Santos: optional `entity.category` and `entity.subcategories` (kebab-case
  slugs, at most 64 characters, 1–5 unique subcategories that require
  `category`), and the first MSR category taxonomy,
  `taxonomy/categories.json` 1.0.0, with 107 categories seeded from those
  registries already use. An unknown slug is a validator warning, not an
  error. Conformance tests in `tests/test_rfc_0009_category.py`.
- `tests/test_v21_superset.py`: 2.1 minus the documented RFC additions equals
  2.0, every declared object is closed, the six reference manifests validate
  against both versions, and the superseded draft equals 2.1 apart from
  metadata.
- `@msrjson/schema` 2.1.0 exports `msr-2.1.json` and
  `taxonomy/categories.json`.

### Fixed

- **The v2.1 draft had lost the 2.0 schema.** It declared only the new fields,
  with no `additionalProperties: false` and no required property below the
  root, so any JSON with the five top-level keys validated: no `entity.name`,
  no `protocol.author`, no `releases.latest`, unknown properties anywhere. 2.1
  is now built from 2.0.
- `capabilities.ai_sandbox` is removed. The draft attributed it to an
  "RFC-0004" that was never written, and it accepted unknown properties.
- RFC 0008 and the schema disagreed on HTTPS: `entity.media` URLs and
  `telemetry.ping_endpoints` now must start with `https://`.
- RFC 0008 described Push-Ping as authenticated, but the ping carries only a
  domain and nothing authenticates it; it is now an unauthenticated hint, and
  registries keep polling. Its example no longer names a real registry, its
  video example no longer points to a third-party video, and the unmeasured
  "more than 90%" bandwidth claim is removed.

### Changed

- The six reference manifests declare `https://msrjson.org/schemas/msr-2.1.json`
  and `protocol.version` `2.1.0`. They still validate against 2.0.
- `schemas/msr-2.1-draft.json` is superseded: identical to `msr-2.1.json`
  apart from `$id`, title and description, kept so manifests that name the
  draft keep resolving.
- `README.md` and `AGENTS.md` point to 2.1 as the current schema.

### Earlier unreleased changes, shipped in 2.1.0

- RFC 0008, *Media Assets, Package Manager Distribution, Execution Requirements & Push-Ping Ingestion Protocol*:
  specifies standardized visual media descriptors (`entity.media`), package manager identifiers (`distribution.package_managers` and `distribution.app_stores`), structured machine requirements (`capabilities.requirements`), and the reactive Push-Ping ingestion protocol (`POST /api/v1/ping`) for registries.
- `@msrjson/schema` — the npm distribution of this repository's canonical
  schemas and reference manifests. Its package contents are selected directly
  from this source of truth; the npm artifact is not a separately maintained
  schema fork.

- RFC 0007 (working draft), *Software Registry Conformance, Ingestion & Interoperability Specification*:
  specifies normative requirements for software registries and crawlers (Zero-Account URL Ingestion,
  SSRF and DoS network protection, semantic cache polling via ETag/If-Modified-Since, PAD JSON transition
  dialect normalization, domain authority/claim verification, and the zero-drift rule prohibiting canonical
  schema forking).
- RFC 0006, *Geographic and Language Availability*: an optional
  `capabilities.availability` object in `schemas/msr-2.1-draft.json` with
  `regions` (UN M49), `countries` and `excluded_countries` (ISO 3166-1
  alpha-2), `languages` and `support_languages` (BCP 47), `currencies` (ISO 4217)
  and `data_residency` (country, M49 region or `EU`). An absent field means not declared, never worldwide. The same draft
  requires `entity.descriptions` keys to be BCP 47 tags. Covered by
  `tests/test_availability.py`, which also asserts that the 2.0 schema keeps
  rejecting the block.
- `README.md` and `AGENTS.md` point to where the files are served today,
  `https://msrjson.org`, and to the repositories under `github.com/msrjson`.
  The validation commands fetched `https://msr-standard.org/schemas/msr-2.0.json`,
  which answers 404; they now fetch it from `msrjson.org`. The schema `$id` is
  unchanged and is described as an identifier, not a download location.
- `AGENTS.md` tells agents not to put `capabilities.availability` in a 2.0
  manifest, and that `vendor.country_code` is the vendor's seat, not a market.

- `AGENTS.md` — instructions for AI agents of any model asked to generate an
  `msr.json`: the constant `protocol` block, a procedure that derives every
  value from the project, the values that must never be invented, and a
  validation command tested against a valid and an invalid manifest.
- `AUTHORS` and `NOTICE`, crediting Antonio Santos as the author of the
  protocol and stating the scope of each license.
- `LICENSE` (MIT, for the tests and CI) and `LICENSE-SPEC` (CC-BY-4.0, full
  legal text, for the specification, schemas, examples and RFCs). The dual
  license had been claimed on the website but existed in no file.
- A conformance suite that runs from a plain checkout, with no container and no
  network, and a GitHub Actions workflow running it on every push and pull
  request.
- A test that the canonical schema's `$id` is the canonical URL, so a fork
  cannot silently become a second protocol.

### Changed in RFC 0007 and project metadata

- RFC 0007's draft crawler rules now require filtering additional non-public IP
  ranges, DNS-rebinding resistance, redirect credential isolation, decompressed
  response limits, duplicate-key-safe JSON parsing and explicit boundaries
  between publisher claims and independently observed verification. These are
  draft registry requirements and do not alter the MSR JSON 2.0 schema.

- RFC 0007 now consistently identifies a manifest's authoritative host as
  `entity.domain`, the field defined by the 2.0 schema. Its PAD-normalization
  guidance no longer instructs registries to add an unsupported
  `artifacts[].verified` field: artifacts without a verified SHA-256 digest are
  omitted from the canonical manifest and any ingestion state remains internal
  to the registry. This is a draft clarification and changes no 2.0 validation.

- The project is named **MSR JSON** everywhere it names itself: RFC page titles
  and logo text say "MSR JSON" instead of "MSR Standard".

- **The canonical domain is `msrjson.org`.** The `$id` of `msr-1.1.json`,
  `msr-2.0.json` and `msr-2.1-draft.json`, the `$schema` of the six reference
  manifests, the RFC canonical links, `AUTHORS`, `README.md` and `AGENTS.md`
  move from `https://msr-standard.org` to `https://msrjson.org`, the address the
  files are actually served from. What validates does not change: `$schema` is
  a URI, not a constant, and a test asserts that a manifest naming the former
  identifier still validates. Registries treat the former URL as an alias.

- `protocol.author` in the six reference manifests names Antonio Santos, the
  author of the protocol, instead of a working group. The field names who wrote
  the **protocol**; a product's owner goes in `entity.vendor`.

## [2.0.0] — 2026-09-17

The current stable protocol. First version published in this repository.

RFC 0001: consolidation of the entity archetype, native MCP and AI descriptors,
integer minor currency units, and Ed25519 trust signatures.

## Earlier versions

Recorded on the specification page, which predates this repository. Their
history is not in this repository's git log.

- **1.1.0** — 2025-11-20 — legacy bridge. Added webhook synchronization headers
  and JSON Schema validation. Its schema is `schemas/msr-1.1.json`.
- **1.0.0** — 2024-04-10 — deprecated. The initial JSON translation of the
  legacy ASP PAD XML standard.
