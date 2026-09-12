# hardened-pipeline

Pipeline de seguridad DevSecOps, agnóstico al lenguaje, con supply chain
hardening desde el diseño. Un único workflow (`security.yml`) con 7 jobs
en paralelo, pensado para clonarse y adoptarse en cualquier repo.

## Qué hace el pipeline

| Job | Herramienta | Qué cubre |
|---|---|---|
| `secrets-scan` | [Betterleaks](https://github.com/betterleaks/betterleaks) | Secrets hardcodeados, en el diff y en el historial de git |
| `sast` | [Semgrep](https://semgrep.dev) | Vulnerabilidades de código (`p/python`, `p/javascript`) |
| `sca` | [OSV-Scanner](https://github.com/google/osv-scanner) | CVEs conocidos en dependencias (lockfiles/manifests, pre-build) |
| `image-scan` | [Syft](https://github.com/anchore/syft) + [Grype](https://github.com/anchore/grype) | SBOM + vulnerabilidades de imagen Docker (opcional, solo si hay `Dockerfile`) |
| `iac-scan` | [Checkov](https://www.checkov.io) | Misconfiguraciones en Terraform |
| `workflow-lint` | [zizmor](https://zizmor.sh) | Vulnerabilidades en los propios workflows (tags mutables, pwn requests, permisos excesivos) |
| `security-gate` | — | Agrega el resultado de los 4 jobs hard-fail (`secrets-scan`, `sast`, `sca`, `workflow-lint`) y es el único required check para branch protection |

`image-scan` e `iac-scan` son **informativos**: corren en soft-fail
(`fail-build: false` / `--soft-fail`) y `security-gate` no los tiene en
cuenta para bloquear el merge — reportan, no bloquean.

Todos los jobs corren bajo
[`step-security/harden-runner`](https://github.com/step-security/harden-runner)
con `egress-policy: block` y un allowlist explícito de dominios por job
(comentado inline en `security.yml`, explicando por qué está cada uno).
[Renovate](https://docs.renovatebot.com) (no Dependabot) mantiene las
dependencias del propio pipeline al día, pineando cada Action por digest.

## Cómo adoptarlo en otro proyecto

1. Copiá `.github/workflows/security.yml` y los archivos de configuración
   de la raíz (`.betterleaks.toml`, `.semgrep.yml`, `.semgrepignore`,
   `.checkov.yaml`, `.grype.yaml`, `.syft.yaml`, `.zizmor.yml`,
   `osv-scanner.toml`, `.github/renovate.json`).
2. Ajustá las rutas hardcodeadas al layout de tu repo:
   - `iac-scan` apunta a `example/infra` — cambiala a donde vivan tus
     `.tf`.
   - `image-scan` busca `example/Dockerfile` — cambiá esa ruta a la tuya
     (o dejala si tu Dockerfile está en la raíz, ajustando el `if:` de
     cada step).
3. Activá GitHub Advanced Security / Code Scanning en el repo (lo usan
   `secrets-scan`, `sast`, `sca` y `workflow-lint` para subir SARIF).
4. Activá la Renovate GitHub App en el repo (o adaptá `renovate.json` a
   tu self-hosted runner de Renovate).
5. En Settings → Branches, marcá `security-gate` como único required
   status check.

Todas las Actions externas están pineadas por SHA de commit (no por tag),
verificado contra el release real en GitHub — no confíes en un SHA sin
volver a verificarlo vos si vas a usarlo en producción, revisá con
`gh api repos/<owner>/<repo>/git/refs/tags/<tag>`.

### Decisiones de instalación no obvias

- **Betterleaks** no tiene una GitHub Action oficial (solo un fork de
  terceros no afiliado). Se instala con `go install
  github.com/betterleaks/betterleaks@<version>` pineado, mismo patrón que
  Semgrep/Checkov — evita sumar una Action no auditada a la cadena de
  confianza del pipeline.
- **OSV-Scanner** tampoco tiene una Action de step único: su repo solo
  publica reusable workflows (a nivel `jobs.<job>.uses`), que no pueden
  convivir con Harden-Runner y el resto de los steps dentro del mismo
  job. Se instala igual, por binario.
- **Semgrep** y **Checkov** no tienen un `action.yml` confiable —
  `pip install <tool>==<versión fija>` y `run:`, en vez de `uses:`.

## Cómo reproducir cada PR de ataque

Cada incidente real de supply chain de 2026 está recreado en una branch
`demo/attack-*`, partiendo de `main` (con el pipeline completo activo).
Abrí un PR de esa branch contra `main` y el control correspondiente
debería frenarlo:

| Branch | Incidente que recrea | Control que lo frena |
|---|---|---|
| `demo/attack-unpinned-tag` | Trivy — CVE-2026-33634 (force-push de 76/77 tags mutables, 19 mar 2026) | `workflow-lint` (zizmor, `unpinned-uses`) |
| `demo/attack-egress-secret` | axios — RAT vía `plain-crypto-js` (30 mar 2026) | Harden-Runner (`egress-policy: block`) en `secrets-scan` |
| `demo/attack-hardcoded-secret` | Campañas npm/PyPI/Docker Hub (21-23 abr 2026) | `secrets-scan` (Betterleaks) |
| `demo/attack-vulnerable-dep` | TanStack — CVE-2026-45321 (84 versiones maliciosas, 11 may 2026) | `sca` (OSV-Scanner) |
| `demo/attack-runner-exfil` | binding.gyp — worm Miasma / "Phantom Gyp" (3 jun 2026) | Harden-Runner (`egress-policy: block`) en `secrets-scan` |
| `demo/attack-excess-permissions` | IronWorm (jun 2026) | `workflow-lint` (zizmor, permisos excesivos) |
| `demo/attack-pwn-request` | AsyncAPI — pwn request vía `pull_request_target` (14 jul 2026) | `workflow-lint` (zizmor, `dangerous-triggers`) |

Cada archivo modificado en estas branches tiene un comentario citando el
incidente real que reproduce. Ninguna branch apunta a infraestructura real
de los atacantes — los dominios/valores usados son de ejemplo,
claramente inválidos.

`demo/attack-egress-secret` y `demo/attack-runner-exfil` insertan su step
malicioso dentro de `secrets-scan` (uno de los 4 jobs hard-fail que
`security-gate` sí evalúa) — no en `image-scan` ni `iac-scan`, que son
soft-fail y quedarían fuera de la decisión de merge.

## Estructura

```
.github/
  workflows/security.yml
  renovate.json
example/            # app mínima (FastAPI) + Dockerfile + Terraform + manifest npm
docs/index.html      # tabla de estado de las 7 demos, servida por GitHub Pages
```
