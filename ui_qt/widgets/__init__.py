# widgets module

from .composer_widget import ComposerInputWidget, ComposerDiffWidget, ComposerHintWidget
from .context_menu_widget import SelectionContextMenu
from .diff_preview_manager import (
    DiffPreviewMode,
    DiffPreviewManager,
    get_diff_preview_mode_from_config,
)
from .inline_diff_manager import InlineDiffManager, DiffHoverToolbar
from .search_replace_widget import SearchReplaceWidget
from .overlay_manager import OverlayManager, OverlayWidget

__all__ = [
    "ComposerInputWidget",
    "ComposerDiffWidget",
    "ComposerHintWidget",
    "SelectionContextMenu",
    "DiffPreviewMode",
    "DiffPreviewManager",
    "get_diff_preview_mode_from_config",
    "InlineDiffManager",
    "DiffHoverToolbar",
    "SearchReplaceWidget",
    "OverlayManager",
    "OverlayWidget",
]
