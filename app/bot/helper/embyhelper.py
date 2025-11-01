import random
import string
from typing import List, Optional

import requests


def _prepare_request_args(api_key: str, headers: Optional[dict] = None, params: Optional[dict] = None):
    merged_headers = {"X-Emby-Token": api_key}
    if headers:
        merged_headers.update(headers)

    merged_params = {"api_key": api_key}
    if params:
        merged_params.update(params)

    return merged_headers, merged_params


def add_user(emby_url: str, emby_api_key: str, username: str, password: str, emby_libs: List[str]):
    try:
        url = f"{emby_url}/Users/New"
        headers, params = _prepare_request_args(emby_api_key, headers={"Content-Type": "application/json"})
        payload = {
            "Name": username,
            "Password": password
        }
        response = requests.post(url, json=payload, headers=headers, params=params, timeout=10)

        if response.status_code not in (200, 204):
            print(f"Error creating new Emby user: {response.text}")
            return False

        user_id = response.json().get("Id")
        if not user_id:
            print("Error creating new Emby user: missing user id in response")
            return False

        enabled_folders = []
        server_libs = get_libraries(emby_url, emby_api_key)

        if emby_libs and emby_libs[0] != "all":
            for lib in emby_libs:
                found = False
                for server_lib in server_libs:
                    name = server_lib.get("Name")
                    item_id = server_lib.get("ItemId") or server_lib.get("Id")
                    if name == lib and item_id:
                        enabled_folders.append(item_id)
                        found = True
                        break
                if not found:
                    print(f"Couldn't find Emby Library: {lib}")

        policy_url = f"{emby_url}/Users/{user_id}/Policy"
        headers, params = _prepare_request_args(emby_api_key, headers={"Content-Type": "application/json"})
        policy_payload = {
            "IsAdministrator": False,
            "IsHidden": True,
            "IsDisabled": False,
            "BlockedTags": [],
            "EnableUserPreferenceAccess": True,
            "AccessSchedules": [],
            "BlockUnratedItems": [],
            "EnableRemoteControlOfOtherUsers": False,
            "EnableSharedDeviceControl": True,
            "EnableRemoteAccess": True,
            "EnableLiveTvManagement": True,
            "EnableLiveTvAccess": True,
            "EnableMediaPlayback": True,
            "EnableAudioPlaybackTranscoding": True,
            "EnableVideoPlaybackTranscoding": True,
            "EnablePlaybackRemuxing": True,
            "ForceRemoteSourceTranscoding": False,
            "EnableContentDeletion": False,
            "EnableContentDeletionFromFolders": [],
            "EnableContentDownloading": True,
            "EnableSyncTranscoding": True,
            "EnableMediaConversion": True,
            "EnabledDevices": [],
            "EnableAllDevices": True,
            "EnabledChannels": [],
            "EnableAllChannels": False,
            "EnabledFolders": enabled_folders,
            "EnableAllFolders": not enabled_folders,
            "InvalidLoginAttemptCount": 0,
            "LoginAttemptsBeforeLockout": -1,
            "MaxActiveSessions": 0,
            "EnablePublicSharing": True,
            "BlockedMediaFolders": [],
            "BlockedChannels": [],
            "RemoteClientBitrateLimit": 0,
            "AuthenticationProviderId": "Emby.Server.Implementations.Users.DefaultAuthenticationProvider",
            "PasswordResetProviderId": "Emby.Server.Implementations.Users.DefaultPasswordResetProvider",
            "SyncPlayAccess": "CreateAndJoinGroups"
        }

        response = requests.post(policy_url, json=policy_payload, headers=headers, params=params, timeout=10)
        if response.status_code in (200, 204):
            return True

        print(f"Error setting Emby user permissions: {response.text}")
        return False
    except Exception as e:
        print(e)
        return False


def get_libraries(emby_url: str, emby_api_key: str):
    url = f"{emby_url}/Library/VirtualFolders"
    headers, params = _prepare_request_args(emby_api_key)
    response = requests.get(url, headers=headers, params=params, timeout=10)

    data = response.json()
    if isinstance(data, dict) and "Items" in data:
        return data.get("Items", [])
    return data


def verify_username(emby_url: str, emby_api_key: str, username: str):
    users = get_users(emby_url, emby_api_key)
    for user in users:
        if user.get('Name', '').lower() == username.lower():
            return False
    return True


def remove_user(emby_url: str, emby_api_key: str, emby_username: str):
    try:
        users = get_users(emby_url, emby_api_key)
        user_id = None
        for user in users:
            if user.get('Name', '').lower() == emby_username.lower():
                user_id = user.get('Id')
                break

        if not user_id:
            print(f"Error removing user {emby_username} from Emby: Could not find user.")
            return False

        url = f"{emby_url}/Users/{user_id}"
        headers, params = _prepare_request_args(emby_api_key)
        response = requests.delete(url, headers=headers, params=params, timeout=10)
        if response.status_code in (200, 204):
            return True

        print(f"Error deleting Emby user: {response.text}")
        return False
    except Exception as e:
        print(e)
        return False


def get_users(emby_url: str, emby_api_key: str):
    url = f"{emby_url}/Users"
    headers, params = _prepare_request_args(emby_api_key)
    response = requests.get(url, headers=headers, params=params, timeout=10)
    return response.json()


def generate_password(length: int, lower: bool = True, upper: bool = True, numbers: bool = True, symbols: bool = True):
    character_list = []
    if not (lower or upper or numbers or symbols):
        raise ValueError("At least one character type must be provided")

    if lower:
        character_list += string.ascii_lowercase
    if upper:
        character_list += string.ascii_uppercase
    if numbers:
        character_list += string.digits
    if symbols:
        character_list += string.punctuation

    return "".join(random.choice(character_list) for _ in range(length))


def get_config(emby_url: str, emby_api_key: str):
    url = f"{emby_url}/System/Configuration"
    headers, params = _prepare_request_args(emby_api_key)
    response = requests.get(url, headers=headers, params=params, timeout=5)
    return response.json()


def get_status(emby_url: str, emby_api_key: str):
    url = f"{emby_url}/System/Configuration"
    headers, params = _prepare_request_args(emby_api_key)
    response = requests.get(url, headers=headers, params=params, timeout=5)
    return response.status_code
