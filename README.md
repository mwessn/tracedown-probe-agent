# tracedown-probe-agent

The Tracedown probe agent — executes [Lace](https://lacelang.dev) probe scripts
and returns structured results. This is the process that actually makes the HTTP
calls, so you deploy one wherever you want checks to originate from.

Tracedown is a self-hosted API monitoring platform. This repository is only the
agent; it is driven by `tracedown-core-backend`.

📖 **Documentation: [tracedown.dev](https://tracedown.dev)** —
see [Probe Agents](https://tracedown.dev/install/agents/).

Stack: Python 3.10+, FastAPI, uvicorn, httpx, and the Lace validator and
executor.

## How it works

The agent is a **stateless executor**. It receives a script, its resolved
variables, and the previous run's result; it runs the script and returns the raw
ProbeResult JSON. It holds no monitoring state and makes no decisions.

The scheduler **dials the agent** — so the agent must be reachable inbound from
the scheduler. An agent behind NAT with no inbound route will enrol successfully
and then never receive work.

**Enrolment** is one-shot: given a bootstrap token and the gateway URL, the agent
generates an RSA-4096 keypair, sends a CSR, and stores the signed certificate,
the CA trust bundle and its slug. Once those files exist, enrolment is skipped —
which is what makes restarts safe. Certificates last a year and the agent renews
itself 30 days out, proving possession of the current key.

**Health** is not a ping: `POST /health/challenge` makes the agent run a real
Lace script to fetch a one-time token from the gateway, so a pass proves the
executor and the network both work.

## Running

The easiest path is the helper in
[tracedown-core-backend](https://github.com/tracedown/tracedown-core-backend),
which generates a token and starts the container against a running stack:

```bash
# from tracedown-core-backend
./scripts/bootstrap-agent.sh [slug]
```

Manually:

```bash
docker build -t tracedown-agent .
docker run -d --name tracedown-agent \
  -e PROBE_AGENT_BOOTSTRAP_TOKEN=<one-time token> \
  -e PROBE_AGENT_SCHEDULER_URL=http://tracedown-gateway:20714 \
  tracedown-agent
```

Despite its name, `PROBE_AGENT_SCHEDULER_URL` is the **api-gateway's** base
URL — registration and certificate renewal are served there, not by the
scheduler.

Configuration is environment-driven and prefixed `PROBE_AGENT_` — the full
reference is in the [documentation](https://tracedown.dev/install/agents/).

## Testing

```bash
pytest
```

## License

Open source under the Apache License 2.0. See `LICENSE`.
