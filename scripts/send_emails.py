import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pandas as pd

from secret import SENDER_EMAIL, SENDER_PASSWORD
from utils import read_meeting_json, meeting_json_exists
from utils import load_presentation_data, load_meet_and_greet_data


PORT = 465  # For SSL
SMTP_SERVER = "smtp.gmail.com"


def get_zoom_users():
    account_info = pd.read_csv("scripts/data/zoom_accounts.csv")
    users = pd.DataFrame(read_meeting_json("users"))
    users = pd.merge(users, account_info, on="email", how="inner")
    users = users.rename(columns={
        "id": "host_id",
        "email": "host_email",
        "password": "host_password"
    })
    users = users[["host_id", "host_email", "host_password", "host_key"]]
    return users


def get_zoom_meetings(ids, prefix):
    meetings = []
    for unique_id in ids:
        if meeting_json_exists("{}_{}".format(prefix, unique_id)):
            meeting_info = read_meeting_json("{}_{}".format(prefix, unique_id))
            meeting_info["unique_id"] = unique_id
            meetings.append(meeting_info)
    meetings = pd.DataFrame(meetings)
    meetings = meetings[["host_id", "start_url", "join_url", "unique_id", "password"]]
    meetings = meetings.rename(columns={
        "password": "meeting_password"
    })
    return meetings


#### Presenter emails ####

def get_presenter_email_body(data):
    message = MIMEMultipart("alternative")
    message["Subject"] = "BAICS Presentation Instructions"
    message["From"] = SENDER_EMAIL
    message["To"] = data["presenter_email"]

    with open("scripts/templates/presenter.html", "r") as fh:
        body = fh.read()
    body = body.format(**data)

    message.attach(MIMEText(body, "html"))
    return message.as_string()


def send_presenter_emails():
    # Load meeting data.
    papers = load_presentation_data()
    meetings = get_zoom_meetings(papers["unique_id"].unique(), prefix="BAICS")
    users = get_zoom_users()
    meetings = pd.merge(meetings, users, on="host_id")
    meetings = pd.merge(meetings, papers, on="unique_id")
    meetings = meetings.to_dict(orient="records")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for meeting in meetings:
            print("{} ({})".format(meeting["presenter_email"], meeting["title"]))
            message = get_presenter_email_body(meeting)
            server.sendmail(SENDER_EMAIL, meeting["presenter_email"], message)


#### Meet-and-greet emails ####

def get_meet_and_greet_email_body(data):
    message = MIMEMultipart("alternative")
    message["Subject"] = "BAICS Meet-and-Greet Instructions"
    message["From"] = SENDER_EMAIL
    message["To"] = data["emails"]

    with open("scripts/templates/meet_and_greet.html", "r") as fh:
        body = fh.read()
    body = body.format(**data)

    message.attach(MIMEText(body, "html"))
    return message


def send_meet_and_greet_emails():
    # Load meeting data.
    data = load_meet_and_greet_data()
    meetings = get_zoom_meetings(
        data["unique_id"].unique(), prefix="meet_and_greet")
    users = get_zoom_users()
    meetings = pd.merge(meetings, users, on="host_id")
    meetings = pd.merge(meetings, data, on="unique_id")
    meetings = meetings.to_dict(orient="records")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for i, meeting in enumerate(meetings):
            print("{}: {}".format(i, meeting["emails"]))
            message = get_meet_and_greet_email_body(meeting)
            server.send_message(message)


if __name__ == "__main__":
    #send_presenter_emails()
    send_meet_and_greet_emails()
 