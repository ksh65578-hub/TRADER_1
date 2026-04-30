# MVP4 Secret Pattern Hygiene Recheck

created_at_utc: 2026-04-29T08:51:41Z
patch_id: MVP4_SECRET_PATTERN_HYGIENE_RECHECK_20260429_001

Findings:
- The previous scanner could miss underscored runtime key names such as AWS-style secret access key assignments.
- The previous scanner could miss Authorization Bearer header values.
- The previous scanner could miss JWT-like literals when copied directly into source or config fixtures.

Patch:
- Added strict credential patterns for underscored API/access/secret/private/token names.
- Added Authorization Bearer header detection.
- Added JWT-like literal detection.
- Added negative tests using runtime-assembled fixtures so the test file itself does not become a secret finding.

Audit:
- included_count: 530
- excluded_count: 977
- secret_findings_count: 0
- covered_secret_shapes: AWS_STYLE_SECRET_ACCESS_KEY_ASSIGNMENT, AUTHORIZATION_BEARER_HEADER, JWT_LITERAL, AWS_AKIA_ACCESS_KEY, PRIVATE_KEY_BLOCK

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
