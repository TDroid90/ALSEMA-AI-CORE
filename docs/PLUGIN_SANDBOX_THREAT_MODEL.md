# Plugin sandbox threat model

## Trust boundary

The API and worker never mount the Docker socket. Only `docker-proxy` mounts it
read-only and exposes the minimal container lifecycle API on the private Compose
network. The application accepts no user-selected image, command, volume, host
path, environment variable or network.

## Execution policy

`docker_sandbox` creates one Python container per execution using the configured
approved image. It runs as UID/GID `65532`, with a read-only root filesystem,
`/tmp` as a small noexec tmpfs, no capabilities, no privileged mode, no host
bind mounts, no Docker socket and `NetworkMode=none`. CPU, memory, PID and wall
clock limits are fixed by server configuration. The container is force-deleted
after logs, exit code and duration are captured.

`in_process` exists only as an internal extension point and rejects external
plugin execution. Production defaults to `docker_sandbox`.

The included `plugins/foundation-python/manifest.json` is the Foundation v1.0
demonstration plugin. An administrator must register and enable that manifest
before its `python.execute` capability can use the execution endpoint. The
request accepts source text only: the Core constructs the fixed interpreter
command and complete container specification itself. It never accepts a
plugin-provided image, environment, mount, network, command, or Docker option.

## Controls verified by automated tests

The sandbox runtime tests assert that the generated Docker request uses a
non-root user, read-only root filesystem, disabled network, empty bind list,
all capabilities dropped, `no-new-privileges`, fixed resource limits and the
only approved temporary filesystem. Tests also cover source validation and
Docker stdout/stderr frame separation. The deployment smoke test executes a
real ephemeral container through the proxy and confirms it is removed.

## Residual risk

The Docker proxy is privileged infrastructure and must remain reachable only on
the internal Compose network. The approved image is part of the trusted supply
chain; pin it to a digest in production. Network-enabled plugins are not part of
Foundation v1.0 and require a dedicated policy and egress proxy.
