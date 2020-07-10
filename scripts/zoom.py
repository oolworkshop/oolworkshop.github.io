"""Zoom API utilities for creating poster sessions.

******************************************************
* Important: The Zoom API limits you to creating max *
* 100 meetings per day.                              *
******************************************************


Assumptions this script makes:
- You have <=30 users.
- Your users have emails that fit a format like
  "my.zoom.email+{}@gmail.com", where "{}" is an
  integer going from 0 to you max user count.
- Information about your posters is in a yaml file called
  `_data/sessions.yml`, with the same format as:
  https://github.com/oolworkshop/oolworkshop.github.io/blob/master/_data/sessions.yml


Instructions:
- Sign up for a Pro Zoom account with the number of
  hosts that you need.
- Add users for the number of hosts you need. You should
  use emails for these users that share a common format,
  e.g. "my.zoom.email+0@gmail.com", "my.zoom.email+1@gmail.com".
  Anything after the "+" is actually ignored by gmail so
  all of these emails will go to the same base email
  ("my.zoom.email@gmail.com").
- In the Zoom web interface, go to Admin -> Account
  Management -> Account Settings to set global settings
  for all your users. Use the lock icon to ensure all
  user accounts always use the same setting.
- Setup a Zoom JWT app here:
  https://marketplace.zoom.us/docs/guides/getting-started/app-types/create-jwt-app
- Create a file called `secret.py` adjacent to this one
  and make sure it has variables:
    TOKEN: the JWT token (see site above)
    PASSWORD: the password for your meetings
    USER_EMAIL_TEMPLATE: a python format string for
      the host email accounts, e.g. "my.zoom.email+{}@gmail.com"
- Put session data in `_data/sessions.yml`, see e.g.
  https://github.com/oolworkshop/oolworkshop.github.io/blob/master/_data/sessions.yml
- Edit `create_poster_sessions` as needed to fit your
  particular workshop format.
- Call `create_poster_sessions()`.


"""

import requests
import json
import logging
import os
import jsondiff
import time
import yaml
import re
import random
import hashlib
from textwrap import dedent

from secret import TOKEN, USER_EMAIL_TEMPLATE, PASSWORD
from utils import meeting_json_exists, save_meeting_json, read_meeting_json


def _get(endpoint, params=None):
	"""Performs a GET request to the Zoom API."""
	headers = {
	    'authorization': "Bearer {}".format(TOKEN),
	    'content-type': "application/json"
	}

	response = requests.get(
		"https://api.zoom.us/v2" + endpoint,
		headers=headers,
		params=params)

	print("GET {} {}".format(response.url, response.status_code))

	try:
		response.raise_for_status()
	except requests.exceptions.HTTPError:
		print(response.json())
		raise

	return response.json()


def _patch(endpoint, json, params=None):
	"""Performs a PATCH request to the Zoom API."""
	headers = {
	    'authorization': "Bearer {}".format(TOKEN),
	    'content-type': "application/json"
	}

	response = requests.patch(
		"https://api.zoom.us/v2" + endpoint,
		headers=headers,
		json=json,
		params=params)

	print("PATCH {} {}".format(response.url, response.status_code))

	try:
		response.raise_for_status()
	except requests.exceptions.HTTPError:
		print(response.json())
		raise


def _post(endpoint, json, params=None):
	"""Performs a POST request to the Zoom API."""
	headers = {
	    'authorization': "Bearer {}".format(TOKEN),
	    'content-type': "application/json"
	}

	response = requests.post(
		"https://api.zoom.us/v2" + endpoint,
		headers=headers,
		json=json,
		params=params)

	print("POST {} {}".format(response.url, response.status_code))

	try:
		response.raise_for_status()
	except requests.exceptions.HTTPError:
		print(response.json())
		raise

	return response.json()


def get_users():
	if meeting_json_exists("users"):
		return read_meeting_json("users")

	else:
		params = {
			"status": "active",
			"page_size": 30,
			"page_number": 1
		}
		users = _get("/users", params)["users"]
		save_meeting_json("users", users)
		return users


def find_user(user_email):
	users = get_users()
	for user in users:
		if user["email"] == user_email:
			return user
	raise ValueError("no such user: {}".format(user_email))


def create_or_update_meeting(
	unique_id, user_email, topic, start_time, password,
	duration, waiting_room):

	if len(password) > 10:
		raise ValueError("password length must be <10")

	if meeting_json_exists(unique_id):
		meeting_id = read_meeting_json(unique_id)['id']
		settings = {
			"topic": topic,
			"start_time": start_time,
			"password": password,
			"duration": duration,
			"settings": {
				"join_before_host": not waiting_room,
				"waiting_room": waiting_room
			}
		}
		_patch("/meetings/{}".format(meeting_id), json=settings)
		meeting = _get("/meetings/{}".format(meeting_id))

	else:
		settings = {
			"topic": topic,
			"type": 2,  # scheduled meeting
			"start_time": start_time,
			"duration": duration,
			"password": password,
			"settings": {
				"host_video": True,
				"participant_video": False,
				"join_before_host": not waiting_room,
				"mute_upon_entry": True,
				"watermark": False,
				"use_pmi": False,
				"approval_type": 2,
				"audio": "both",
				"auto_recording": "none",
				"waiting_room": waiting_room,
				"meeting_authentication": True,
			}
		}

		user = find_user(user_email)
		url = "/users/{}/meetings".format(user["id"])
		meeting = _post(url, json=settings)

	save_meeting_json(unique_id, meeting)
	return meeting


def create_poster_sessions():
	# These are in GMT.
	session_times = {
		1: "2020-07-17T15:30:00Z",
		2: "2020-07-17T23:00:00Z",
	}

	# TODO: update this to use `load_presentation_data` rather
	# than the session yaml.
	with open("_data/sessions.yml", "r") as fh:
		sessions = yaml.load(fh)

	i = 1
	for session in sessions:
		for paper in session["papers"]:
			meeting = create_or_update_meeting(
				unique_id="OOL_{}".format(paper["id"]),
				user_email=USER_EMAIL_TEMPLATE.format(i),
				topic=paper["title"],
				start_time=session_times[paper["session"]],
				password=PASSWORD,
				duration=60,  # minutes
				waiting_room=True)
			time.sleep(1)  # to prevent ratelimiting
			i += 1


if __name__ == "__main__":
	create_poster_sessions()
