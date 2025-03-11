from datetime import date, timedelta

# Incomplete streaks currently under consideration. Each is
# (start_date, {
#  frozenset(participants): [expeditions],
#  ...
# })
# Later we can add an optional graticule to the tuple.
streaks = []

# Assume expedition data ends up as a list of
# {date: {graticule: [participants]}}
expeditions = {
    "2025-01-01": {"52 13": ["C"]},
    "2025-01-02": {"52 13": ["A", "B"]},
    "2025-01-03": {"52 13": ["A", "B"]},
    "2025-01-04": {"52 13": ["C"]},
    "2025-01-05": {"52 13": ["D", "E"]},
    "2025-01-06": {"52 13": ["D", "E"]},
    "2025-01-07": {"52 13": ["C"]},
}

day = date(2025, 1, 1)
while day <= date(2025, 1, 8):
  day_str = day.isoformat()
  expeditions_day = expeditions.get(day_str, {})

  # Try extending current streaks
  extended_streaks = []
  for (start_date, groups) in streaks:
    extended_groups = {}
    for ps, es in groups.items():
      for new_e, new_ps in expeditions_day.items():
        for new_p in new_ps:
          if new_p not in ps:
            # We can grow the group!
            extended_ps = ps.union(new_p)
            if extended_ps not in extended_groups:
              # If we found a different way to build the same group, ignore this
              extended_groups[extended_ps] = [*es, (new_e, new_p)]
    if extended_groups:
      extended_streaks.append((start_date, extended_groups))
    else:
      # Current streaks were maximal, report one
      example_group = next(iter(groups.values()))
      print(start_date, len(groups), len(example_group), example_group)

  streaks = extended_streaks

  # Start a new streak
  if expeditions_day:
    streaks.append((day_str, {frozenset(p): [(e, p)] for e, ps in expeditions_day.items() for p in ps}))

  # Advance
  day += timedelta(days=1)

