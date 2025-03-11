import json
import sys
from datetime import date, timedelta

# Incomplete streaks currently under consideration. Each is
# (date, graticule, {
#  frozenset(participants): [participant, ...],
#  ...
# })
# Later we can add an optional graticule to the tuple.
streaks = []

# Assume expedition data ends up as a list of
# {date: {graticule: [participants]}}
expeditions = {}
#    "2025-01-01": {"52 13": ["C"]},
#    "2025-01-02": {"52 13": ["A", "B"]},
#    "2025-01-03": {"52 13": ["A", "B"]},
#    "2025-01-04": {"52 13": ["C"]},
#    "2025-01-05": {"52 13": ["D", "E"]},
#    "2025-01-06": {"52 13": ["D", "E"]},
#    "2025-01-07": {"52 13": ["C"]},
#}

with open('alldata.js') as js:
  json_str = js.read()
  # Skip trailing comma
  json_str = json_str[json_str.find('['):json_str.rfind(']')-2] + ']'
  for expedition in json.loads(json_str):
    day_str = expedition[0][0:10]
    graticule = expedition[0][11:]
    participants = expedition[3]
    success = expedition[4]
    if success and participants:
      expeditions.setdefault(day_str, {})[graticule] = participants

print("Loaded", len(expeditions), "expeditions", file=sys.stderr)

day = date(2008, 5, 17)
while day <= date.today(): #>= date(2008, 5, 1):
  day_str = day.isoformat()
  expeditions_day = expeditions.get(day_str, {})
  #print(day_str, ":", sum(len(ps) for ps in expeditions_day.values()), "participants", file=sys.stderr)

  # Try extending current streaks
  extended_streaks = []
  for (start_date, graticule, groups) in streaks:
    extended_groups = {}
    for ps, es in groups.items():
      for new_p in expeditions_day.get(graticule, []):
        if new_p not in ps:
          # We can grow the group!
          extended_ps = frozenset({*ps, new_p})
          if extended_ps not in extended_groups:
            # If we found a different way to build the same group, ignore this
            extended_groups[extended_ps] = [*es, new_p]
    if extended_groups:
      if len(extended_groups) > 100000:
        print("warning:", len(extended_groups), "possible groups from", start_date, "to", day_str)
      extended_streaks.append((start_date, graticule, extended_groups))
    else:
      # Current streaks were maximal, report one
      example_group = next(iter(groups.values()))
      if len(example_group) >= 4:
        print(start_date, graticule, len(groups), len(example_group), example_group)

  streaks = extended_streaks

  # Start a new streak
  for g, ps in expeditions_day.items():
    streaks.append((day_str, g, {frozenset([p]): [p] for p in ps}))

  # Advance
  day += timedelta(days=1)

