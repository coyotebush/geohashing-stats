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
parser.add_argument('--graticule', action='append',
                    help='Only consider expeditions in this graticule (can be repeated). '
                         'Example: --graticule=-37_144 --graticule=-37_145')
parser.add_argument('-v', '--verbose', action='count', default=0)
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
    graticule = title[11:]
    day = date.fromisoformat(day_str)
    participants = expedition[3]
    success = expedition[4]
    if success and (args.graticule is None or graticule in args.graticule):
      expeditions.setdefault(day, {}).update({p: title for p in participants})

print("Loaded", len(expeditions), "expeditions", file=sys.stderr)

def find_streaks(day, participants_seen, sequence):
  if args.verbose >= 2:
    print("Visiting", day, end='\r', file=sys.stderr)
  participants_day = expeditions.get(day, {})
  for participant in set(participants_day.keys()).difference(participants_seen):
    yield from find_streaks(day + step, participants_seen.union([participant]), [*sequence, (participant, participants_day[participant])])
  else:
    yield len(participants_day) == 0, sequence

print('{| class="wikitable sortable"')
print("|-")
print("! Starting")
print("! Days")
print("! Example")
start_date = args.date1
seen_end_dates = set() # Suppress sub-streaks
while start_date != args.date2:
  if args.verbose >= 1:
    print("Starting from", start_date, file=sys.stderr)
  some_longest_sequence = []
  for final, sequence in find_streaks(start_date, set(), []):
    if len(sequence) > len(some_longest_sequence):
      some_longest_sequence = sequence
      if final:
        break

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
