# TODOs

Generated from `/plan-ceo-review` on 2026-04-26.

## Deferred Scope

- Add user-controlled browser-assisted import after manual import works.
- Consider fully automated portal collection only after legal, security, and portal reliability review.
- Add Form 16 versus AIS/Form 26AS TDS reconciliation after the EPF wedge.
- Add bank salary credit checks after bank statement fixtures are reliable.
- Add CA review workflows only after packet exports are trusted.
- Add multi-bank connector support after the connector contract stabilizes.
- Decide whether to package a desktop wrapper, signed installer, or developer-first local distribution after the V1.0 local FastAPI web app works end to end.

## Design Review Follow-Ups

- Decide the packet export format and packet review template before V1.1. The packet must be useful for HR, EPFO, or CA review, not merely safe to export.
- Run a mobile and accessibility prototype check once the first dashboard, timeline, evidence drawer, and packet review screen exist.

## Engineering Review Follow-Ups

- Define a redacted-real fixture contribution process after synthetic fixtures prove the parser contract. The process must prevent private salary, UAN, PAN, employer, and account data from entering the public repo.
- Add OCR/scanned document support only after text-based salary slip and EPF passbook parsing is reliable. V1.0 should reject OCR-only files as unsupported with clear recovery copy.
- Design runtime connector plugin sandboxing only after built-in reviewed connectors and fixture gates exist. V1.0 should not load third-party connector code at runtime.
