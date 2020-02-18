![](https://github.com/tra-sg/discreetly/workflows/Tests/badge.svg)
[![PyPI version fury.io](https://badge.fury.io/py/discreetly.svg)](https://pypi.python.org/pypi/discreetly/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/discreetly.svg)](https://pypi.python.org/pypi/discreetly/)

# discreetly x

## A secrets manager for AWS and GCP

```console
$ discreetly set acme/github/api-token my-secret-api-key
$ discreetly get acme/github/api-token
my-secret-api-key
$ discreetly --profile prod list acme/
['acme/prod/postgres/passwd', 'acme/prod/github/api-token']
```

Applications often require access to secrets such as database passwords or API keys. A really bad way to manage those secrets would be to bake them into your code and then check them into source control. Marginally better would be storing secrets in environment variables. If your applications are running on AWS or GCP, both platforms provide tooling for better secrets management.

`discreetly` provides a consistent API for managing secrets across both AWS and GCP. It encourages you to partition your secrets and encryption keys so that your web application only has access to the secrets it needs to run and not, for example, access to infrastructure secrets only needed by your infrastructure management tools.

## Installation

`discreetly` does not set up any infrastructure for you. At a minimum, you need to have i) credentials available for authenticating with AWS and/or Google, ii) permissions to use KMS to encrypt and decrypt secrets, and iii) permissions to read/write to the underlying store.

To install the `discreetly` cli with support for AWS and GCP:

```console
$ pip install discreetly[cli]
```

For use as a library, install `discreetly` specifying which backends you need to support, e.g.:

```console
$ pip install discreetly[aws,gcp]
```

## Configuration

`discreetly` can be configured with a JSON file, e.g.:

```json
{
  "acme": {
    "type": "aws"
  },
  "default": {
    "type": "gcp",
    "datastore_project": "acme-corp",
    "keyid": "projects/acme-corp-kms/locations/global/keyRings/discreetly/cryptoKeys/default"
  }
}
```

In the above example, the configuration contains two profiles, "acme" and "default". A profile must specify a `type`, either "aws" or "gcp".

Because a profile can specify a `keyid`, you can have named profiles not only for different cloud providers but for different KMS keys, e.g. one for dev, another for prod.

`discreetly` will search for a configuration file at the location provided by the environment variable `DISCREETLY_CONFIG_FILE`, falling back to a file named `discreetly.json` in the current directory.

## Frequently Asked Questions (FAQ)

1. What about credstash/Chamber/Vault/etc.?

   `discreetly` was actually inspired by credstash. However, credstash only supports AWS and it pre-dates Parameter Store. That said, there are use cases where a DynamoDB backend might be preferred (e.g. parameters greater than 4096 characters).

   Chamber is excellent choice, especially in a Go environment or if you only need AWS support.

   Vault is great if you have the resources to support it.

## Troubleshooting

Most issues are related to authentication or permissions with your cloud provider.

With the `discreetly` cli, you can also change the logging level by setting the `LOGLEVEL` environment variable, e.g.

```console
$ LOGLEVEL=DEBUG discreetly get my/super/secret
```

### AWS

If you have the AWS CLI installed, verify that you can use it to access Parameter Store, e.g.:

```console
$ aws ssm get-parameter /path/to/parameter --with-decryption
```

If that works, then the problem may very well be with `discreetly` and you should consider opening an issue.

However, if that's not working, it's likely a configuration or authentication issue. Under the hood, `discreetly` uses Boto 3, so consult their documentation on [setting up your authentication credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration).

### GCP

Unfortunately, [gcloud](https://cloud.google.com/sdk/gcloud/reference/datastore/) doesn't support much of the Datastore API, so it's a little harder to sanity test any issues in your local environment.

Verify that you've followed the steps in [Obtaining and providing service account credentials manually](https://cloud.google.com/docs/authentication/production#obtaining_and_providing_service_account_credentials_manually), in particular:

1. Creating a service account
2. Saving the JSON file for the service account locally
3. Setting the path to the JSON file in the environment variable, `GOOGLE_APPLICATION_CREDENTIALS`

## Library usage

```console
$ pip install discreetly[aws,gcp]
```

```python
import discreetly

cfg = {
    "default": {
        "type": "gcp",
        "datastore_project": "acme-corp",
        "keyid": "projects/acme-corp-kms/locations/global/keyRings/discreetly/cryptoKeys/default"
    },
    "acme-aws": {
        "type": "aws",
        "keyid: "alias/discreetly_key",
    }
}

d = discreetly.Session.create(cfg) # uses the 'default' profile
d.set('my-service/my-key', 'my_value')
d.get('my-service/my_key')

acme = discreetly.session.create(config=cfg, profile='acme-aws') # uses the 'acme-aws' profile
acme.set('acme/dev/postgres/password', 'open-sesame')
acme.get('acme/dev/postgres/password')

acme.set('acme/prod/postgres/password', 'super-secret', keyid='alias/prod_key')
acme.get('acme/prod/postgres/password') # no need to specify the keyid for get
```

## Development

`discreetly` is written in Python and supports Python 2.7 and 3.3+.

After cloning the repo, run `pip install -r requirements.txt` to install the required development dependencies (e.g. pytest, flake8, etc.)

You can run `pytest` to run the unit tests locally or `tox` to run all the tests under Python 2.7 and 3.x.

### Releases

- Review and update `CHANGELOG.md` in a new release branch

  - The following will show commits since the last tag beginning with 'v':

    ```console
    $ git log $(git describe --tags --match "v*" --abbrev=0)..HEAD`
    ```

  - Replace `[Unreleased]` with the new [semver](https://semver.org/) and release date, e.g. `[0.1.2] - 2019-12-13`
  - Add a new `[Unreleased]` placeholder above the new version you just created

- Create a new PR

  - The following lists all commits since the last tag, which may be useful for including in the PR description:

    `git log --pretty=format:"* %h %s" $(git describe --tags --abbrev=0 @^)..@`

- Once the PR is merged to master and passes all status checks, create and push a new signed, annotated tag, e.g.:

  ```console
  $ LAST_VERSION=$(git describe --tags --match "v*" --abbrev=0)
  $ VERSION=v0.1.1
  $ awk "/^## \[${VERSION}/{flag=1;}/## \[${LAST_VERSION}/{flag=0} flag" CHANGELOG.md | git tag -s -a ${VERSION} --cleanup=whitespace -F -
  $ git push --follow-tags
  ```

  The `awk` command above grabs the contents of the CHANGELOG for `$VERSION` to include as the message for the annotated git tag. It's fairly brittle in its assumptions about the format of the CHANGELOG. so you might just run the awk command:

  > `awk "/^## \[${VERSION}/{flag=1;}/## \[${LAST_VERSION}/{flag=0} flag" CHANGELOG.md`

  as a sanity check before creating & pushing the tag.
