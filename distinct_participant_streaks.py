import json
import sys
from datetime import date, timedelta

# Assume expedition data ends up as a list of
# {date: {graticule: [participants]}}
expeditions = {}

with open('alldata.js') as js:
  json_str = js.read()
  # Skip trailing comma
  json_str = json_str[json_str.find('['):json_str.rfind(']')-2] + ']'
  print(json_str[-20:])
  for expedition in json.loads(json_str):
    day_str = expedition[0][0:10]
    graticule = expedition[0][11:]
    participants = expedition[3]
    success = expedition[4]
    if success:
      expeditions.setdefault(day_str, {})[graticule] = participants

print("Loaded", len(expeditions), "expeditions", file=sys.stderr)

start_date = date.today()#: date(2010, 5, 17)
step = timedelta(days=-1)
while start_date >= date(2008, 5, 1):
  # Start a new streak
  start_date_str = start_date.isoformat()
  expeditions_day = expeditions.get(start_date_str, {})
  if expeditions_day:
    # {
    #  frozenset(participants): [(expedition, participant), ...],
    #  ...
    # }
    #streak = {frozenset([p]): [(e, p)] for e, ps in expeditions_day.items() for p in ps}
    streak = {frozenset([p]) for e, ps in expeditions_day.items() for p in ps}

    # Extend it as far as possible
    day = start_date
    while streak:
      day_str = day.isoformat()
      expeditions_day = expeditions.get(day_str, {})
      #print(day_str, ":", sum(len(ps) for ps in expeditions_day.values()), "participants", file=sys.stderr)

      # Try extending current streak
      extended_streak = set()
      for ps in streak:
        for new_e, new_ps in expeditions_day.items():
          for new_p in new_ps:
            if new_p not in ps:
              # We can grow the group!
              extended_ps = frozenset({*ps, new_p})
              extended_streak.add(extended_ps)
      if len(extended_streak) > 100000:
        print("warning:", len(extended_streak), "possible groups from", start_date, "to", day_str)
      else:
        # Current streak was maximal, report one group
        example_group = next(iter(streak))
        if len(example_group) >= 7:
          print(start_date, len(example_group), len(streak), example_group)

      # If empty, loop ends
      streak = extended_streak

      # Advance
      day += step

  start_date += step
