import argparse
import json
import sys
from datetime import date, timedelta

parser = argparse.ArgumentParser()
parser.add_argument('--date1', type=date.fromisoformat, default='2008-05-17',
                    help='One end (inclusive) of date range to search (default: %(default)s)')
parser.add_argument('--date2', type=date.fromisoformat, default=date.today(),
                    help='Other end (exclusive) of date range to search (default: %(default)s). '
                         'If earlier than date1, search will run backwards in time.')
parser.add_argument('--minlength', type=int, default=14,
                    help='Minimum length of streak to report (default: %(default)s)')
args = parser.parse_args()

step = timedelta(days=1) if args.date2 > args.date1 else timedelta(days=-1)

# Assume expedition data ends up as a list of
# {date: {participant: expedition}}}
expeditions = {}

# https://fippe.de/alldata.js
with open('alldata.js') as js:
  json_str = js.read()
  # Skip trailing comma
  json_str = json_str[json_str.find('['):json_str.rfind(']')-2] + ']'
  for expedition in json.loads(json_str):
    title = expedition[0]
    day_str = title[0:10]
    day = date.fromisoformat(day_str)
    participants = expedition[3]
    success = expedition[4]
    if success:
      expeditions.setdefault(day, {}).update({p: title for p in participants})

print("Loaded", len(expeditions), "expeditions", file=sys.stderr)

def find_streaks(day, participants_seen, sequence):
  participants_day = expeditions.get(day, {})
  for participant in set(participants_day.keys()).difference(participants_seen):
    yield from find_streaks(day + step, participants_seen.union([participant]), [*sequence, (participant, participants_day[participant])])
  else:
    yield sequence

print('{| class="wikitable sortable"')
print("|-")
print("! Starting")
print("! Days")
print("! Example")
start_date = args.date1
seen_end_dates = set() # Suppress sub-streaks
while start_date != args.date2:
  print("Trying", start_date, file=sys.stderr)
  some_longest_sequence = max(find_streaks(start_date, set(), []), key=lambda s: len(s))
  longest_length = len(some_longest_sequence)
  end_date = start_date + step*longest_length
  if longest_length >= args.minlength and end_date not in seen_end_dates:
    seen_end_dates.add(end_date)
    print("|-")
    print("|", start_date)
    print("|", longest_length)
    print("|", end="")
    for participant, expedition in some_longest_sequence:
      print(" [[", expedition, "|", participant, "]],", sep="", end="")
    print(flush=True)
  start_date += step
print("|}")
