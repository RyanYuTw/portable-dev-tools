#!/usr/bin/env python3
"""Google Drive CRUD CLI backed by a Service Account.

Auth: set GDRIVE_SA_KEY_PATH (or pass --key-file) to the service account
JSON key path. The target folder/Shared Drive must be shared with the
service account's client_email, otherwise the service account cannot see it
(files uploaded with no --folder-id land in the service account's own,
invisible-to-humans Drive).
"""
import argparse
import io
import os
import sys

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

SCOPES = ["https://www.googleapis.com/auth/drive"]
FOLDER_MIME = "application/vnd.google-apps.folder"


def get_service(key_file):
    key_file = key_file or os.environ.get("GDRIVE_SA_KEY_PATH")
    if not key_file:
        sys.exit("錯誤：未提供服務帳號金鑰。請設定 GDRIVE_SA_KEY_PATH 或使用 --key-file")
    if not os.path.isfile(key_file):
        sys.exit(f"錯誤：找不到金鑰檔案 {key_file}")
    creds = service_account.Credentials.from_service_account_file(key_file, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def cmd_list(svc, args):
    q_parts = []
    if args.folder_id:
        q_parts.append(f"'{args.folder_id}' in parents")
    if args.query:
        q_parts.append(args.query)
    if not args.trashed:
        q_parts.append("trashed = false")
    query = " and ".join(q_parts) if q_parts else None

    results = svc.files().list(
        q=query,
        pageSize=args.limit,
        fields="files(id, name, mimeType, size, modifiedTime, parents)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
        corpora="allDrives",
    ).execute()
    files = results.get("files", [])
    if not files:
        print("(無檔案)")
        return
    for f in files:
        kind = "📁" if f["mimeType"] == FOLDER_MIME else "📄"
        size = f.get("size", "-")
        print(f"{kind} {f['id']}  {f['name']}  size={size}  modified={f.get('modifiedTime','')}")


def cmd_upload(svc, args):
    if not os.path.isfile(args.local_path):
        sys.exit(f"錯誤：找不到本機檔案 {args.local_path}")
    metadata = {"name": args.name or os.path.basename(args.local_path)}
    if args.folder_id:
        metadata["parents"] = [args.folder_id]
    media = MediaFileUpload(args.local_path, mimetype=args.mime_type, resumable=True)
    f = svc.files().create(
        body=metadata, media_body=media, fields="id, name, webViewLink",
        supportsAllDrives=True,
    ).execute()
    print(f"已上傳：{f['name']}  id={f['id']}  {f.get('webViewLink','')}")


def cmd_download(svc, args):
    meta = svc.files().get(fileId=args.file_id, fields="name, mimeType", supportsAllDrives=True).execute()
    output = args.output or meta["name"]

    if meta["mimeType"].startswith("application/vnd.google-apps"):
        export_mime = args.export_mime_type or "application/pdf"
        request = svc.files().export_media(fileId=args.file_id, mimeType=export_mime)
    else:
        request = svc.files().get_media(fileId=args.file_id, supportsAllDrives=True)

    fh = io.FileIO(output, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    print(f"已下載至：{output}")


def cmd_update(svc, args):
    metadata = {}
    if args.name:
        metadata["name"] = args.name

    kwargs = {"fileId": args.file_id, "fields": "id, name, parents", "supportsAllDrives": True}
    if metadata:
        kwargs["body"] = metadata
    if args.content:
        if not os.path.isfile(args.content):
            sys.exit(f"錯誤：找不到本機檔案 {args.content}")
        kwargs["media_body"] = MediaFileUpload(args.content, resumable=True)
    if args.add_parent:
        kwargs["addParents"] = args.add_parent
    if args.remove_parent:
        kwargs["removeParents"] = args.remove_parent

    f = svc.files().update(**kwargs).execute()
    print(f"已更新：{f['name']}  id={f['id']}")


def cmd_delete(svc, args):
    if args.trash:
        svc.files().update(fileId=args.file_id, body={"trashed": True}, supportsAllDrives=True).execute()
        print(f"已移至垃圾桶：{args.file_id}")
    else:
        svc.files().delete(fileId=args.file_id, supportsAllDrives=True).execute()
        print(f"已永久刪除：{args.file_id}")


def cmd_mkdir(svc, args):
    metadata = {"name": args.name, "mimeType": FOLDER_MIME}
    if args.folder_id:
        metadata["parents"] = [args.folder_id]
    f = svc.files().create(body=metadata, fields="id, name", supportsAllDrives=True).execute()
    print(f"已建立資料夾：{f['name']}  id={f['id']}")


def cmd_info(svc, args):
    f = svc.files().get(
        fileId=args.file_id,
        fields="id, name, mimeType, size, modifiedTime, parents, owners, webViewLink",
        supportsAllDrives=True,
    ).execute()
    for k, v in f.items():
        print(f"{k}: {v}")


def cmd_share(svc, args):
    perm = {"type": "user", "role": args.role, "emailAddress": args.email}
    svc.permissions().create(
        fileId=args.file_id, body=perm, sendNotificationEmail=args.notify, supportsAllDrives=True,
    ).execute()
    print(f"已將 {args.file_id} 以 {args.role} 權限分享給 {args.email}")


def main():
    parser = argparse.ArgumentParser(description="Google Drive CRUD CLI (Service Account)")
    parser.add_argument("--key-file", help="服務帳號 JSON 金鑰路徑（預設讀取 GDRIVE_SA_KEY_PATH）")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="列出檔案")
    p.add_argument("--folder-id")
    p.add_argument("--query", help="額外的 Drive query 條件")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--trashed", action="store_true", help="包含已在垃圾桶的檔案")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("upload", help="上傳檔案")
    p.add_argument("local_path")
    p.add_argument("--folder-id")
    p.add_argument("--name")
    p.add_argument("--mime-type")
    p.set_defaults(func=cmd_upload)

    p = sub.add_parser("download", help="下載檔案")
    p.add_argument("file_id")
    p.add_argument("--output")
    p.add_argument("--export-mime-type", help="Google 原生文件（文件/試算表等）匯出格式")
    p.set_defaults(func=cmd_download)

    p = sub.add_parser("update", help="更新檔名/內容/所在資料夾")
    p.add_argument("file_id")
    p.add_argument("--name")
    p.add_argument("--content", help="以此本機檔案取代內容")
    p.add_argument("--add-parent", help="新增到此資料夾")
    p.add_argument("--remove-parent", help="從此資料夾移除")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("delete", help="刪除檔案")
    p.add_argument("file_id")
    p.add_argument("--trash", action="store_true", help="移至垃圾桶而非永久刪除")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("mkdir", help="建立資料夾")
    p.add_argument("name")
    p.add_argument("--folder-id")
    p.set_defaults(func=cmd_mkdir)

    p = sub.add_parser("info", help="查看檔案詳細資訊")
    p.add_argument("file_id")
    p.set_defaults(func=cmd_info)

    p = sub.add_parser("share", help="分享檔案給指定 email")
    p.add_argument("file_id")
    p.add_argument("email")
    p.add_argument("--role", default="reader", choices=["reader", "writer", "commenter"])
    p.add_argument("--notify", action="store_true")
    p.set_defaults(func=cmd_share)

    args = parser.parse_args()
    svc = get_service(args.key_file)
    args.func(svc, args)


if __name__ == "__main__":
    main()
