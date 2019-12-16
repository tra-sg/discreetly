# discreetly AWS backend

A `discreetly` backend for Amazon Web Services (AWS).

This backend uses KMS and SSM Parameter Store.

## Configuration

| Property | default         |
| -------- | --------------- |
| `keyid`  | See NOTES below |

### Notes

If `keyid` is not specified, the default is the AWS managed CMK for your account, `alias/aws/ssm`.
