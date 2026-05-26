# ADR: AWS API Gateway HTTP API

## Status

Accepted.

## Context

Phase 3 requires an API Gateway in front of the platform. The demo environment
uses AWS Academy, k3s on EC2 and RDS PostgreSQL. Cost and permission limits are
important constraints.

## Decision

Use AWS API Gateway HTTP API with the `$default` stage as the public entry
point.

Validated public URL:

```text
https://oubv5hamu5.execute-api.us-east-1.amazonaws.com
```

Backend integration for the main API:

```text
http://32.197.10.136/{proxy}
```

The CPF authentication route is intended to invoke
`service-order-auth-cpf`. In the academic environment, API Gateway and Lambda
were created/configured manually through the AWS Console where needed.

## Alternatives Considered

- REST API Gateway: more features, but unnecessary for the current demo and
  generally more operational overhead.
- Direct EC2 public IP only: simpler, but would not meet the API Gateway
  requirement.
- ALB Ingress Controller: useful in production, but heavier for AWS Academy and
  not required for the current k3s setup.

## Consequences

- Meets the API Gateway requirement with low operational overhead.
- Keeps k3s/Traefik as the application ingress behind the gateway.
- Public URL is stable while EC2 IP remains stable.
- Manual console configuration must be captured as evidence until Terraform
  state and permissions are production-grade.
