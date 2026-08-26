#!/usr/bin/env bash
# S3 eventstore bulk load driver — run on a box in the bucket's region (GNU
# date), from this repo checkout at a pushed SHA:
#
#     GJK_DB_URL=<writer url> scripts/s3_bulk_load.sh
#
# PASS1=0 skips the layout pass (resume after it completed); DRY=1 lists,
# decodes and writes summaries without persisting; RUN sets the output dir
# (default runs/<UTC stamp> under the repo); WORKERS / BATCH tune the importer.
#
# Two forward passes from the population start (2024-10-13): layouts first
# over the whole span, then every other type. Each type's range ends
# strictly before its earliest messages.timestamp already in prod (queried,
# not hand-kept) so id-less types never double-load. Windows are weeks; each
# writes its importer summary JSON next to its log for the reconciliation.
#
# Needs GJK_DB_URL (writer) in the environment and AWS access to the bucket
# (instance role). Dry-run first.
set -euo pipefail
JK="$(cd "$(dirname "$0")/.." && pwd)"
RUN="${RUN:-$JK/runs/$(date -u +%Y%m%dT%H%M)}"
mkdir -p "$RUN"
START="${START:-2024-10-13}"  # override to resume a pass from a later day
IMPORT="uv run --project $JK python -m gjk.s3_message_importer --workers ${WORKERS:-16} --batch-size ${BATCH:-500} ${DRY:+--dry-run}"

# Earliest prod row per type, the day BEFORE it is each type's last import day.
floors="$RUN/floors.txt"
psql "${GJK_DB_URL/+psycopg2/}" -At -F' ' -c \
  "select message_type_name, (min(timestamp)::date - 1) from gridworks.messages group by 1" > "$floors"
floor_of() { awk -v t="$1" '$1==t {print $2}' "$floors"; }

weeks() {  # weeks START END -> "s e" lines
  local s="$1" e="$2"
  while [[ "$s" < "$e" || "$s" == "$e" ]]; do
    local n; n=$(date -u -d "$s +6 days" +%Y-%m-%d)
    [[ "$n" > "$e" ]] && n="$e"
    echo "$s $n"
    s=$(date -u -d "$n +1 day" +%Y-%m-%d)
  done
}

cd "$JK"
if [[ "${PASS1:-1}" == 1 ]]; then
echo "== pass 1: layout.lite $START → $(floor_of layout.lite)"
weeks "$START" "$(floor_of layout.lite)" | while read -r s e; do
  $IMPORT --start "$s" --end "$e" --message-types layout.lite --summary-json "$RUN/pass1_${s}_$e.json" > "$RUN/pass1_${s}_$e.log" 2>&1
done
fi

# Pass 2: every non-layout type up to the common floor in one listing pass,
# then only the late-floor types from the day after it to their own floors.
# gridworks.event.problem is never back-filled: the archive's pre-2026 volume
# is a device-fault flap (2.9M rows in three weeks of Dec 2024 - Jan 2025)
# and the history since Jan 2026 is enough.
SKIP="layout.lite,gridworks.event.problem"
common="$(awk '$1!="layout.lite" && $1!="gridworks.event.problem" {print $2}' "$floors" | sort | head -1)"
echo "== pass 2a: all but layout.lite $START → $common"
weeks "$START" "$common" | while read -r s e; do
  $IMPORT --start "$s" --end "$e" --message-types "~$SKIP" --summary-json "$RUN/pass2a_${s}_$e.json" > "$RUN/pass2a_${s}_$e.log" 2>&1
done
# Pass 2b: the late-floor types, grouped by floor date so each day is listed
# once per group, not once per type. gw.weather.* is skipped: the weather
# service began emitting in Aug 2026, there is nothing older in the store.
after_common=$(date -u -d "$common +1 day" +%Y-%m-%d)
late="$(awk -v c="$common" '$1!="layout.lite" && $1!="gridworks.event.problem" && $1!~/^gw\.weather\./ && $2>c {print $2, $1}' "$floors" | sort)"
start="$after_common"
for f in $(echo "$late" | awk '{print $1}' | sort -u); do
  types="$(echo "$late" | awk -v f="$f" '$1>=f {print $2}' | paste -sd, -)"
  echo "== pass 2b: $start → $f: $types"
  weeks "$start" "$f" | while read -r s e; do
    $IMPORT --start "$s" --end "$e" --message-types "$types" --summary-json "$RUN/pass2b_${s}_$e.json" > "$RUN/pass2b_${s}_$e.log" 2>&1
  done
  start=$(date -u -d "$f +1 day" +%Y-%m-%d)
done
echo "== done. Next: refresh readings_1hr over the range and rebuild cached_hourly_data (delete-then-insert) as the cagg owner; then scripts/replay_flo_params.py"
