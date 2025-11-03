import logging
import platform
import re
import subprocess

# taken from https://stackoverflow.com/a/2091530/373655
class ChromeWindowMgr:
    """Encapsulates some calls to the winapi for window management"""

    def __init__(self):
        """Constructor"""
        self._handle = None
        self.platform = platform.system()
        self.win32gui = None
        self.guiInterfaceExists = False

        if self.platform == 'Windows':
            self.win32gui = self._import_if_exists('win32gui')
            self.guiInterfaceExists = self.win32gui is not None

            if self.guiInterfaceExists:
                self._find_window()

    def _window_enum_callback(self, hwnd, chromeWindowHandles):
        """Pass to win32gui.EnumWindows() to check all the opened windows"""
        if re.match('.* Google Chrome', str(self.win32gui.GetWindowText(hwnd))) is not None:
            chromeWindowHandles.append(hwnd)

    def _find_window(self):
        """find a window whose title matches the wildcard regex"""
        self._handle = None
        chromeWindowHandles = []
        self.win32gui.EnumWindows(self._window_enum_callback, chromeWindowHandles)

        if len(chromeWindowHandles) == 0:
            raise Exception('No chrome windows open')
        elif len(chromeWindowHandles) == 1:
            self._handle = chromeWindowHandles[0]
        else:
            matchingWindows = [handle for handle in chromeWindowHandles if re.match('github.com.*', self.win32gui.GetWindowText(handle))]
            if len(matchingWindows) != 1:
                raise Exception('Multiple Chrome windows open. Go to https://github.com/robianmcd/chrome-dino-ai in the window you want to use.')
            else:
                self._handle = matchingWindows[0]

    def set_foreground(self):
        """put the window in the foreground"""
        if self.guiInterfaceExists:
            try:
                self._find_window()
            except Exception:
                logging.exception('Failed to locate Chrome window on Windows.')
                raise

            try:
                self.win32gui.SetForegroundWindow(self._handle)
            except Exception:
                logging.exception('Failed to set Chrome window to foreground on Windows.')
        elif self.platform == 'Darwin':
            self._set_foreground_mac()
        else:
            logging.info('Chrome foreground activation is not implemented for %s.', self.platform)

    def _import_if_exists(self, module_name):
        try:
            module = __import__(module_name)
        except ImportError:
            return None
        else:
            return module

    def _set_foreground_mac(self):
        try:
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    'tell application "Google Chrome" to activate'
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except FileNotFoundError:
            logging.warning(
                'osascript not found. Unable to bring Chrome to the foreground on macOS.'
            )
        except subprocess.CalledProcessError:
            logging.exception('osascript failed to activate Google Chrome on macOS.')
