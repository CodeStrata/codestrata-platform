# Repository Cloud Evidence (Phase 4.7.2)

Platform evidence for repository-observable cloud technologies and deployment
signals. **Not** owned by Cloud Intelligence assessment.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Discovery / containers / IaC / orchestration / serverless / managed services / deployment facts | Platform `repository_cloud` evidence |
| Cloud Intelligence interpretation | Cloud Hygiene rules (Phase 4.7.3) |
| Findings / severity / readiness scores | Findings via `cloud.core`; no readiness scores |

Collectors must not import `codestrata.domain.cloud` / `codestrata.application.cloud` and
must not emit Findings.

## Contract

| Constant | Value |
| -------- | ----- |
| Schema | `repository-cloud-evidence` **1.0.0** |
| Artifact | `repository-cloud-evidence.json` |
| Schema ID | `codestrata.repository_cloud_evidence` |
| Provider | `repository_cloud.discovery` @ `1.0.0` |
| Aggregate | `AggregatedRepositoryCloudEvidence` |

## Detected families

- **Platforms:** AWS, Azure, GCP (from provider/content markers)
- **Containers:** Docker, Docker Compose, Podman, Dev Containers, Containerfile
- **Orchestration:** Kubernetes, Helm, OpenShift
- **IaC:** Terraform, CloudFormation, CDK, Pulumi, ARM, Bicep
- **Serverless:** Lambda, Azure Functions, Google Cloud Functions, Serverless Framework, SAM
- **Managed services:** S3, DynamoDB, RDS, SQS, SNS, EventBridge, Azure Storage / Service Bus / Cosmos DB, GCS, Pub/Sub, Cloud SQL
- **Deployment:** GitHub Actions, Azure DevOps, GitLab CI, Jenkins, Argo CD, Flux

## Configuration

```toml
[evidence.repository_cloud]
enabled = false
# max_files = 500
# max_file_chars = 500000
# max_file_bytes = 2000000
```

Independent of `[analysis.cloud]` and `[report.sections.cloud]`.

## Explicit non-claims

Zero candidates does not mean cloud technologies are absent. Presence of
candidates does not mean the repository is cloud ready, secure, or cost-efficient.
