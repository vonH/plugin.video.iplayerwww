
import os
import json

import xbmc

from resources.lib.ipwww_common import (
    translation,
    DIR_USERDATA,
    AddMenuEntry,
    icondir)


class SearchHistory:
    """
    A class providing an easy interface to saved search terms.

    :param content_type: The media type of the search terms, either `video`, for iplayer
        keywords, or `audio` for sounds.
    """

    def __init__(self, content_type: str):
        self.full_path = os.path.join(DIR_USERDATA, 'search_terms.json')
        if content_type not in ('video', 'audio'):
            raise ValueError(f"Invalid content_type '{content_type}' for SearchHistory. "
                             "Only 'video' and 'audio' are allowed.")
        self.content_type = content_type
        file_content = self._read_file()
        self._keywords_list = file_content.setdefault(content_type, [])

    def _read_file(self):
        try:
            with open(self.full_path, 'r', encoding='utf8') as f:
                data = json.load(f)
                return data
        except (OSError, KeyError, TypeError):
            return {}

    def _save_file(self):
        # dumps first, so as not to overwrite existing data on json errors.
        _file_content = self._read_file()
        _file_content[self.content_type] = self._keywords_list
        new_data = json.dumps(_file_content)
        with open(self.full_path, 'w', encoding='utf8') as f:
            f.write(new_data)

    def append(self, keyword: str):
        """Add `term` to the saved search terms for the specified media type.

        :param keyword: The search term to save.

        """
        xbmc.log(f"[ipwww_search] Adding new search term '{keyword}' to {self.content_type} list")
        if not keyword or keyword in self._keywords_list:
            return
        self._keywords_list.insert(0, keyword)
        self._save_file()

    def remove(self, keyword: str):
        """Remove `term` from the saved search terms for the specified media type.
        Fails silently when `term` does not exist in the search history.

        :param keyword: The search term to remove.

        """
        xbmc.log(f"[ipwww_search] Removing search term '{keyword}' from the {self.content_type} list")
        if keyword not in self._keywords_list:
            return
        self._keywords_list.remove(keyword)
        self._save_file()

    def clear(self):
        """Remove al search terms."""
        xbmc.log(f"[ipwww_search] Clear search history of {self.content_type}.")
        self._keywords_list.clear()
        self._save_file()

    def replace(self, existing: str, new: str):
        """Replace an existing keyword with a new one.

        :param existing: The existing keyword to replace.
        :param new: The new keyword that will replace the existing.
        :raises: ValueError if `existing` is not present in the search history
        """
        xbmc.log(f"[ipwww_search] Replacing search term '{existing}' for {new} in the {self.content_type} list")
        idx = self._keywords_list.index(existing)
        self._keywords_list[idx] = new
        self._save_file()

    def __bool__(self):
        return bool(self._keywords_list)

    def __iter__(self):
        return iter(self._keywords_list)


def open_keyboard(content_type):
    heading = ' - '.join((translation(30304), 'iPlayer' if content_type == 'video' else 'Sounds'))
    keyboard = xbmc.Keyboard('', heading)
    keyboard.doModal()
    if keyboard.isConfirmed():
        return keyboard.getText()
    else:
        return ''


def list_search_terms(content_type: str, mode: int):
    """Create a listing of saved search terms, starting with an item that enables users
    to enter a new search term using the on-screen keyboard.

    :param content_type: The media type of the search terms, either `video`, for iplayer
        searches, or `audio` for sounds.
    :param mode: The mode to define the callback that is to perform the actual search.
    """
    icon = icondir + 'search.png'
    search_history = SearchHistory(content_type)
    txt_remove = translation(30601)
    txt_edit = translation(30604)
    txt_clear = translation(30605)

    AddMenuEntry('New Search', url=content_type, mode=190, iconimage=icon)
    for keyword in search_history:
        ctx_mnu = [(txt_remove,
                    'RunPlugin(plugin://plugin.video.iplayerwww?'
                    f'mode=304&content_type={content_type}&url=remove&keyword={keyword})'),
                   (txt_edit,
                    'RunPlugin(plugin://plugin.video.iplayerwww?'
                    f'mode=304&content_type={content_type}&url=edit&keyword={keyword})'),
                   (txt_clear,
                    'RunPlugin(plugin://plugin.video.iplayerwww?'
                    f'mode=304&content_type={content_type}&url=clear)')
                   ]
        AddMenuEntry(keyword, keyword, mode, icon, context_mnu=ctx_mnu)


def new_search(content_type, mode):
    keyword = open_keyboard(content_type)
    if keyword:
        SearchHistory(content_type).append(keyword)
        xbmc.executebuiltin(f'Container.Update(plugin://plugin.video.iplayerwww?mode={mode}&url={keyword})')


def context_menu(content_type: str, action: str, keyword: str = None):
    """Handle all search related context menu items."""
    search_history = SearchHistory(content_type)

    if action == 'remove':
        search_history.remove(keyword)
    elif action == 'clear':
        search_history.clear()
    elif action == 'edit':
        heading = ' - '.join((translation(30604), keyword))
        keyboard = xbmc.Keyboard(keyword, heading)
        keyboard.doModal()
        if not keyboard.isConfirmed():
            return

        new_term = keyboard.getText()
        if new_term == '':
            search_history.remove(keyword)
        else:
            search_history.replace(keyword, new_term)
    else:
        xbmc.log(f"[ipwww_search] Invalid context menu action '{action}'.")
    xbmc.executebuiltin('Container.Refresh')
