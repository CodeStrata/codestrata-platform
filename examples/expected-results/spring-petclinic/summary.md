# Spring PetClinic — curated showcase summary

> Bounded artifact for public distribution. Full raw reports are not checked in.
> Absolute local paths and secrets must never appear here.

## Repository identity

| Field | Value |
| ----- | ----- |
| Example ID | `spring-petclinic` |
| Upstream | https://github.com/spring-projects/spring-petclinic.git |
| Pinned revision | `f182358d02e4a68e52bdbabf55ca7800288511e7` |
| License | Apache-2.0 |
| Profile | `community` / `--no-ai` |
| CodeStrata | CodeStrata 0.1.0 |
| Duration | 2.15s |
| Checkout size | 1.84 MB |

## Detected technologies

- Gradle
- Maven
- Spring Boot
- Java
- JUnit

## Architecture summary

Analyzed repository 'spring-petclinic' with 131 scanned file(s). Detected 12 finding(s) (0 critical) and 1 recommendation(s) (0 critical/high priority). Automated tests were detected. CI was detected. Cloud capabilities detected: devcontainer, docker-compose, kubernetes, deployment-workflow.

## Assessment coverage

- technology_detection
- architecture_signals
- dependency_signals
- cloud_readiness_signals
- html_json_reports

## Finding counts

By severity: `{"critical": 0, "high": 0, "info": 11, "low": 1, "medium": 0}`

By category: `{"architecture": 5, "cloud_readiness": 4, "dependency": 1, "maintainability": 2}`

Total findings: **12** · Recommendations: **1**

## Top five findings

- Dependency locking is not configured (low/dependency; DEP003)
- Application architecture components detected (informational/architecture; ARCH001)
- API layer detected (informational/architecture; ARCH002)
- Persistence layer detected (informational/architecture; ARCH003)
- Test structure detected (informational/architecture; ARCH005)

## Top recommendations

- Evaluate reusable Kubernetes deployment packaging (low/cloud; REC.CLOUD.003)

## Modernization roadmap summary

Baseline deterministic assess produced one low-priority cloud packaging recommendation; no formal multi-wave roadmap artifact in this profile.

## Known false positives

- Gradle dependency-locking finding may be noisy for Maven-primary samples that also ship a build.gradle.

## Known unsupported areas

- Assessment is source-static; runtime Spring profiles and databases are not executed.
- Optional AI enrichment requires separate credentials and is not part of the baseline showcase.
