"""LLM output quality evaluation — hits the live API with 25 real incidents.

Run this when the API is up (docker compose up or uvicorn running):
    python scripts/eval/run_llm_eval.py

Results saved to artifacts/llm_eval_results.json for manual scoring.
After running, open that file and score each response on 4 dimensions (1-5):
  - relevance:     Did it address the actual incident?
  - correctness:   Are the actions technically valid?
  - hallucination: 5=no hallucination, 1=made things up (inverted scale)
  - completeness:  Did it cover all steps needed to resolve?

Then run: python scripts/eval/score_llm_eval.py to compute aggregate scores.
"""

import json
import sys
import time
from pathlib import Path

import httpx

API_URL = "http://localhost:8000/incident/analyze"
TIMEOUT = 60  # seconds per request — LLM can be slow

INCIDENTS = [
    {
        "incident_id": "EVAL-001",
        "alert_title": "NodeFilesystemSpaceFillingUp",
        "service": "payment-api",
        "severity": "critical",
        "log_lines": [
            "ERROR disk usage at 94% on /dev/sda1",
            "WARN inode exhaustion approaching on /var/log",
            "ERROR unable to write to /tmp: no space left on device",
        ],
    },
    {
        "incident_id": "EVAL-002",
        "alert_title": "KubePodCrashLooping",
        "service": "order-service",
        "severity": "critical",
        "log_lines": [
            "ERROR OOMKilled: container exceeded memory limit 512Mi",
            "WARN pod order-service-7d9f8b restarted 15 times in 10 minutes",
            "ERROR failed to pull image: ImagePullBackOff",
        ],
    },
    {
        "incident_id": "EVAL-003",
        "alert_title": "KubeAPIDown",
        "service": "kube-apiserver",
        "severity": "critical",
        "log_lines": [
            "ERROR connection refused to kube-apiserver:6443",
            "WARN etcd cluster unhealthy: leader election in progress",
            "ERROR kubectl get pods: dial tcp: connect: connection refused",
        ],
    },
    {
        "incident_id": "EVAL-004",
        "alert_title": "CPUThrottlingHigh",
        "service": "analytics-service",
        "severity": "warning",
        "log_lines": [
            "WARN CPU throttling 87% for container analytics-worker",
            "INFO request latency P99 increased from 200ms to 2400ms",
            "WARN goroutine pool exhausted: 500/500 workers busy",
        ],
    },
    {
        "incident_id": "EVAL-005",
        "alert_title": "etcdNoLeader",
        "service": "etcd",
        "severity": "critical",
        "log_lines": [
            "ERROR etcd cluster has no leader",
            "WARN raft: heartbeat send failed to member 3a4b5c6d",
            "ERROR lost quorum: 1 of 3 members reachable",
        ],
    },
    {
        "incident_id": "EVAL-006",
        "alert_title": "KubeDeploymentReplicasMismatch",
        "service": "frontend",
        "severity": "warning",
        "log_lines": [
            "WARN deployment frontend: desired 5 replicas, available 2",
            "ERROR pod frontend-abc123 failed to schedule: insufficient memory",
            "WARN rollout paused: waiting for 3 pods to be ready",
        ],
    },
    {
        "incident_id": "EVAL-007",
        "alert_title": "PrometheusRemoteWriteBehind",
        "service": "prometheus",
        "severity": "warning",
        "log_lines": [
            "WARN remote write behind 4m30s for endpoint https://thanos:9291",
            "ERROR remote write: context deadline exceeded after 30s",
            "WARN queue high watermark reached: 10000/10000 samples",
        ],
    },
    {
        "incident_id": "EVAL-008",
        "alert_title": "AlertmanagerClusterDown",
        "service": "alertmanager",
        "severity": "critical",
        "log_lines": [
            "ERROR alertmanager cluster has 0 healthy members",
            "WARN mesh peer connection failed: dial tcp refused",
            "ERROR failed to send alert PagerDuty: connection refused",
        ],
    },
    {
        "incident_id": "EVAL-009",
        "alert_title": "KubePersistentVolumeFillingUp",
        "service": "postgres",
        "severity": "warning",
        "log_lines": [
            "WARN PVC postgres-data is 89% full (89Gi of 100Gi used)",
            "ERROR PostgreSQL: could not write to file: no space left",
            "WARN WAL archive filling up: 45Gi of 50Gi used",
        ],
    },
    {
        "incident_id": "EVAL-010",
        "alert_title": "KubeNodeNotReady",
        "service": "worker-node-3",
        "severity": "critical",
        "log_lines": [
            "ERROR node worker-node-3 status: NotReady for 8 minutes",
            "WARN kubelet stopped posting node status",
            "ERROR container runtime docker is not running",
        ],
    },
    {
        "incident_id": "EVAL-011",
        "alert_title": "KubeStatefulSetReplicasMismatch",
        "service": "kafka",
        "severity": "warning",
        "log_lines": [
            "WARN statefulset kafka: desired 3 replicas, ready 1",
            "ERROR kafka-1 pod stuck in Pending: PVC not bound",
            "WARN under-replicated partitions: 45 partitions at risk",
        ],
    },
    {
        "incident_id": "EVAL-012",
        "alert_title": "NodeNetworkReceiveErrs",
        "service": "ingress-node",
        "severity": "warning",
        "log_lines": [
            "WARN network receive errors on eth0: 1240 errors/sec",
            "ERROR packet loss 12% detected on bond0",
            "WARN NIC firmware mismatch: driver version incompatible",
        ],
    },
    {
        "incident_id": "EVAL-013",
        "alert_title": "KubeHpaMaxedOut",
        "service": "api-gateway",
        "severity": "warning",
        "log_lines": [
            "WARN HPA api-gateway at maximum replicas: 20/20",
            "INFO CPU utilization 94% across all pods",
            "WARN request queue depth 5000: shedding load",
        ],
    },
    {
        "incident_id": "EVAL-014",
        "alert_title": "PrometheusBadConfig",
        "service": "prometheus",
        "severity": "critical",
        "log_lines": [
            "ERROR failed to reload config: invalid scrape_config",
            "WARN prometheus config reload failed at 14:32:07",
            "ERROR unknown field 'scrape_interval_seconds' in scrape_config",
        ],
    },
    {
        "incident_id": "EVAL-015",
        "alert_title": "KubeletDown",
        "service": "node-5",
        "severity": "critical",
        "log_lines": [
            "ERROR kubelet on node-5 is not responding",
            "WARN node node-5 has not reported status for 5 minutes",
            "ERROR all pods on node-5 evicted: node is NotReady",
        ],
    },
    {
        "incident_id": "EVAL-016",
        "alert_title": "KubeJobFailed",
        "service": "data-pipeline",
        "severity": "warning",
        "log_lines": [
            "ERROR job nightly-etl failed after 3 retries",
            "ERROR exit code 1: database connection timeout after 30s",
            "WARN job nightly-etl has been running for 4h (timeout: 2h)",
        ],
    },
    {
        "incident_id": "EVAL-017",
        "alert_title": "KubeClientCertificateExpiration",
        "service": "kube-apiserver",
        "severity": "warning",
        "log_lines": [
            "WARN client certificate for system:node:worker-2 expires in 12h",
            "ERROR TLS handshake failed: certificate expired",
            "WARN kubelet unable to authenticate: x509 certificate has expired",
        ],
    },
    {
        "incident_id": "EVAL-018",
        "alert_title": "NodeRAIDDegraded",
        "service": "storage-node-1",
        "severity": "critical",
        "log_lines": [
            "ERROR md0: degraded — 1 of 2 drives failed",
            "WARN /dev/sdb I/O errors: 452 read failures",
            "ERROR SMART: reallocated sector count critical on /dev/sdb",
        ],
    },
    {
        "incident_id": "EVAL-019",
        "alert_title": "KubeProxyDown",
        "service": "kube-proxy",
        "severity": "critical",
        "log_lines": [
            "ERROR kube-proxy not running on node worker-4",
            "WARN iptables rules stale: services unreachable from node",
            "ERROR service ClusterIP 10.96.45.12 not accessible",
        ],
    },
    {
        "incident_id": "EVAL-020",
        "alert_title": "PrometheusRuleFailures",
        "service": "prometheus",
        "severity": "warning",
        "log_lines": [
            "ERROR rule evaluation failed: group=SLO, rule=ErrorBudgetBurn",
            "WARN evaluation took 45s, exceeds interval 15s",
            "ERROR query timed out: too many time series matched",
        ],
    },
    {
        "incident_id": "EVAL-021",
        "alert_title": "KubeSchedulerDown",
        "service": "kube-scheduler",
        "severity": "critical",
        "log_lines": [
            "ERROR kube-scheduler is not running",
            "WARN 47 pods pending: no scheduler to assign nodes",
            "ERROR leader election lost: scheduler exiting",
        ],
    },
    {
        "incident_id": "EVAL-022",
        "alert_title": "KubeVersionMismatch",
        "service": "cluster",
        "severity": "warning",
        "log_lines": [
            "WARN node worker-7 running kubelet v1.27.3, apiserver v1.28.1",
            "WARN version skew exceeds supported limit of 2 minor versions",
            "ERROR feature gate PodSchedulingReadiness not supported on node",
        ],
    },
    {
        "incident_id": "EVAL-023",
        "alert_title": "NodeClockSkewDetected",
        "service": "worker-node-2",
        "severity": "warning",
        "log_lines": [
            "WARN clock skew 350ms detected on worker-node-2",
            "ERROR NTP sync failed: all servers unreachable",
            "WARN TLS certificate validation failures due to time drift",
        ],
    },
    {
        "incident_id": "EVAL-024",
        "alert_title": "KubeMemoryOvercommit",
        "service": "cluster",
        "severity": "warning",
        "log_lines": [
            "WARN memory overcommit ratio 1.8x on node worker-1",
            "ERROR OOMKiller invoked: killed process redis-server (pid 12345)",
            "WARN memory requests 48Gi exceed allocatable 32Gi on node",
        ],
    },
    {
        "incident_id": "EVAL-025",
        "alert_title": "KubeDaemonSetRolloutStuck",
        "service": "log-collector",
        "severity": "warning",
        "log_lines": [
            "WARN daemonset log-collector rollout stuck: 3/10 nodes updated",
            "ERROR pod log-collector-xyz failed: permission denied /var/log",
            "WARN updateStrategy maxUnavailable=1 blocking progress",
        ],
    },
]


def run_eval() -> None:
    """Call the API for each incident and save results for manual scoring."""
    print(f"Running LLM eval against {API_URL}")
    print(f"Total incidents: {len(INCIDENTS)}\n")

    # Check API is reachable
    try:
        resp = httpx.get("http://localhost:8000/health", timeout=5)
        resp.raise_for_status()
        print("✓ API is reachable\n")
    except Exception as e:
        print(f"✗ API not reachable: {e}")
        print("Start the API first: uvicorn opspilot.api.main:app --port 8000")
        sys.exit(1)

    results = []
    for i, incident in enumerate(INCIDENTS, 1):
        print(f"[{i:02d}/{len(INCIDENTS)}] {incident['incident_id']}: {incident['alert_title']}")
        t0 = time.perf_counter()
        try:
            resp = httpx.post(API_URL, json=incident, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            latency_ms = int((time.perf_counter() - t0) * 1000)

            results.append(
                {
                    "incident_id": incident["incident_id"],
                    "alert_title": incident["alert_title"],
                    "input": incident,
                    "output": data,
                    "latency_ms": latency_ms,
                    # Leave blank — you fill these in manually
                    "scores": {
                        "relevance": None,       # 1-5: did it address the actual incident?
                        "correctness": None,     # 1-5: are the actions technically valid?
                        "hallucination": None,   # 1-5: 5=no hallucination, 1=made things up
                        "completeness": None,    # 1-5: covered all steps to resolve?
                    },
                    "notes": "",
                }
            )
            print(f"     ✓ {latency_ms}ms | summary: {data.get('summary','')[:80]}...")
        except Exception as e:
            latency_ms = int((time.perf_counter() - t0) * 1000)
            results.append(
                {
                    "incident_id": incident["incident_id"],
                    "alert_title": incident["alert_title"],
                    "input": incident,
                    "output": None,
                    "latency_ms": latency_ms,
                    "error": str(e),
                    "scores": {
                        "relevance": None,
                        "correctness": None,
                        "hallucination": None,
                        "completeness": None,
                    },
                    "notes": "",
                }
            )
            print(f"     ✗ ERROR: {e}")

    Path("artifacts").mkdir(exist_ok=True)
    out_path = "artifacts/llm_eval_results.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)

    success = sum(1 for r in results if r.get("output"))
    print(f"\n{'='*60}")
    print(f"  Done: {success}/{len(INCIDENTS)} succeeded")
    print(f"  Results saved to: {out_path}")
    print(f"\n  Next step: open {out_path} and fill in scores (1-5)")
    print("  Then run: python scripts/eval/score_llm_eval.py")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_eval()
