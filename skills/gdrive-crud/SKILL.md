---
name: gdrive-crud
description: "使用 Google Service Account 對 Google Drive 檔案進行 CRUD（列出、上傳、下載、更新、刪除、建立資料夾、分享）。當使用者要求連線/操作 Google Drive、上傳或下載雲端硬碟檔案、列出雲端硬碟內容時使用。需要 GDRIVE_SA_KEY_PATH 環境變數指向服務帳號金鑰檔。"
license: MIT
metadata:
  author: user
  version: 1.0.0
---

# Google Drive CRUD Skill

透過 Google Service Account 直接呼叫 Drive API v3，對檔案／資料夾做完整 CRUD。腳本位於 `scripts/gdrive.py`。

## 前置準備（使用者需自行完成一次）

1. 到 Google Cloud Console 建立專案，啟用 **Google Drive API**。
2. 建立 **Service Account**，下載其 JSON 金鑰檔（**不要**放進 git 追蹤的目錄）。
3. 記下金鑰檔中的 `client_email`（例如 `xxx@yyy.iam.gserviceaccount.com`）。
4. 到 Google Drive，把要操作的資料夾（或 Shared Drive）**分享給這個 service account email**（至少「編輯者」權限）。
   - 這一步必要：Service Account 有自己獨立、人看不到的 Drive 空間；沒有分享的話，即使呼叫成功，使用者也在自己的 Drive UI 中看不到檔案。
5. 設定環境變數（每次 shell session，或寫入 `~/.zshrc`）：
   ```bash
   export GDRIVE_SA_KEY_PATH="/絕對路徑/service-account-key.json"
   ```
6. 安裝依賴：
   ```bash
   pip install -r ~/.claude/skills/gdrive-crud/requirements.txt
   ```

## 使用時機

使用者提到「連線 Google Drive」「上傳/下載到雲端硬碟」「列出 Drive 檔案」「刪除/更新 Drive 上的檔案」「分享 Drive 檔案」時觸發。

## 指令

所有指令都透過：
```bash
python3 ~/.claude/skills/gdrive-crud/scripts/gdrive.py <command> [options]
```

若使用者未設定 `GDRIVE_SA_KEY_PATH`，可用 `--key-file <path>` 明確指定。

### 列出檔案
```bash
python3 gdrive.py list --folder-id <FOLDER_ID> --limit 50
```
不帶 `--folder-id` 時列出 service account 可見的所有檔案（通常是已分享的資料夾內容）。可用 `--query` 加 Drive query 語法，例如 `--query "name contains 'report'"`。

### 上傳檔案
```bash
python3 gdrive.py upload ./local/path/file.pdf --folder-id <FOLDER_ID> --name "自訂檔名.pdf"
```

### 下載檔案
```bash
python3 gdrive.py download <FILE_ID> --output ./local/save/path.pdf
```
若目標是 Google 原生文件（文件/試算表/簡報），需用 `--export-mime-type` 指定匯出格式（預設 `application/pdf`）。

### 更新檔案（改名 / 換內容 / 換資料夾）
```bash
python3 gdrive.py update <FILE_ID> --name "新檔名.pdf"
python3 gdrive.py update <FILE_ID> --content ./local/new-version.pdf
python3 gdrive.py update <FILE_ID> --add-parent <NEW_FOLDER_ID> --remove-parent <OLD_FOLDER_ID>
```

### 刪除檔案
```bash
python3 gdrive.py delete <FILE_ID>            # 永久刪除
python3 gdrive.py delete <FILE_ID> --trash    # 移至垃圾桶
```

### 建立資料夾
```bash
python3 gdrive.py mkdir "新資料夾" --folder-id <PARENT_FOLDER_ID>
```

### 查看檔案詳細資訊
```bash
python3 gdrive.py info <FILE_ID>
```

### 分享檔案
```bash
python3 gdrive.py share <FILE_ID> someone@example.com --role writer --notify
```

## 錯誤排除

- `404 File not found`：該資料夾/檔案未分享給 service account 的 `client_email`，先到 Drive 分享。
- `insufficientPermissions`：分享權限不足（只有檢視者但嘗試寫入），到 Drive 提升為編輯者。
- 上傳後在自己 Drive 找不到檔案：確認上傳時有帶 `--folder-id` 指向已分享的資料夾，否則檔案會落在 service account 自己的空間。
- 若要操作 Shared Drive（共用雲端硬碟），把 Shared Drive 的 ID 當作 `--folder-id` 使用即可，腳本已加上 `supportsAllDrives=True`。

## 安全注意事項

- 金鑰 JSON 檔含長期有效的憑證，絕對不要 commit 進 git，也不要貼在對話或任何會被記錄的地方。
- 若懷疑金鑰外洩，立即到 Google Cloud Console 停用該 service account 的金鑰。
