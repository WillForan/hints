from __future__ import annotations

import logging
from argparse import ArgumentParser
from itertools import product
from math import ceil, log
from time import sleep, time
from typing import TYPE_CHECKING, Any

from gi import require_version
from pynput.mouse import Button, Controller

from hints.backends.atspi import AtspiBackend
from hints.backends.exceptions import AccessibleChildrenNotFoundError
from hints.backends.opencv import OpenCV
from hints.constants import MOUSE_GRAB_PAUSE
from hints.huds.interceptor import InterceptorWindow
from hints.huds.overlay import OverlayWindow
from hints.utils import HintsConfig, load_config

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .child import Child

try:
    require_version("GtkLayerShell", "0.1")
    from gi.repository import GtkLayerShell

    IS_WAYLAND = True
except ValueError:
    IS_WAYLAND = False

require_version("Gtk", "3.0")
from gi.repository import Gtk


def get_hints(children: set, alphabet: str | set[str]) -> dict[str, Child]:
    """Get hints.

    :param children: The children elements of windown that indicate the
        absolute position of those elements.
    :param alphabet: The alphabet used to create hints
    :return: The hints. Ex {"ab": Child, "ac": Child}
    """
    hints: dict[str, Child] = {}

    if len(children) == 0:
        return hints

    for child, hint in zip(
        children,
        product(alphabet, repeat=ceil(log(len(children)) / log(len(alphabet)))),
    ):
        hints["".join(hint)] = child

    return hints


def hint_mode(config: HintsConfig, mouse: Controller):
    """Hint mode to interact with hints on screen.

    :param config: Hints config.
    :param mouse: Mouse device.
    """
    window_extents = None
    hints = {}

    backends_map = {"atspi": AtspiBackend, "opencv": OpenCV}
    backends = config["backends"]["enable"]

    for backend in backends:

        start = time()
        current_backend = backends_map[backend](config)
        logger.debug(
            "Attempting to get accessible children using the '%s' backend.",
            backend,
        )
        try:
            children = current_backend.get_children()

            logger.debug("Gathering hints took %f seconds", time() - start)
            logger.debug("Gathered %d hints", len(children))

            hints = get_hints(
                children,
                alphabet={
                    character
                    for character in config["alphabet"]
                    if not character.isdigit()
                },
            )

            window_extents = current_backend.get_window_extents()

        except AccessibleChildrenNotFoundError:
            logger.debug(
                "No acceessible children found with the '%s' backend.",
                backend,
            )

        if window_extents and hints:
            mouse_action: dict[str, Any] = {}
            x, y, width, height = window_extents
            app = OverlayWindow(
                x,
                y,
                width,
                height,
                config=config,
                hints=hints,
                mouse_action=mouse_action,
            )

            if IS_WAYLAND:
                GtkLayerShell.init_for_window(app)
                GtkLayerShell.auto_exclusive_zone_enable(app)
                GtkLayerShell.set_anchor(app, GtkLayerShell.Edge.TOP, True)
                GtkLayerShell.set_anchor(app, GtkLayerShell.Edge.LEFT, True)
                GtkLayerShell.set_layer(app, GtkLayerShell.Layer.OVERLAY)

            app.show_all()
            Gtk.main()

            if mouse_action:
                match mouse_action["action"]:
                    case "click":
                        mouse.position = (mouse_action["x"], mouse_action["y"])
                        mouse.click(
                            (
                                Button.left
                                if mouse_action["button"] == "left"
                                else Button.right
                            ),
                            mouse_action["repeat"],
                        )
                    case "hover":
                        mouse.position = (mouse_action["x"], mouse_action["y"])
                    case "grab":
                        mouse.position = (mouse_action["x"], mouse_action["y"])
                        # sleep required to allow time for mouse to move before pressing
                        # less than 0.2 seconds does not always work
                        sleep(MOUSE_GRAB_PAUSE)
                        mouse.press(Button.left)
                        interceptor = InterceptorWindow(
                            x, y, 1, 1, mouse, mouse_action, config
                        )
                        interceptor.show_all()
                        Gtk.main()

            # no need to use the next backend if the current one succeeded
            break


def main():
    """Hints entry point."""

    config = load_config()

    parser = ArgumentParser(
        prog="Hints",
        description="Hints lets you navigate GUI applications in Linux without"
        ' your mouse by displaying "hints" you can type on your keyboard to'
        " interact with GUI elements.",
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default="hint",
        choices=["hint", "scroll"],
        help="mode to use",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Set verbosity of output. Useful for debugging and seeing the"
        " output of accessible elements (roles, states, application name, ect)"
        " for setting up configuration.",
    )

    args = parser.parse_args()

    custom_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if args.verbose >= 1:
        logging.basicConfig(level=logging.DEBUG, format=custom_format)
    else:
        logging.basicConfig(level=logging.INFO, format=custom_format)

    mouse = Controller()

    match args.mode:
        case "hint":
            hint_mode(config, mouse)
        case "scroll":
            interceptor = InterceptorWindow(
                0, 0, 1, 1, mouse, {"action": "scroll"}, config
            )
            interceptor.show_all()
            Gtk.main()
