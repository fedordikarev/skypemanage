#!/usr/bin/env python3
""" Add or remove new or leaving users to/from chat """

import os
import argparse
import yaml
from skpy import Skype, SkypeAuthException

def make_args():
    """ Build cli args """
    parser = argparse.ArgumentParser(description="Manage Skype channels")
    parser.add_argument('action', choices=['add', 'remove', 'list'])
    parser.add_argument('user_id', help="User ID: either skype nickname, live account or e-mail")
    parser.add_argument('--admin', help="Add as admin user or force remove of admin user",
                        action='store_true')
    parser.add_argument('--message', type=str, help="Show this message in chat")
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
                         add_as_admin=False,
                         welcome_message=None):
    """ Add user to list of channels """
    if not welcome_message:
        welcome_message = u"Приветствуем нового {} {} в этом чате".format(
            "админа" if add_as_admin else "пользователя", user_id)
    for chat_id, topic in channels.items():
        chat = skype_client.chats.chat(chat_id)
        # Right now skpy returns truncated topics for channels
        # So skip verification by default
        if verify_channels and topic != chat.topic:
            print("Topic differ for channel {}: got '{}', but expected '{}'".format(
                chat_id, chat.topic, topic))
            continue
        chat.addMember(user_id, admin=add_as_admin)
        chat.sendMsg(welcome_message)


def remove_user_from_channels(user_id, skype_client, channels,
                              verify_channels=False,
                              remove_admin=False,
                              bye_message=None):
    """ Remove user from channels """
    if not bye_message:
        bye_message = "Прощаемся с {} в этом чате!".format(user_id)

    skipped_count = 0

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
                print("Skip: user has admin role on channel '{}' ({})".format(chat.topic, chat_id))
                skipped_count += 1
                continue
        chat.sendMsg(bye_message)
        chat.removeMember(user_id)

    if skipped_count > 0:
        print("Use --admin flag to remove user from skipped chats")

def list_recent(skype_client, max_count=1):
    """ List recent chats """
    recent = skype_client.chats.recent()
    count = 0
    while(recent and count < max_count):
        for chat_id in recent:
            chat = skype_client.chats.chat(chat_id)
            try:
                display_name = chat.topic
            except AttributeError:
                display_name = " ".join([str(chat.user.name.first), str(chat.user.name.last)])
            print(chat_id, display_name)
        recent = skype_client.chats.recent()
        count += 1


def skype_auth():
    """ Use authorization token or make new one """
    sk = Skype(connect=False)   #pylint: disable=invalid-name
    sk.conn.setTokenFile(".tokens-app")
    try:
        sk.conn.readToken()
    except (SkypeAuthException, FileNotFoundError):
        creds = read_credentials()
        sk.conn.setUserPwd(creds['username'], creds['password'])
        sk.conn.getSkypeToken()

    return sk

def main():
    """ Main function """
    args = make_args()

    sk = skype_auth() #pylint: disable=invalid-name
    channels = read_channels()

    if args.action == "add":
        add_user_to_channels(args.user_id, sk, channels,
                             add_as_admin=args.admin, welcome_message=args.message)
    elif args.action == "remove":
        remove_user_from_channels(args.user_id, sk, channels,
                                  remove_admin=args.admin, bye_message=args.message)
    elif args.action == "list":
        list_recent(sk, int(args.user_id)) # user_id actually is count for "list" action
    else:
        print("Not implemented yet")

if __name__ == "__main__":
    main()
