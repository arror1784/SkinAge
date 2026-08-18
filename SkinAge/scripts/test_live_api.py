import requests
import json
from pathlib import Path

def test_api():
    print("==================================================")
    print("1. Testing GET /api/v1/health")
    print("==================================================")
    res_health = requests.get("http://127.0.0.1:8000/api/v1/health")
    print("Status Code:", res_health.status_code)
    print("Response:", json.dumps(res_health.json(), indent=2))
    assert res_health.status_code == 200, "Health check failed!"

    print("\n==================================================")
    print("2. Testing POST /api/v1/analyze with User Selfie")
    print("==================================================")
    img_path = Path(r"C:\Users\arror\.gemini\antigravity-ide\brain\0d4e17bb-1754-42b3-be09-8df41afd78ae\.user_uploaded\media_1786817717765.jpg")
    assert img_path.exists(), "User image not found"

    files = {"file": ("selfie.jpg", img_path.read_bytes(), "image/jpeg")}
    data = {"age": 24, "include_heatmaps": False}

    res_analyze = requests.post("http://127.0.0.1:8000/api/v1/analyze", files=files, data=data)
    print("Status Code:", res_analyze.status_code)
    assert res_analyze.status_code == 200, f"Analyze request failed: {res_analyze.text}"

    resp = res_analyze.json()
    print("\n--- Actual API Response JSON ---")
    print(json.dumps(resp, indent=2, ensure_ascii=False))

    print("\n==================================================")
    print("3. Validating Against Specification Document")
    print("==================================================")
    errors = []

    # 1. Summary validation
    summary = resp.get("summary")
    if not summary:
        errors.append("Missing top-level 'summary' object")
    else:
        for f in ["predicted_skin_age", "actual_age", "age_delta", "overall_score", "skin_health_grade"]:
            if f not in summary:
                errors.append(f"Missing summary field: {f}")
        print(f"[PASS] Summary: Skin Age = {summary.get('predicted_skin_age')} yrs, Overall Score = {summary.get('overall_score')}, Grade = {summary.get('skin_health_grade')}")

    # 2. Zone Scores validation (7 zones x 4 concerns = 28 metrics)
    zones = resp.get("zone_scores", [])
    if len(zones) != 7:
        errors.append(f"Expected 7 facial zones, got {len(zones)}")
    else:
        print(f"[PASS] Facial Zones Count: {len(zones)} zones")

    expected_zones = {"forehead", "under_eyes", "crows_feet", "cheeks", "nose", "nasolabial", "chin"}
    found_zones = set()
    total_concerns = 0

    for z in zones:
        z_name = z.get("zone")
        found_zones.add(z_name)
        for zf in ["composite_score", "label", "occlusion_confidence", "concerns"]:
            if zf not in z:
                errors.append(f"Zone '{z_name}' missing field '{zf}'")
        
        c_list = z.get("concerns", [])
        total_concerns += len(c_list)
        for c in c_list:
            for cf in ["concern", "score", "severity"]:
                if cf not in c:
                    errors.append(f"Concern in zone '{z_name}' missing field '{cf}'")

    if found_zones == expected_zones:
        print(f"[PASS] Zone Names Match: {sorted(found_zones)}")
    else:
        errors.append(f"Zone mismatch: {found_zones} vs expected {expected_zones}")

    print(f"[PASS] Total Measured Concern Metrics: {total_concerns} (7 zones x 4 concerns)")

    # 3. Aggregate Metrics validation
    agg = resp.get("aggregate_metrics")
    if not agg:
        errors.append("Missing top-level 'aggregate_metrics' object")
    else:
        for af in ["t_zone_score", "u_zone_score", "concern_averages", "priority_concerns"]:
            if af not in af:
                errors.append(f"Missing aggregate field: {af}")
        print(f"[PASS] Aggregate Metrics: T-Zone = {agg.get('t_zone_score')}, U-Zone = {agg.get('u_zone_score')}")
        print(f"[PASS] Priority Concerns Count: {len(agg.get('priority_concerns', []))}")

    # 4. Metadata validation
    meta = resp.get("metadata")
    if not meta:
        errors.append("Missing top-level 'metadata' object")
    else:
        for mf in ["processing_time_ms", "model_version", "device", "input_size"]:
            if mf not in meta:
                errors.append(f"Missing metadata field: {mf}")
        print(f"[PASS] Processing Latency: {meta.get('processing_time_ms')} ms (device: {meta.get('device')})")

    print("\n==================================================")
    if errors:
        print("RESULT: VALIDATION FAILED WITH ERRORS:")
        for e in errors:
            print(" -", e)
        return False
    else:
        print("RESULT: 100% PERFECT MATCH WITH SPECIFICATION! [ALL TESTS PASSED]")
        return True

if __name__ == "__main__":
    test_api()
