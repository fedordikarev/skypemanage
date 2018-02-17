#!/usr/bin/env python3
""" Add or remove new or leaving users to/from chat """

import os
import yaml
from dotmap import DotMap
from skpy import Skype, SkypeAuthException

def read_credentials(path=None):
    """ Read Skype credentials """
    if not path:
        path = os.path.expanduser("~/.skype_credentials.yaml")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return data


def read_channels(path=None):
    """ Read channels list """
    if not path:
        path = os.path.expanduser("~/.skype_channels.yaml")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    return data


def action_on_channel(group_chat, user_id, action="add"):
    """ Add or remove user to/from channel """
    #TODO: check user not admin before remove it
    #TODO: add option to override this check

    if action == "add":
        group_chat.addMember(user_id)
    elif action == "remove":
        group_chat.removeMember(user_id)
    else:
        raise NotImplementedError("Unknown action " + action)


def skype_auth():
    """ Use authorization token or make new one """
    sk = Skype(connect=False)   #pylint: disable=invalid-name
    sk.conn.setTokenFile(".tokens-app")
    try:
        sk.conn.readToken()
    except SkypeAuthException:
        creds = DotMap(read_credentials())
        sk.conn.setUserPwd(creds.username, creds.password)
        sk.conn.getSkypeToken()

    return sk

def main():
    """ Main function """
    sk = skype_auth() #pylint: disable=invalid-name

    recent = sk.chats.recent()
    count = 1
    while recent and count < 3:
        for chat_id in recent:
            chat = sk.chats.chat(chat_id)
            try:
                display_name = chat.topic
            except AttributeError:
                display_name = " ".join([str(chat.user.name.first), str(chat.user.name.last)])
            print(chat_id, display_name)
        recent = sk.chats.recent()
        count += 1


if __name__ == "__main__":
    main()
