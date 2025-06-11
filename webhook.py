from flask import Flask, request, jsonify
import base64
import json
from kubernetes import client, config

app = Flask(__name__)

# Load in-cluster config
config.load_incluster_config()
k8s = client.CoreV1Api()

@app.route("/mutate", methods=["POST"])
def mutate():
    req = request.get_json()
    pod = req["request"]["object"]
    namespace = req["request"]["namespace"]
    uid = req["request"]["uid"]

    try:
        ns = k8s.read_namespace(name=namespace)
        labels = ns.metadata.labels or {}
        node_selector_value = labels.get("nfvcl-area")
    except Exception as e:
        print(f"Failed to read namespace {namespace}: {e}")
        return admission_review(uid, [])  # Don't block pod creation

    if not node_selector_value:
        return admission_review(uid, [])  # Skip mutation if label is not set

    patch = [{
        "op": "add",
        "path": "/spec/nodeSelector",
        "value": {
            "area": node_selector_value
        }
    }]

    return admission_review(uid, patch)

def admission_review(uid, patch):
    response = {
        "apiVersion": "admission.k8s.io/v1",
        "kind": "AdmissionReview",
        "response": {
            "uid": uid,
            "allowed": True,
            "patchType": "JSONPatch",
            "patch": base64.b64encode(json.dumps(patch).encode()).decode()
        }
    }
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=443, ssl_context=('/certs/tls.crt', '/certs/tls.key'))
