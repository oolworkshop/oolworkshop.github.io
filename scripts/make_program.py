import yaml
import os
import pandas as pd
import re

from utils import load_presentation_data, read_meeting_json, meeting_json_exists


INCLUDE_MEETING_URLS = True
TEMPLATE = """
---
layout: paper
id: {unique_id}
slides_live_id: {slides_live_id}
rocket_id: {rocket_id}
meeting_url: {meeting_url}
authors: "{authors}"
camera_ready: {camera_ready}
cmt_id: {cmt_id}
kind: {kind}
session_id: {session_id}
session_title: "{session_title}"
title: "{title}"
abstract: "{abstract}"
track: {track}
live: {live}
video_file_url: {video_file_url}
youtube_url: {youtube_url}
---
""".strip()


def make_jekyll_data():
    data = load_presentation_data()
    data = data.sort_values(by="authors")
    data = data.rename(columns={
        "session_id": "session",
        "unique_id": "id"
    })
    data = data.drop(columns=[
        "presenter_email",
        "presenter_name",
        "slides_live_id",
        "live",
    ])

    # Process sessions.
    sessions = []
    for session in [1, 2]:
        session_data = data.query("session == {}".format(session))
        session_title, = session_data["session_title"].unique()
        session_data = pd.concat([
            session_data.query("kind == 'oral'"),
            session_data.query("kind == 'spotlight'"),
            session_data.query("kind == 'poster'"),
        ])
        session_data = session_data.drop(columns=[
            "session_title",
            "video_file_url",
            "youtube_url",
        ])
        sessions.append({
            "id": session,
            "title": session_title,
            "papers": session_data.to_dict(orient="records")
        })
    with open("_data/sessions.yml", "w") as fh:
        yaml.dump(sessions, fh)

    # Process speakers.
    speakers = data.query("session == 0")
    speakers = speakers.sort_values(by="id")
    speakers = speakers.drop(columns=[
        "cmt_id",
        "camera_ready",
        "session",
        "session_title",
        "track",
        "video_file_url",
        "youtube_url",
    ])
    speakers = speakers.to_dict(orient="records")
    with open("_data/speakers.yml", "w") as fh:
        yaml.dump(speakers, fh)


def make_program():
    # Delete existing files.
    files = os.listdir("program")
    for file in files:
        os.remove(os.path.join("program", file))

    all_data = load_presentation_data().to_dict(orient="records")
    for data in all_data:
        print(data["unique_id"])

        if INCLUDE_MEETING_URLS:
            meeting_id = "OOL_{}".format(data["unique_id"])
            if meeting_json_exists(meeting_id):
                meeting = read_meeting_json(meeting_id)
                data["meeting_url"] = meeting["join_url"]
            else:
                print("No meeting '{}'".format(meeting_id))
                data["meeting_url"] = ""
        else:
            data["meeting_url"] = ""

        data["camera_ready"] = str(data["camera_ready"]).lower()
        data["title"] = data["title"].replace("\"", "\\\"")
        data["abstract"] = data["abstract"]
        data["live"] = str(data["live"]).lower()

        data["rocket_id"] = "ool-paper-{:d}".format(data["unique_id"])
        if data["kind"] == "opening":
            data["rocket_id"] = "object-oriented-learning-perception-representation-and-reasoning-11"

        html = TEMPLATE.format(**data)
        path = "program/ool_{}.html".format(data["unique_id"])
        assert not os.path.exists(path)
        with open(path, "w") as fh:
            fh.write(html)


def add_zoom_links():
    all_data = load_presentation_data().to_dict(orient="records")
    for data in all_data:
        print(data["unique_id"])

        if INCLUDE_MEETING_URLS:
            meeting_id = "OOL_{}".format(data["unique_id"])
            if meeting_json_exists(meeting_id):
                meeting = read_meeting_json(meeting_id)
                data["meeting_url"] = meeting["join_url"]
            else:
                print("No meeting '{}'".format(meeting_id))
                data["meeting_url"] = ""
        else:
            data["meeting_url"] = ""

        path = "program/ool_{}.html".format(data["unique_id"])
        with open(path, "r") as fh:
            html = fh.read()

        pattern = r"meeting_url: .*"
        repl = r"meeting_url: {}".format(data["meeting_url"])
        html = re.sub(pattern, repl, html)

        with open(path, "w") as fh:
            fh.write(html)


if __name__ == "__main__":
    # make_jekyll_data()
    # make_program()
    add_zoom_links()
