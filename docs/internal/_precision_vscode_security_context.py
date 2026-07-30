#!/usr/bin/env python3
"""Precision summary: vscode security/secret findings by severity and security_context."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VSCODE_LATEST = ROOT / "validation/reports/typescript-vscode/vscode/20260730-062724"
PETCLINIC = ROOT / "validation/reports/java-spring-petclinic/spring-petclinic/20260730-061646"
SELF = ROOT / "validation/reports/codestrata-self/codestrata-platform/20260730-061659"
AUDIT = ROOT / "docs/internal/_audit_vscode_secret_findings.json"
BASELINE = ROOT / "validation/reports/typescript-vscode/vscode/20260729-082446"

SECRET_RULES = {
    "SEC001",
    "SEC002",
    "SEC003",
    "SEC004",
    "security.credential-literal",
}
HIGHISH = {"critical", "high"}
INFOISH = {"informational", "info", "low"}

CONTEXT_RE = re.compile(r"Context:\s*([^.]+?)(?:\s*\(|\.|$)", re.I)


def load_json(path: Path):
    return json.loads(path.read_text())


def ctx_from_finding(f: dict) -> str:
    md = f.get("metadata") or {}
    if isinstance(md, dict) and md.get("security_context"):
        return str(md["security_context"])
    desc = f.get("description") or f.get("explanation") or ""
    m = CONTEXT_RE.search(desc)
    if m:
        return m.group(1).strip()
    # fall back to source_role / classification
    for key in ("security_context", "source_role", "classification"):
        if f.get(key):
            return str(f[key])
        if isinstance(md, dict) and md.get(key):
            return str(md[key])
    return "(none)"


def is_secret_like(f: dict) -> bool:
    rule = str(f.get("rule_id") or "")
    cat = str(f.get("category") or f.get("finding_category") or f.get("security_category") or "").lower()
    title = str(f.get("title") or "").lower()
    if rule in SECRET_RULES or rule.startswith("SEC00"):
        return True
    if "credential" in cat or "secret" in cat:
        return True
    if "credential" in title or "secret" in title or "private key" in title or "api key" in title:
        return True
    return cat == "security" and rule.startswith("security.")


def summarize_findings(findings: list[dict], label: str) -> dict:
    by_sev = Counter()
    by_ctx = Counter()
    by_sev_ctx = Counter()
    secret = []
    for f in findings:
        if not is_secret_like(f) and str(f.get("category") or f.get("finding_category") or "").lower() != "security":
            # still count pure security category
            continue
        if not is_secret_like(f) and "security" not in str(f.get("category") or f.get("finding_category") or "").lower():
            continue
        sev = str(f.get("severity") or "unknown").lower()
        ctx = ctx_from_finding(f)
        by_sev[sev] += 1
        by_ctx[ctx] += 1
        by_sev_ctx[(sev, ctx)] += 1
        secret.append(f)
    # If filter too strict, also accept any with security_context metadata
    return {
        "label": label,
        "total_security_or_secret": len(secret),
        "by_severity": dict(by_sev),
        "by_context": dict(by_ctx),
        "high_critical": sum(by_sev[s] for s in HIGHISH),
        "info_low": sum(by_sev[s] for s in INFOISH),
        "medium": by_sev.get("medium", 0),
        "findings": secret,
    }


def summarize_security_assessment(path: Path) -> dict:
    data = load_json(path / "security-assessment.json")
    all_sums = data.get("all_finding_summaries") or data.get("finding_summaries") or []
    by_sev = Counter(str(f.get("severity") or "unknown").lower() for f in all_sums)
    by_ctx = Counter()
    by_rule = Counter(str(f.get("rule_id") or "?") for f in all_sums)
    for f in all_sums:
        by_ctx[ctx_from_finding(f)] += 1
    secretish = [
        f
        for f in all_sums
        if is_secret_like(f)
        or "credential" in str(f.get("security_category") or "").lower()
        or "credential" in str(f.get("rule_id") or "").lower()
    ]
    sec_by_sev = Counter(str(f.get("severity") or "unknown").lower() for f in secretish)
    sec_by_ctx = Counter(ctx_from_finding(f) for f in secretish)
    return {
        "status": data.get("status"),
        "all_count": len(all_sums),
        "primary_count": len(data.get("finding_summaries") or []),
        "all_by_severity": dict(by_sev),
        "all_by_context": dict(by_ctx),
        "all_by_rule": dict(by_rule),
        "secret_count": len(secretish),
        "secret_by_severity": dict(sec_by_sev),
        "secret_by_context": dict(sec_by_ctx),
        "high_critical_all": sum(by_sev[s] for s in HIGHISH),
        "info_low_all": sum(by_sev[s] for s in INFOISH),
        "high_critical_secret": sum(sec_by_sev[s] for s in HIGHISH),
        "info_low_secret": sum(sec_by_sev[s] for s in INFOISH),
        "severity_inventory": data.get("severity_inventory"),
        "finding_inventory": {
            k: (v.get("finding_count"), v.get("severity_counts"))
            for k, v in (data.get("finding_inventory") or {}).items()
            if isinstance(v, dict) and "finding_count" in v
        },
    }


def print_table(title: str, rows: list[tuple[str, object]]) -> None:
    print(f"\n=== {title} ===")
    w = max(len(r[0]) for r in rows) if rows else 10
    for k, v in rows:
        print(f"  {k:<{w}}  {v}")


def main() -> None:
    print(f"NEW vscode report: {VSCODE_LATEST}")

    findings_doc = load_json(VSCODE_LATEST / "findings.json")
    findings = findings_doc.get("findings") or []
    report_sec = [f for f in findings if str(f.get("category") or "").lower() == "security" or is_secret_like(f)]
    by_sev = Counter(str(f.get("severity") or "?").lower() for f in report_sec)
    by_ctx = Counter(ctx_from_finding(f) for f in report_sec)
    by_rule = Counter(str(f.get("rule_id") or "?") for f in report_sec)

    print_table(
        "VSCODE findings.json (report surface)",
        [
            ("total findings.json", findings_doc.get("finding_count", len(findings))),
            ("security/secret subset", len(report_sec)),
            ("by severity", dict(by_sev)),
            ("HIGH+CRITICAL", sum(by_sev[s] for s in HIGHISH)),
            ("INFO/INFORMATIONAL/LOW", sum(by_sev[s] for s in INFOISH)),
            ("by security_context", dict(by_ctx)),
            ("by rule_id", dict(by_rule)),
        ],
    )

    sa = summarize_security_assessment(VSCODE_LATEST)
    print_table(
        "VSCODE security-assessment.json (all_finding_summaries)",
        [
            ("status", sa["status"]),
            ("all findings", sa["all_count"]),
            ("primary (visible) findings", sa["primary_count"]),
            ("all by severity", sa["all_by_severity"]),
            ("HIGH+CRITICAL (all)", sa["high_critical_all"]),
            ("INFO/LOW (all)", sa["info_low_all"]),
            ("all by Context/security_context", sa["all_by_context"]),
            ("all by rule", sa["all_by_rule"]),
            ("secret-like count", sa["secret_count"]),
            ("secret by severity", sa["secret_by_severity"]),
            ("secret HIGH+CRITICAL", sa["high_critical_secret"]),
            ("secret INFO/LOW", sa["info_low_secret"]),
            ("secret by context", sa["secret_by_context"]),
            ("finding_inventory roles", sa["finding_inventory"]),
        ],
    )

    # Cross-tab severity x context for all security assessment findings
    all_sums = load_json(VSCODE_LATEST / "security-assessment.json").get("all_finding_summaries") or []
    print("\n=== VSCODE severity × context (all security findings) ===")
    print(f"  {'severity':<16} {'context':<40} count")
    cross = Counter((str(f.get("severity") or "?").lower(), ctx_from_finding(f)) for f in all_sums)
    for (sev, ctx), n in sorted(cross.items(), key=lambda x: (-x[1], x[0][0], x[0][1])):
        print(f"  {sev:<16} {ctx:<40} {n}")

    # Audit baseline
    if AUDIT.exists():
        audit = load_json(AUDIT)
        audit_n = audit.get("total_secret_findings", len(audit.get("findings") or []))
        audit_by_class = audit.get("by_classification") or {}
        audit_by_rule = audit.get("by_rule") or {}
        audit_sev = Counter(str(f.get("severity") or "?").lower() for f in audit.get("findings") or [])
        print_table(
            "BASELINE audit (_audit_vscode_secret_findings.json from 20260729-082446)",
            [
                ("audit secret findings", audit_n),
                ("by classification", audit_by_class),
                ("by rule", audit_by_rule),
                ("by severity (audit)", dict(audit_sev)),
                ("delta: new secret-like vs audit", f"{sa['secret_count']} now vs {audit_n} audit (Δ {sa['secret_count'] - audit_n})"),
                ("delta: new all security vs audit", f"{sa['all_count']} all security now vs {audit_n} audit secrets"),
                (
                    "HIGH+CRITICAL change",
                    f"now secret HIGH+CRIT={sa['high_critical_secret']} / all HIGH+CRIT={sa['high_critical_all']}; "
                    f"audit HIGH+CRIT={sum(audit_sev[s] for s in HIGHISH)}",
                ),
            ],
        )

    if BASELINE.exists() and (BASELINE / "security-assessment.json").exists():
        old = summarize_security_assessment(BASELINE)
        print_table(
            "PRIOR report security-assessment (20260729-082446)",
            [
                ("all findings", old["all_count"]),
                ("by severity", old["all_by_severity"]),
                ("HIGH+CRITICAL", old["high_critical_all"]),
                ("INFO/LOW", old["info_low_all"]),
                ("secret-like", old["secret_count"]),
                ("secret HIGH+CRIT", old["high_critical_secret"]),
            ],
        )

    # Peer repos
    for name, path in (("petclinic", PETCLINIC), ("codestrata-self", SELF)):
        sec_path = path / "security-assessment.json"
        if not sec_path.exists():
            print(f"\n=== {name}: no security-assessment.json ===")
            continue
        peer = summarize_security_assessment(path)
        print_table(
            f"{name} security findings",
            [
                ("status", peer["status"]),
                ("all / primary", f"{peer['all_count']} / {peer['primary_count']}"),
                ("by severity", peer["all_by_severity"]),
                ("HIGH+CRITICAL", peer["high_critical_all"]),
                ("INFO/LOW", peer["info_low_all"]),
                ("by context", peer["all_by_context"]),
            ],
        )


if __name__ == "__main__":
    main()
