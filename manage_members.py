#!/usr/bin/env python3
""" Add or remove new or leaving users to/from chat """

import os
import argparse
import yaml
from dotmap import DotMap
from skpy import Skype, SkypeAuthException

def make_args():
    """ Build cli args """
    parser = argparse.ArgumentParser(description="Manage Skype channels")
    parser.add_argument('action', choices=['add', 'remove'])
    parser.add_argument('user_id', help="User ID: either skype nickname, live account or e-mail")
    parser.add_argument('--admin', help="Add as admin user or force remove of admin user",
                        action='store_true')
    return parser.parse_args()

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


def add_user_to_channels(user_id, skype_client, channels,
                         verify_channels=False,
                         add_as_admin=False):
    """ Add user to list of channels """

    for chat_id, topic in channels.items():
        chat = skype_client.chats.chat(chat_id)
        # Right now skpy returns truncated topics for channels
        # So skip verification by default
        if verify_channels and topic != chat.topic:
            print("Topic differ for channel {}: got '{}', but expected '{}'".format(
                chat_id, chat.topic, topic))
            continue
        chat.addMember(user_id, admin=add_as_admin)
        if add_as_admin:
            chat.sendMsg(u"Приветствуем нового админа {} в этом чате!".format(user_id))
        else:
            chat.sendMsg(u"Приветствуем нового пользователя {} в этом чате!".format(user_id))


def remove_user_from_channels(user_id, skype_client, channels,
                              verify_channels=False,
                              remove_admin=False):
    """ Remove user from channels """

    for chat_id, topic in channels.items():
        chat = skype_client.chats.chat(chat_id)
        if verify_channels and topic != chat.topic:
            print("Topic differ for channel {}: got '{}', but expected '{}'".format(
                chat_id, chat.topic, topic))
            continue
        if not remove_admin:
            user_is_admin = False
            for user in chat.admins:
                if user.id == user_id:
                    user_is_admin = True
                    break
            if user_is_admin:
                print("User has admin role on channel '{}' ({})".format(chat_id, chat.topic))
                continue
        chat.sendMsg(u"Прощаемся с {} в этом чате!".format(user_id))
        chat.removeMember(user_id)


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
    args = make_args()

    sk = skype_auth() #pylint: disable=invalid-name
    channels = read_channels()

    if args.action == "add":
        add_user_to_channels(args.user_id, sk, channels, add_as_admin=args.admin)
    elif args.action == "remove":
        remove_user_from_channels(args.user_id, sk, channels, remove_admin=args.admin)
    else:
        print("Not implemented yet")

if __name__ == "__main__":
    main()
