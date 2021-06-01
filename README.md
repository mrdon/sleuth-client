# Sleuth Client

`sleuth-client` connects your git repository to [Sleuth](https://sleuth.io). It collects deployment information 
from your local git repository and publishes it to Sleuth.

Sleuth Client is available to install in binary form on Linux and macOS or any other 
system that supports Python 3.8.

## Documentation

The sleuth client supports multiple commands. To discover what they are, run:

```
sleuth --help
```

Most commands require the `-k` argument to be first passed in, which is the API key used to authenticate to Sleuth.

### `deploy`

The `deploy` command collects diff information from a local git repository and submits it to Sleuth
as a "deploy" or release. For example:

```
sleuth -k my_key deploy -o my_org -d my_deployment .
```

### `validate`

The `validate` command takes a Sleuth Actions file as an argument and validates it against your organization's 
schema. It allows you to validate your `rules.yml` file either locally or in a continuous integration (CI) server.

To learn more about Sleuth Actions and the file format, see the [documentation](https://help.sleuth.io/actions).

For example:

```
sleuth -k my_key deploy -o my_org -d my_deployment .sleuth/rules.yml
```

### `set-health`

The `set-health` command sets the health for a deployment by finding the latest deploy for that deployment and 
overriding its health.

For example:

```
sleuth -k my_key set-health -o my_org -d my_deployment unhealthy
```

## Installation

### Linux

The latest release can be downloaded directly via:

```
wget https://github.com/sleuth-io/sleuth-client/releases/latest/download/sleuth
chmod 755 sleuth
```

### MacOS

The latest release can be downloaded directly via:

```
wget https://github.com/sleuth-io/sleuth-client/releases/latest/download/sleuth-macOS
chmod 755 sleuth-macOS
```
