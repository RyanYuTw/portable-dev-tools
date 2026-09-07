#!/usr/bin/env python3
import json
import sys
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# 參數
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 30
OUTPUT_DIR = os.path.expanduser(sys.argv[2] if len(sys.argv) > 2 else '~/Documents/TNL')

MEMBERS = {
    '65f917d5-1329-4b73-a462-2049fd53f3a7': 'Ryan',
    '65f919ee-cf06-437e-9b9e-868e80e71960': '小智',
    '65f941c1-57c6-45fc-875d-c00fff48f79f': 'Joyce',
    '67a1cfca-c087-4ad3-adee-29c420c98ba8': 'Angel',
}

STATE_MAP = {
    500009833: '待確認', 500009841: '觀察中', 500009826: '已確認待排程',
    500009827: '待執行', 500009828: '執行中', 500009840: 'Greenroom',
    500009829: 'Stage', 500009830: 'Sandbox', 500009832: 'Production',
    500009831: '已完成',
}

REVIEW_STATES = ['已完成', 'Production', 'Sandbox', 'Stage', 'Greenroom', '執行中']

# 讀取資料
stories_file = sys.argv[3] if len(sys.argv) > 3 else '/tmp/stories.json'
with open(stories_file, 'r') as f:
    all_stories = json.load(f)

# 計算日期範圍
today = datetime.now(timezone.utc)
start_date = today - timedelta(days=DAYS)

# 過濾近 N 天
recent_stories = []
for story in all_stories:
    updated_at_str = story.get('updated_at', '')
    if updated_at_str:
        try:
            updated_at = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
            if updated_at >= start_date and updated_at <= today:
                recent_stories.append(story)
        except:
            pass

# 過濾 Review 狀態
review_stories = []
for story in recent_stories:
    state = STATE_MAP.get(story['workflow_state_id'], '其他')
    if state in REVIEW_STATES:
        review_stories.append(story)

# 按專案分組
by_project = defaultdict(list)

for story in review_stories:
    name = story.get('name', '')
    if name.startswith('[') and ']' in name:
        project_name = name[1:name.index(']')]
        story_name = name[name.index(']')+1:].strip()
    else:
        project_name = '其他'
        story_name = name

    owner_names = [MEMBERS[owner] for owner in story.get('owner_ids', []) if owner in MEMBERS]
    owners_str = ', '.join(owner_names) if owner_names else '未指派'
    state = STATE_MAP.get(story['workflow_state_id'], '其他')

    by_project[project_name].append({
        'name': story_name,
        'state': state,
        'owners': owners_str,
        'id': story['id'],
        'updated_at': story.get('updated_at', ''),
    })

# 生成 Markdown
output_md = os.path.join(OUTPUT_DIR, f'會議記錄_{today.strftime("%m-%d")}_IT_Review.md')

with open(output_md, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write(f"會議記錄: {today.strftime('%m/%d')} - IT Team Review\n")
    f.write("=" * 80 + "\n\n")
    f.write("## 大綱\n\n")
    f.write("- 與會人: Joyce, 小智, Ryan, Angel\n")
    f.write(f"- 會議日期: {today.strftime('%Y年%m月%d日')}\n")
    f.write(f"- 統計期間: {start_date.strftime('%Y年%m月%d日')} ~ {today.strftime('%Y年%m月%d日')}\n")
    f.write("- 會議目標: 回顧近期工作成果與進度\n\n")
    f.write("-" * 80 + "\n\n")
    f.write("## 會議記錄\n\n")

    # 按專案輸出
    for project in sorted(by_project.keys()):
        stories = by_project[project]
        if not stories:
            continue

        f.write(f"### {project}\n\n")

        # 按狀態分組
        by_state = defaultdict(list)
        for story in stories:
            by_state[story['state']].append(story)

        # 狀態順序
        state_order = ['已完成', 'Production', 'Sandbox', 'Stage', 'Greenroom', '執行中']

        for state in state_order:
            if state not in by_state:
                continue

            for story in sorted(by_state[state], key=lambda x: x['updated_at'], reverse=True):
                state_marker = f"→ {state}" if state != '已完成' else "→ 已完成"
                f.write(f"- {story['name']} {state_marker} / {story['owners']}\n")

        f.write("\n")

    f.write("-" * 80 + "\n\n")
    f.write("## 討論\n\n\n\n")
    f.write("## 心情\n\n")

# 輸出統計
print(json.dumps({
    'success': True,
    'markdown': output_md,
    'stats': {
        'days': DAYS,
        'total': len(all_stories),
        'recent': len(recent_stories),
        'review': len(review_stories),
        'projects': len(by_project),
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d'),
    }
}, ensure_ascii=False))
