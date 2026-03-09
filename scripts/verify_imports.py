"""Verify all OpsPilot modules can be imported without errors."""

import sys

modules = [
    "opspilot",
    "opspilot.api.main",
    "opspilot.api.schemas",
    "opspilot.api.deps",
    "opspilot.api.routes.health",
    "opspilot.api.routes.incident",
    "opspilot.api.routes.rag",
    "opspilot.api.routes.anomaly",
    "opspilot.api.routes.feedback",
    "opspilot.api.routes.admin",
    "opspilot.agent.prompts",
    "opspilot.agent.safety",
    "opspilot.agent.tools",
    "opspilot.agent.graph",
    "opspilot.rag.chunking",
    "opspilot.rag.index",
    "opspilot.rag.docstore",
    "opspilot.rag.bm25",
    "opspilot.rag.retriever",
    "opspilot.embeddings.encoder",
    "opspilot.anomaly.features",
    "opspilot.anomaly.infer",
    "opspilot.storage.db",
    "opspilot.storage.models",
    "opspilot.workflows.drift",
    "opspilot.observability.logging",
    "opspilot.observability.metrics",
]

errors = []
for mod in modules:
    try:
        __import__(mod)
        print(f"  ✅ {mod}")
    except Exception as e:
        print(f"  ❌ {mod}: {e}")
        errors.append((mod, str(e)))

print(f"\n{'='*50}")
if errors:
    print(f"❌ {len(errors)} import(s) FAILED:")
    for mod, err in errors:
        print(f"   {mod}: {err}")
    sys.exit(1)
else:
    print(f"✅ All {len(modules)} modules imported successfully!")
