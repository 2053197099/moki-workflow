import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request


FEISHU_BASE = "https://open.feishu.cn"

APP_ID = os.environ.get("FEISHU_APP_ID")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET")

SEED_APP = os.environ.get("MOKI_SEED_APP_TOKEN")
SEED_TABLE = os.environ.get("MOKI_SEED_TABLE_ID")

STYLE_APP = os.environ.get("MOKI_STYLE_APP_TOKEN")
STYLE_TABLE = os.environ.get("MOKI_STYLE_TABLE_ID")

EXPECTED_SEED_FIELDS = ["风格种子", "人", "动物", "建筑", "环境", "评分", "建立时间", "种子状态"]
EXPECTED_STYLE_FIELDS = [
    "风格种子",
    "风格图1",
    "风格图2",
    "风格图3",
    "风格图4",
    "风格图5",
    "风格图6",
    "发布状态",
    "最终上传图片1",
    "最终上传图片2",
    "最终上传图片3",
    "最终上传图片4",
    "最终上传图片5",
    "最终上传图片6",
    "抖音上传截图",
    "小红书上传截图",
]


def request(method, path, token=None, payload=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(FEISHU_BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, {"code": exc.code, "msg": raw}


def tenant_token():
    if not APP_ID or not APP_SECRET:
        return None, "FEISHU_APP_ID and FEISHU_APP_SECRET are required"
    status, body = request(
        "POST",
        "/open-apis/auth/v3/tenant_access_token/internal",
        payload={"app_id": APP_ID, "app_secret": APP_SECRET},
    )
    if body.get("code") != 0:
        return None, f"token failed: {status} {body.get('code')} {body.get('msg')}"
    return body["tenant_access_token"], None


def fields(token, app_token, table_id):
    status, body = request(
        "GET",
        f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields?page_size=100",
        token=token,
    )
    if body.get("code") != 0:
        raise RuntimeError(f"field read failed: {status} {body.get('code')} {body.get('msg')}")
    return [item.get("field_name") for item in body.get("data", {}).get("items", [])]


def validate_midjourney_command(command, kind):
    validator = os.environ.get("MOKI_MJ_VALIDATOR")
    if validator and os.path.exists(validator):
        args = ["python", validator, "validate", command]
        if kind != "seed":
            args.extend(["--type", kind])
        result = subprocess.run(args, text=True, encoding="utf-8", errors="replace", capture_output=True)
        return {"ok": result.returncode == 0, "detail": result.stdout.strip() or result.stderr.strip()}

    patterns = {
        "seed": r"^1 --sref random --ar 1:1$",
        "category": r"^(person|animal|architecture|environment) --ar 1:1 --sref \d+$",
        "production": r"^.+ --ar 9:16 --sref \d+$",
    }
    return {"ok": bool(re.match(patterns[kind], command)), "detail": "built-in validation"}


def run_stats():
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        [sys.executable, "moki_feishu_stats.py"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
    )
    if result.returncode != 0:
        return {"ok": False, "error": result.stderr.strip() or result.stdout.strip()}
    return {"ok": True, "stats": json.loads(result.stdout)}


def main():
    report = {
        "midjourney_commands": {
            "seed": validate_midjourney_command("1 --sref random --ar 1:1", "seed"),
            "category": validate_midjourney_command("person --ar 1:1 --sref 2735878167", "category"),
            "production": validate_midjourney_command("sacred snowy mountain --ar 9:16 --sref 2735878167", "production"),
        },
        "feishu": {},
    }

    token, error = tenant_token()
    if not token:
        report["feishu"]["ok"] = False
        report["feishu"]["error"] = error
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    missing_env = [
        name
        for name, value in {
            "MOKI_SEED_APP_TOKEN": SEED_APP,
            "MOKI_SEED_TABLE_ID": SEED_TABLE,
            "MOKI_STYLE_APP_TOKEN": STYLE_APP,
            "MOKI_STYLE_TABLE_ID": STYLE_TABLE,
        }.items()
        if not value
    ]
    if missing_env:
        report["feishu"]["ok"] = False
        report["feishu"]["missing_env"] = missing_env
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1

    seed_fields = fields(token, SEED_APP, SEED_TABLE)
    style_fields = fields(token, STYLE_APP, STYLE_TABLE)
    report["feishu"]["seed_table"] = {
        "fields_present": sorted(set(seed_fields) & set(EXPECTED_SEED_FIELDS)),
        "fields_missing": sorted(set(EXPECTED_SEED_FIELDS) - set(seed_fields)),
    }
    report["feishu"]["style_table"] = {
        "fields_present": sorted(set(style_fields) & set(EXPECTED_STYLE_FIELDS)),
        "fields_missing": sorted(set(EXPECTED_STYLE_FIELDS) - set(style_fields)),
    }
    report["stats"] = run_stats()

    print(json.dumps(report, ensure_ascii=False, indent=2))
    missing = report["feishu"]["seed_table"]["fields_missing"] or report["feishu"]["style_table"]["fields_missing"]
    command_failed = not all(item["ok"] for item in report["midjourney_commands"].values())
    stats_failed = not report["stats"]["ok"]
    return 1 if missing or command_failed or stats_failed else 0


if __name__ == "__main__":
    sys.exit(main())
