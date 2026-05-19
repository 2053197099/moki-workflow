import json
import os
import urllib.error
import urllib.parse
import urllib.request


FEISHU_BASE = "https://open.feishu.cn"

APP_ID = os.environ.get("FEISHU_APP_ID")
APP_SECRET = os.environ.get("FEISHU_APP_SECRET")

SEED_APP = os.environ.get("MOKI_SEED_APP_TOKEN")
SEED_TABLE = os.environ.get("MOKI_SEED_TABLE_ID")
SEED_VIEW = os.environ.get("MOKI_SEED_VIEW_ID")

STYLE_APP = os.environ.get("MOKI_STYLE_APP_TOKEN")
STYLE_TABLE = os.environ.get("MOKI_STYLE_TABLE_ID")
STYLE_VIEW = os.environ.get("MOKI_STYLE_VIEW_ID")


def require_env(name, value):
    if not value:
        raise SystemExit(f"Set {name} before running this script.")


def request(method, path, token=None, payload=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        FEISHU_BASE + path,
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"code": exc.code, "msg": raw}


def tenant_token():
    require_env("FEISHU_APP_ID", APP_ID)
    require_env("FEISHU_APP_SECRET", APP_SECRET)
    body = request(
        "POST",
        "/open-apis/auth/v3/tenant_access_token/internal",
        payload={"app_id": APP_ID, "app_secret": APP_SECRET},
    )
    if body.get("code") != 0:
        raise SystemExit(json.dumps(body, ensure_ascii=False, indent=2))
    return body["tenant_access_token"]


def list_records(token, app_token, table_id, view_id):
    records = []
    page_token = ""
    while True:
        query = {"page_size": "100"}
        if view_id:
            query["view_id"] = view_id
        if page_token:
            query["page_token"] = page_token
        qs = urllib.parse.urlencode(query)
        path = f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?{qs}"
        body = request("GET", path, token=token)
        if body.get("code") != 0:
            raise SystemExit(json.dumps(body, ensure_ascii=False, indent=2))
        data = body.get("data", {})
        records.extend(data.get("items", []))
        page_token = data.get("page_token") or ""
        if not data.get("has_more") or not page_token:
            return records


def has_attachment(fields, field_name):
    value = fields.get(field_name)
    return isinstance(value, list) and len(value) > 0


def numeric(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    require_env("MOKI_SEED_APP_TOKEN", SEED_APP)
    require_env("MOKI_SEED_TABLE_ID", SEED_TABLE)
    require_env("MOKI_SEED_VIEW_ID", SEED_VIEW)
    require_env("MOKI_STYLE_APP_TOKEN", STYLE_APP)
    require_env("MOKI_STYLE_TABLE_ID", STYLE_TABLE)
    require_env("MOKI_STYLE_VIEW_ID", STYLE_VIEW)

    token = tenant_token()
    seed_records = list_records(token, SEED_APP, SEED_TABLE, SEED_VIEW)
    style_records = list_records(token, STYLE_APP, STYLE_TABLE, STYLE_VIEW)

    stats = {
        "种子总记录": len(seed_records),
        "种子编号已填": 0,
        "已评分": 0,
        "优秀种子_4分及以上": 0,
        "满分种子_5分": 0,
        "四类种子图齐全": 0,
        "评分分布": {},
        "风格表记录": len(style_records),
        "已有风格图": 0,
        "已有最终上传图": 0,
        "抖音截图已填": 0,
        "小红书截图已填": 0,
    }

    for record in seed_records:
        fields = record.get("fields", {})
        if fields.get("风格种子") not in (None, ""):
            stats["种子编号已填"] += 1
        rating = numeric(fields.get("评分"))
        if rating is not None:
            stats["已评分"] += 1
            key = str(int(rating)) if rating.is_integer() else str(rating)
            stats["评分分布"][key] = stats["评分分布"].get(key, 0) + 1
            if rating >= 4:
                stats["优秀种子_4分及以上"] += 1
            if rating >= 5:
                stats["满分种子_5分"] += 1
        if all(has_attachment(fields, name) for name in ["人", "动物", "建筑", "环境"]):
            stats["四类种子图齐全"] += 1

    for record in style_records:
        fields = record.get("fields", {})
        if any(has_attachment(fields, f"风格图{i}") for i in range(1, 7)):
            stats["已有风格图"] += 1
        if any(has_attachment(fields, f"最终上传图片{i}") for i in range(1, 7)):
            stats["已有最终上传图"] += 1
        if has_attachment(fields, "抖音上传截图"):
            stats["抖音截图已填"] += 1
        if has_attachment(fields, "小红书上传截图"):
            stats["小红书截图已填"] += 1

    print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
