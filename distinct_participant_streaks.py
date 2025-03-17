import argparse
import json
import time
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
parser.add_argument('--same-graticule', action='store_true',
                    help='Only consider streaks within the same graticule.')
parser.add_argument('--timeout', type=float, default='inf',
                    help='Maximum time, in seconds, to spend on each date.')
parser.add_argument('-v', '--verbose', action='count', default=0)
args = parser.parse_args()

step = timedelta(days=1) if args.date2 > args.date1 else timedelta(days=-1)

# Assume expedition data ends up as a list of
# {date: {participant: expedition}}}
# For same-graticule mode:
# {graticule: {date: {participant: expedition}}}
all_expeditions = {}

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
      participant_map = {p: title for p in participants}
      if args.same_graticule:
        all_expeditions.setdefault(graticule, {}).setdefault(day, {}).update(participant_map)
      else:
        all_expeditions.setdefault(day, {}).update(participant_map)

print("Loaded expeditions for", len(all_expeditions),
      "graticules" if args.same_graticule else "dates",
      file=sys.stderr)

def find_longest_streak(expeditions, start_time, day, participants_seen, sequence):
  """
  Returns the longest possible streak within the expeditions that can be found within the timeout,
  starting on the given day, not using any of the participants_seen, and appended to a previous sequence.
  Also returns the set of participants whose presence in participants_seen (or some extended
  version thereof) directly or indirectly led to running out of ways to continue a streak.
  Finally, returns whether the timeout was reached before potentially finding a longer streak.
  """
  if args.verbose >= 2:
    print("Visiting", day, "without", "".join(p[0] for (p, _e) in sequence), end='\x1b[0K\r', file=sys.stderr)
  expeditions_day = expeditions.get(day, {})
  participants_day = set(expeditions_day.keys())
  participants_available = participants_day.difference(participants_seen)
  participants_unavailable = participants_day.intersection(participants_seen)

  if time.process_time() - start_time > args.timeout:
    # Timed out
    return sequence, participants_unavailable, True

  if not participants_available:
    # Report who would need to be available to continue the streak
    return sequence, participants_day, False

  limiting_participants = set()

  longest_sequence = sequence

  for participant in participants_available:
    complete_sequence, next_participants, timed_out \
        = find_longest_streak(expeditions,
                              start_time,
                              day + step,
                              participants_seen.union([participant]),
                              [*sequence, (participant, expeditions_day[participant])])
    if len(complete_sequence) > len(longest_sequence):
      longest_sequence = complete_sequence

    limiting_participants.update(next_participants)
    if timed_out:
      return longest_sequence, limiting_participants, True
    if participant in next_participants:
      # Choices that were unavailable to us might also be relevant
      limiting_participants.update(participants_unavailable)
      # Here we could omit participant from limiting_participants, but
      # it doesn't matter for correctness - no other invocation in the stack
      # is going to check for it anyway. (This might be more obvious if we
      # tracked limiting choice *dates* rather than values.)
      # It's easier to keep, and useful diagnostic information in the end.
    else:
      # No use continuing this loop!
      break
  return longest_sequence, limiting_participants, False

def upper_bound_streaks(expeditions, day):
  participants_count_day = len(expeditions.get(day, {}))
  if participants_count_day:
    return participants_count_day * upper_bound_streaks(expeditions, day + step)
  else:
    return 1

def print_longest_streak(seen_end_dates, expeditions, start_date):
  if args.verbose >= 1:
    print("Starting from", start_date, file=sys.stderr)
    print("Estimated possible sequences:", upper_bound_streaks(expeditions, start_date), file=sys.stderr)
  some_longest_sequence, limiting_participants, timed_out = find_longest_streak(expeditions, time.process_time(), start_date, set(), [])
  if args.verbose >= 1:
    print("Limited by", limiting_participants, file=sys.stderr) # To make sure there are some non-trivial cases

  longest_length = len(some_longest_sequence)
  end_date = start_date + step*longest_length
  if longest_length >= args.minlength and end_date not in seen_end_dates:
    seen_end_dates.add(end_date)
    print("|-")
    print("|", start_date)
    print("|", longest_length, "+" if timed_out else "")
    print("|", end="")
    for participant, expedition in some_longest_sequence:
      print(" [[", expedition, "|", participant, "]],", sep="", end="")
    print(flush=True)

print('{| class="wikitable sortable"')
print("|-")
print("! Starting")
print("! Days")
print("! Example")
start_date = args.date1
if args.same_graticule:
  graticule_seen_end_dates = {}
  while start_date != args.date2:
    for graticule, graticule_expeditions in all_expeditions.items():
      print_longest_streak(graticule_seen_end_dates.setdefault(graticule, set()),
                           graticule_expeditions, start_date)
    start_date += step
else:
  all_seen_end_dates = set() # Suppress sub-streaks
  while start_date != args.date2:
    print_longest_streak(all_seen_end_dates, all_expeditions, start_date)
    start_date += step
print("|}")
