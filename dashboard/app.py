import os

import httpx
import streamlit as st

API = os.getenv("API_URL", "https://ananya-cloud-ai-orchestration-platform.onrender.com")
if not API.startswith("http"):
    API = f"https://{API}"

st.set_page_config(page_title="Cloud AI Orchestration", layout="wide")
st.title("Cloud AI Orchestration Platform")
st.caption("Multi-stage workflows · idempotency · HITL · AWS/Azure deployment patterns")

api = st.text_input("API URL", API).rstrip("/")

if st.button("Start AI Data Pipeline", type="primary"):
    resp = httpx.post(f"{api}/workflows", json={"input_payload": {"source": "dashboard"}}, timeout=60)
    st.session_state["run"] = resp.json()

if "run" in st.session_state:
    run = st.session_state["run"]
    st.json(run)
    if run.get("status") == "awaiting_human":
        if st.button("Approve human review"):
            r = httpx.post(f"{api}/workflows/{run['run_id']}/approve", json={"approved": True}, timeout=60)
            st.session_state["run"] = r.json()
            st.rerun()

st.divider()
try:
    runs = httpx.get(f"{api}/workflows", timeout=30).json()
    for r in runs[:5]:
        st.write(f"`{r['run_id'][:8]}` · {r['status']} · {r['definition_name']}")
except httpx.HTTPError as exc:
    st.warning(str(exc))
