# Install On Jenkins

The Jenkins adapter is provided as a Shared Library under `ci/jenkins/`.

Configure Jenkins to load the repository as a Global Pipeline Library and set the library base path to `ci/jenkins`.

Available steps:

- `mb3rBeringDiscover(...)`
- `mb3rSheaftGate(...)`
- `mb3rPublishReport(...)`

## Consumption Model

The library does not embed Bering or Sheaft logic. Pipelines pass commands that invoke upstream released tools or containers and write JSON payloads to the paths exposed through `MB3R_PAYLOAD_JSON`.

## Minimal Example

See `examples/jenkins/Jenkinsfile`.

Use the library by tag:

```groovy
@Library('mb3r-stack@v1.3.0') _
```

The example targets the verified `v1.3.0` bundle; use this tag after publication.
For the current published bundle, use the `v1.2.0` release pack.
