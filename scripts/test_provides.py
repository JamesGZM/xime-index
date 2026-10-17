#!/usr/bin/env python3
"""provides 规范化的合成数据检查。不访问网络，也不改索引。"""

import io
import json
import zipfile

from lib import apply_provides, normalize_provides, provides_from_zip_bytes


def zip_with_manifest(manifest: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.json", json.dumps(manifest))
    return buf.getvalue()


def main():
    assert normalize_provides(None) is None
    assert normalize_provides([]) is None
    derived = normalize_provides([
        {"id": " fixture.read ", "version": 1, "name": "合成", "methods": ["process"]},
        {"id": "fixture.read", "version": 9},
        {"id": "fixture.other", "version": "2", "callers": ["host"]},
        {"id": "", "version": 1},
        "bad",
    ])
    assert derived == [
        {"id": "fixture.read", "version": 1},
        {"id": "fixture.other", "version": 2},
    ]

    blob = zip_with_manifest({
        "id": "fixture.reader",
        "type": "tool",
        "provides": [{"id": "fixture.read", "version": 1, "reason": "合成"}],
    })
    assert provides_from_zip_bytes(blob) == [{"id": "fixture.read", "version": 1}]
    assert provides_from_zip_bytes(b"not-a-zip") is None

    inline = apply_provides({
        "currentVersion": "1.0.0",
        "provides": [{"id": "fixture.read", "version": 1, "methods": ["process"]}],
        "versions": [{"version": "1.0.0", "downloadUrl": [{"url": "https://example.invalid/a.xipk"}]}],
    }, fetch=lambda url: (_ for _ in ()).throw(AssertionError("已有 provides 时不应下载")))
    assert inline["provides"] == [{"id": "fixture.read", "version": 1}]

    fetched = apply_provides({
        "pluginType": "context",
        "currentVersion": "1.0.0",
        "versions": [{"version": "1.0.0", "downloadUrl": [{"url": "https://example.invalid/a.xipk"}]}],
    }, fetch=lambda url: blob)
    assert fetched["provides"] == [{"id": "fixture.read", "version": 1}]
    assert fetched["pluginType"] == "context"

    missing = apply_provides({
        "currentVersion": "1.0.0",
        "versions": [{"version": "1.0.0", "downloadUrl": [{"url": "https://example.invalid/a.xipk"}]}],
    }, fetch=lambda url: zip_with_manifest({"id": "fixture.plain", "type": "tool"}))
    assert "provides" not in missing

    failed = apply_provides({
        "currentVersion": "1.0.0",
        "versions": [{"version": "1.0.0", "downloadUrl": [{"url": "https://example.invalid/a.xipk"}]}],
    }, fetch=lambda url: (_ for _ in ()).throw(OSError("合成失败")))
    assert "provides" not in failed
    print("ok")


if __name__ == "__main__":
    main()
