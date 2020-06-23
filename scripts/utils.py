import pandas as pd
import os
import json


def format_authors(x):
  authors = x.split(";")
  for i in range(len(authors)):
    author = authors[i]
    author = author.strip()
    last, first = author.split(",")
    first = first.strip()
    last = last.strip()
    author = "{} {}".format(first, last)
    authors[i] = author

  if len(authors) == 1:
    x = authors[0]
  elif len(authors) == 2:
    x = "{} and {}".format(*authors)
  else:
    first = ", ".join(authors[:-1])
    last = authors[-1]
    x = "{}, and {}".format(first, last)
  
  return x


def load_presentation_data():
    data = pd.read_csv("scripts/data/presentations.csv")
    data["session_title"] = data["session"].replace({
        "invited": "Invited Talk",
        "opening": "Opening Remarks",
        "2-3 pm GMT": "Session 1 (2-3pm GMT)",
        "9-10 pm GMT": "Session 2 (9-10pm GMT)",
    })
    data["session_id"] = data["session"].replace({
        "invited": 0,
        "opening": 0,
        "2-3 pm GMT": 1,
        "9-10 pm GMT": 2,
    })
    data = data.drop(columns=["session"])
    data["authors"] = data["authors"].apply(format_authors)
    return data


def load_meet_and_greet_data():
    def _get_names(meeting):
        cols = sorted([x for x in meeting.index if x.startswith("name_")])
        names = [meeting[x] for x in cols]
        names = [x for x in names if x]
        if len(names) == 2:
            names = "{} and {}".format(*names)
        else:
            names = ", ".join(names[:-1]) + ", and " + names[-1]
        return names

    def _get_emails(meeting):
        cols = sorted([x for x in meeting.index if x.startswith("email_")])
        emails = [meeting[x] for x in cols]
        emails = [x for x in emails if x]
        return ", ".join(emails)

    data = pd.read_csv("scripts/data/meet_and_greet.csv")
    data.index.name = "unique_id"
    data = data.reset_index()
    data = data.fillna("")
    data["names"] = ""
    data["emails"] = ""
    data = data.rename(columns={"timeslot": "session"})
    data["session_title"] = data["session"].replace({
        "1:00-1:30 PM": "1:00-1:30pm GMT",
        "8:00-8:30 PM": "8:00-8:30pm GMT"
    })
    data["session"] = data["session"].replace({
        "1:00-1:30 PM": 1,
        "8:00-8:30 PM": 2
    })

    detail_keys = ["institution", "academic_status", "google_scholar", "website"]
    for key in detail_keys:
        for j in [1, 2, 3, 4]:
            data["{}_{}".format(key, j)] = ""

    all_details = pd.read_csv("scripts/data/meet_and_greet_details.csv")
    all_details = all_details.set_index("email")
    all_details = all_details.fillna("")

    for i, row in data.iterrows():
        data.loc[i, "names"] = _get_names(row)
        data.loc[i, "emails"] = _get_emails(row)
        for j in [1, 2, 3, 4]:
            email = row["email_{}".format(j)]
            if not email:
                continue
            details = all_details.loc[email]
            for key in detail_keys:
                data.loc[i, "{}_{}".format(key, j)] = details[key]

    return data



def meeting_json_exists(name):
    path = os.path.join("scripts/data/meetings", "{}.json".format(name))
    return os.path.exists(path)


def save_meeting_json(name, data):
    path = os.path.join("scripts/data/meetings", "{}.json".format(name))
    if not os.path.exists("scripts/data/meetings"):
        os.makedirs("scripts/data/meetings")
    with open(path, "w") as fh:
        json.dump(data, fh)


def read_meeting_json(name):
    path = os.path.join("scripts/data/meetings", "{}.json".format(name))
    with open(path, "r") as fh:
        return json.load(fh)

