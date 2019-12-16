# discreetly GCP backend

A `discreetly` backend for Google Cloud Platform (GCP).

This backend uses Cloud KMS and Datastore.

## Configuration

| Property                        | default         |
| ------------------------------- | --------------- |
| `datastore_project`             | See NOTES below |
| `datastore_namespace`           |                 |
| `datastore_kind`                | `Secret`        |
| `datastore_property_ciphertext` | `ciphertext`    |
| `datastore_property_keyid`      | `keyid`         |
| `keyid`                         | See NOTES below |

### NOTES

If `datastore_project` is not specified, the default project ID will be determined by the [google-cloud-core library](https://googleapis.dev/python/google-cloud-core/latest/config.html), which searches these locations in the following order:

- `GOOGLE_CLOUD_PROJECT` environment variable
- `GOOGLE_APPLICATION_CREDENTIALS JSON` file
- Default service configuration path from `$ gcloud beta auth application-default login`
- Google App Engine application ID
- Google Compute Engine project ID (from metadata server)

If `keyid` is not specified, the keyid will be constructed from the default project ID, location `global`, keyRing `discreetly`, and cryptoKey `default`. For example, assuming the default project ID is determined to be "acme-corp", the keyid would be:

> `projects/acme-corp/locations/global/keyRings/discreetly/cryptoKeys/default`

## Datastore Entities, Properties and Keys

Given a `discreetly` secret named "foo/bar/baz", the corresponding Datastore Entity would be:

|              |                                                            |
| ------------ | ---------------------------------------------------------- |
| Namespace:   | [default]                                                  |
| Kind:        | `Secret`                                                   |
| Key:         | `Parent name:foo > Parent name:bar > Secret name:baz`      |
| Key literal: | `` Key(`Parent`, 'foo', `Parent`, 'bar', Secret, 'baz') `` |

with the following properties:

| Name         | Type   | Indexed? | Description                                                                                       |
| ------------ | ------ | -------- | ------------------------------------------------------------------------------------------------- |
| `ciphertext` | Blob   | No       | the KMS-encrypted value                                                                           |
| `keyid`      | String | Yes      | the KMS keyid (e.g. `projects/acme-corp/locations/global/keyRings/discreetly/cryptoKeys/default`) |

Notably, [Datastore best practices](https://cloud.google.com/datastore/docs/best-practices) recommend not using a forward slash (`/`) in kind or key names. This was the primary driver for creating an ancestor chain of kind `Parent` for each path element.
