"""
AI Sticker Generator - PyQt6 Desktop Application
Integrates all sticker generation functions into a beautiful local UI
"""

import os
import sys
import asyncio
import threading
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QTabWidget,
    QFrame, QFileDialog, QSpinBox, QMessageBox, QProgressBar,
    QGroupBox, QGridLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon, QPalette, QColor, QMovie

# Import controllers
from controllers.free_sticker import generate_sticker_free, create_animated_webp as free_create_animated
from controllers.free_animation import generate_animated_sticker as free_animated_sticker
from controllers.replicate_sticker import generate_sticker as replicate_generate, \
    create_animated_webp as replicate_create_animated
from controllers.replicate_animation import generate_animated_sticker as replicate_animated_sticker
from controllers.gemini_sticker import generate_sticker as gemini_generate, \
    create_animated_webp as gemini_create_animated
from controllers.gemini_animation import generate_animated_sticker as gemini_animated_sticker
from controllers.video_model_animation import generate_runware_transparent_sticker
from controllers.image_generation import generate_image
# ============== STYLE CONSTANTS ==============
DARK_BG = "#1a1a2e"
DARKER_BG = "#16213e"
CARD_BG = "#1f1f3d"
ACCENT_COLOR = "#7c3aed"
ACCENT_HOVER = "#8b5cf6"
TEXT_COLOR = "#ffffff"
TEXT_SECONDARY = "#a0a0a0"
BORDER_COLOR = "#2d2d5a"
SUCCESS_COLOR = "#22c55e"
WARNING_COLOR = "#f59e0b"

STYLESHEET = f"""
QMainWindow {{
    background-color: {DARK_BG};
}}

QWidget {{
    background-color: transparent;
    color: {TEXT_COLOR};
    font-family: 'Segoe UI', Arial, sans-serif;
}}

QTabWidget::pane {{
    border: none;
    background-color: {DARK_BG};
}}

QTabWidget::tab-bar {{
    alignment: center;
}}

QTabBar::tab {{
    background-color: {CARD_BG};
    color: {TEXT_SECONDARY};
    padding: 12px 24px;
    margin: 4px;
    border-radius: 20px;
    font-weight: bold;
    min-width: 100px;
}}

QTabBar::tab:selected {{
    background-color: {ACCENT_COLOR};
    color: {TEXT_COLOR};
}}

QTabBar::tab:hover:!selected {{
    background-color: {BORDER_COLOR};
}}

QGroupBox {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    margin-top: 12px;
    padding: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: {TEXT_COLOR};
}}

QLineEdit {{
    background-color: {DARKER_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 16px;
    color: {TEXT_COLOR};
    font-size: 14px;
    min-height: 20px;
}}

QLineEdit:focus {{
    border: 2px solid {ACCENT_COLOR};
}}

QComboBox {{
    background-color: {DARKER_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 12px;
    color: {TEXT_COLOR};
    font-size: 14px;
    min-width: 150px;
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 8px solid {TEXT_SECONDARY};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {DARKER_BG};
    border: 1px solid {BORDER_COLOR};
    selection-background-color: {ACCENT_COLOR};
    color: {TEXT_COLOR};
}}

QSpinBox {{
    background-color: {DARKER_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 8px;
    padding: 16px;
    color: {TEXT_COLOR};
    font-size: 14px;
    min-height: 20px;
}}

QPushButton {{
    background-color: {ACCENT_COLOR};
    color: {TEXT_COLOR};
    border: none;
    border-radius: 8px;
    padding: 14px 28px;
    font-weight: bold;
    font-size: 14px;
}}

QPushButton#secondaryBtn {{
    font-size: 12px;
    padding: 10px 16px;
}}


QPushButton:hover {{
    background-color: {ACCENT_HOVER};
}}

QPushButton:pressed {{
    background-color: {ACCENT_COLOR};
}}

QPushButton:disabled {{
    background-color: {BORDER_COLOR};
    color: {TEXT_SECONDARY};
}}

QPushButton#secondaryBtn {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
}}

QPushButton#secondaryBtn:hover {{
    background-color: {BORDER_COLOR};
}}

QProgressBar {{
    background-color: {DARKER_BG};
    border: none;
    border-radius: 8px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {ACCENT_COLOR};
    border-radius: 8px;
}}

QLabel#title {{
    font-size: 28px;
    font-weight: bold;
    color: {TEXT_COLOR};
}}

QLabel#subtitle {{
    font-size: 14px;
    color: {TEXT_SECONDARY};
}}

QLabel#sectionTitle {{
    font-size: 14px;
    font-weight: bold;
    color: {TEXT_COLOR};
    margin-bottom: 8px;
}}

QFrame#previewFrame {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 12px;
    min-height: 300px;
}}

QFrame#generatorCard {{
    background-color: {CARD_BG};
    border: 2px solid {BORDER_COLOR};
    border-radius: 12px;
    padding: 16px;
}}

QFrame#generatorCard:hover {{
    border-color: {ACCENT_COLOR};
}}

QFrame#selectedCard {{
    background-color: {CARD_BG};
    border: 2px solid {ACCENT_COLOR};
    border-radius: 12px;
    padding: 16px;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}
"""


class GeneratorCard(QFrame):
    """Clickable card for selecting generator type."""

    clicked = pyqtSignal(str)

    def __init__(self, name: str, description: str, icon_text: str, is_free: bool = False):
        super().__init__()
        self.name = name
        self.selected = False
        self.setObjectName("generatorCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(160, 130)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)

        # Icon
        icon_label = QLabel(icon_text)
        icon_label.setFont(QFont("Segoe UI", 24))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        # Name with FREE badge
        name_layout = QHBoxLayout()
        name_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        name_label = QLabel(name)
        name_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_layout.addWidget(name_label)

        if is_free:
            free_badge = QLabel("FREE")
            free_badge.setStyleSheet(f"""
                background-color: {SUCCESS_COLOR};
                color: white;
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 9px;
                font-weight: bold;
            """)
            name_layout.addWidget(free_badge)

        layout.addLayout(name_layout)

        # # Description
        # desc_label = QLabel(description)
        # desc_label.setFont(QFont("Segoe UI", 9))
        # desc_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        # desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # desc_label.setWordWrap(True)
        # layout.addWidget(desc_label)

    def mousePressEvent(self, event):
        self.clicked.emit(self.name)

    def setSelected(self, selected: bool):
        self.selected = selected
        self.setObjectName("selectedCard" if selected else "generatorCard")
        self.style().unpolish(self)
        self.style().polish(self)


class WorkerThread(QThread):
    """Background worker for sticker generation."""

    finished = pyqtSignal(str)  # Output path
    error = pyqtSignal(str)  # Error message
    progress = pyqtSignal(str)  # Progress message

    def __init__(self, task_type: str, params: dict):
        super().__init__()
        self.task_type = task_type
        self.params = params

    def run(self):
        try:
            output_path = None

            # ===== STICKERS TAB =====
            if self.task_type == "free_sticker":
                self.progress.emit("Generating sticker with Pollinations.ai...")
                image = generate_sticker_free(self.params["prompt"])
                self.progress.emit("Creating animated WebP...")
                output_path = free_create_animated(
                    image,
                    self.params["animation"],
                    self.params["output_file"]
                )

            elif self.task_type == "replicate_sticker":
                self.progress.emit("Generating sticker with Replicate...")
                image_path = replicate_generate(self.params["prompt"])
                self.progress.emit("Creating animated WebP...")
                output_path = replicate_create_animated(
                    image_path,
                    self.params["output_file"],
                    self.params["animation"]
                )

            elif self.task_type == "gemini_sticker":
                self.progress.emit("Generating sticker with Gemini...")
                image = gemini_generate(
                    self.params["prompt"],
                    self.params.get("reference_image")
                )
                self.progress.emit("Creating animated WebP...")
                output_path = gemini_create_animated(
                    image,
                    self.params["animation"],
                    self.params["output_file"]
                )

            # ===== ANIMATIONS TAB =====
            elif self.task_type == "free_animation":
                self.progress.emit("Generating animated sticker (FREE)...")
                output_path = free_animated_sticker(
                    concept=self.params["prompt"],
                    num_frames=self.params["num_frames"],
                    fps=self.params["fps"],
                    output_file=self.params["output_file"]
                )

            elif self.task_type == "replicate_animation":
                self.progress.emit("Generating animated sticker with Replicate...")
                output_path = replicate_animated_sticker(
                    concept=self.params["prompt"],
                    num_frames=self.params["num_frames"]
                )

            elif self.task_type == "gemini_animation":
                self.progress.emit("Generating animated sticker with Gemini...")
                output_path = gemini_animated_sticker(
                    concept=self.params["prompt"],
                    reference_image=self.params.get("reference_image"),
                    num_frames=self.params["num_frames"],
                    fps=self.params["fps"],
                    output_file=self.params["output_file"]
                )

            # ===== PREMIUM VIDEO TAB =====
            elif self.task_type == "video_animation":
                self.progress.emit("Generating video animation with Runware...")
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    original, transparent = loop.run_until_complete(
                        generate_runware_transparent_sticker(
                            prompt=self.params["prompt"],
                            duration=self.params["duration"],
                            fps=self.params["fps"]
                        )
                    )
                    output_path = f"{transparent}|{original}"  # Pass both paths
                finally:
                    loop.close()

                    # ===== IMAGE GENERATION TAB =====
            elif self.task_type == "image_generation":
                self.progress.emit("Generating image with Pollinations.ai...")
                output_path = generate_image(
                    prompt=self.params["prompt"],
                    width=self.params["width"],
                    height=self.params["height"],
                    output_file=self.params["output_file"],
                    seed=self.params["seed"]
                )

            if output_path:
                self.finished.emit(output_path)
            else:
                self.error.emit("No output generated")

        except Exception as e:
            self.error.emit(str(e))


class StickerGeneratorApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Sticker Generator")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet(STYLESHEET)

        # State
        # State
        self.current_generator = "Free Sticker"
        self.current_animation_generator = "Free Animation"

        # Separate preview paths (IMPORTANT)
        self.sticker_preview_path = None
        self.animation_preview_path = None
        self.image_preview_path = None
        self.video_preview_path = None
        self.current_video_mp4_path = None

        self.worker = None

        self.setup_ui()

    def setup_ui(self):
        """Setup the main UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()

        title_layout = QVBoxLayout()
        title = QLabel("🎨 AI Sticker Generator")
        title.setObjectName("title")
        title_layout.addWidget(title)

        subtitle = QLabel("Create amazing stickers & animations")
        subtitle.setObjectName("subtitle")
        title_layout.addWidget(subtitle)

        header_layout.addLayout(title_layout)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_stickers_tab(), "💜 Stickers")
        self.tabs.addTab(self.create_animations_tab(), "🎬 Animations")
        self.tabs.addTab(self.create_premium_tab(), "⭐ Premium Video")
        self.tabs.addTab(self.create_image_gen_tab(), "🖼️ Image Gen")

        main_layout.addWidget(self.tabs)

    def create_stickers_tab(self) -> QWidget:
        """Create the Stickers tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)

        # Left side - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)

        # Generator Type Selection
        gen_group = QGroupBox("Generator Type")
        gen_layout = QHBoxLayout(gen_group)

        self.sticker_cards = []

        free_card = GeneratorCard("Free Sticker", "Powered by Flux Model", "✨", is_free=True)
        free_card.clicked.connect(self.on_sticker_generator_selected)
        free_card.setSelected(True)
        self.sticker_cards.append(free_card)
        gen_layout.addWidget(free_card)

        replicate_card = GeneratorCard("Replicate Sticker", "High quality generation", "🎨", is_free=False)
        replicate_card.clicked.connect(self.on_sticker_generator_selected)
        self.sticker_cards.append(replicate_card)
        gen_layout.addWidget(replicate_card)

        gemini_card = GeneratorCard("Gemini Sticker", "With optional image reference", "🤖", is_free=False)
        gemini_card.clicked.connect(self.on_sticker_generator_selected)
        self.sticker_cards.append(gemini_card)
        gen_layout.addWidget(gemini_card)

        gen_layout.addStretch()
        left_layout.addWidget(gen_group)

        # Prompt Input
        prompt_label = QLabel("Prompt")
        prompt_label.setObjectName("sectionTitle")
        left_layout.addWidget(prompt_label)

        self.sticker_prompt = QLineEdit()
        self.sticker_prompt.setPlaceholderText("a person is going to school...")
        left_layout.addWidget(self.sticker_prompt)

        hint_label = QLabel("Describe what you want your sticker to show")
        hint_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        left_layout.addWidget(hint_label)

        # Reference Image (for Gemini)
        self.ref_image_group = QGroupBox("Reference Image (Optional)")
        ref_layout = QHBoxLayout(self.ref_image_group)

        self.ref_image_path = QLineEdit()
        self.ref_image_path.setPlaceholderText("No image selected")
        self.ref_image_path.setReadOnly(True)
        ref_layout.addWidget(self.ref_image_path)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self.browse_reference_image)
        ref_layout.addWidget(browse_btn)

        self.ref_image_group.setVisible(False)
        left_layout.addWidget(self.ref_image_group)

        # Animation Style
        anim_label = QLabel("Animation Style")
        anim_label.setObjectName("sectionTitle")
        left_layout.addWidget(anim_label)

        self.sticker_animation = QComboBox()
        self.sticker_animation.addItems(["float", "bounce", "pulse", "wiggle", "static"])
        left_layout.addWidget(self.sticker_animation)

        left_layout.addStretch()

        # Generate Button
        self.sticker_generate_btn = QPushButton("🎨 Generate Free Sticker")
        self.sticker_generate_btn.setFixedHeight(50)
        self.sticker_generate_btn.clicked.connect(self.generate_sticker)
        left_layout.addWidget(self.sticker_generate_btn)

        # Progress
        self.sticker_progress = QProgressBar()
        self.sticker_progress.setVisible(False)
        left_layout.addWidget(self.sticker_progress)

        self.sticker_status = QLabel("")
        self.sticker_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        left_layout.addWidget(self.sticker_status)

        layout.addWidget(left_panel, stretch=1)

        # Right side - Preview
        right_panel = self.create_preview_panel("sticker")
        layout.addWidget(right_panel, stretch=1)

        return tab

    def create_animations_tab(self) -> QWidget:
        """Create the Animations tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)

        # Left side - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)

        # Generator Type Selection
        gen_group = QGroupBox("Generator Type")
        gen_layout = QHBoxLayout(gen_group)

        self.animation_cards = []

        free_anim_card = GeneratorCard("Free Animation", "GPT + Pollinations", "✨", is_free=True)
        free_anim_card.clicked.connect(self.on_animation_generator_selected)
        free_anim_card.setSelected(True)
        self.animation_cards.append(free_anim_card)
        gen_layout.addWidget(free_anim_card)

        replicate_anim_card = GeneratorCard("Replicate Animation", "GPT + Replicate", "🎨", is_free=False)
        replicate_anim_card.clicked.connect(self.on_animation_generator_selected)
        self.animation_cards.append(replicate_anim_card)
        gen_layout.addWidget(replicate_anim_card)

        gemini_anim_card = GeneratorCard("Gemini Animation", "GPT + Gemini", "🤖", is_free=False)
        gemini_anim_card.clicked.connect(self.on_animation_generator_selected)
        self.animation_cards.append(gemini_anim_card)
        gen_layout.addWidget(gemini_anim_card)

        gen_layout.addStretch()
        left_layout.addWidget(gen_group)

        # Prompt Input
        prompt_label = QLabel("Animation Concept")
        prompt_label.setObjectName("sectionTitle")
        left_layout.addWidget(prompt_label)

        self.animation_prompt = QLineEdit()
        self.animation_prompt.setPlaceholderText("a cat freezing into ice...")
        left_layout.addWidget(self.animation_prompt)

        # Reference Image (for Gemini Animation)
        self.anim_ref_image_group = QGroupBox("Reference Image (Optional)")
        anim_ref_layout = QHBoxLayout(self.anim_ref_image_group)

        self.anim_ref_image_path = QLineEdit()
        self.anim_ref_image_path.setPlaceholderText("No image selected")
        self.anim_ref_image_path.setReadOnly(True)
        anim_ref_layout.addWidget(self.anim_ref_image_path)

        anim_browse_btn = QPushButton("Browse")
        anim_browse_btn.setObjectName("secondaryBtn")
        anim_browse_btn.setFixedWidth(100)
        anim_browse_btn.clicked.connect(self.browse_anim_reference_image)
        anim_ref_layout.addWidget(anim_browse_btn)

        self.anim_ref_image_group.setVisible(False)
        left_layout.addWidget(self.anim_ref_image_group)

        # Settings
        # Settings - Only Frames (FPS removed)
        frames_label = QLabel("Frames")
        frames_label.setObjectName("sectionTitle")
        left_layout.addWidget(frames_label)

        self.animation_frames = QSpinBox()
        self.animation_frames.setRange(2, 6)
        self.animation_frames.setValue(3)
        left_layout.addWidget(self.animation_frames)

        left_layout.addStretch()

        # Generate Button
        self.animation_generate_btn = QPushButton("🎬 Generate Free Animation")
        self.animation_generate_btn.setFixedHeight(50)
        self.animation_generate_btn.clicked.connect(self.generate_animation)
        left_layout.addWidget(self.animation_generate_btn)

        # Progress
        self.animation_progress = QProgressBar()
        self.animation_progress.setVisible(False)
        left_layout.addWidget(self.animation_progress)

        self.animation_status = QLabel("")
        self.animation_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        left_layout.addWidget(self.animation_status)

        layout.addWidget(left_panel, stretch=1)

        # Right side - Preview
        right_panel = self.create_preview_panel("animation")
        layout.addWidget(right_panel, stretch=1)

        return tab

    def create_premium_tab(self) -> QWidget:
        """Create the Premium Video tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)

        # Left side - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)

        # PRO Badge
        pro_layout = QHBoxLayout()
        pro_badge = QLabel("⭐ PRO")
        pro_badge.setStyleSheet(f"""
            background-color: {WARNING_COLOR};
            color: black;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
        """)
        pro_layout.addWidget(pro_badge)
        pro_layout.addStretch()
        left_layout.addLayout(pro_layout)

        info_label = QLabel("Uses Runware Video AI for smooth video-based animations")
        info_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        info_label.setWordWrap(True)
        left_layout.addWidget(info_label)

        # Prompt Input
        prompt_label = QLabel("Video Prompt")
        prompt_label.setObjectName("sectionTitle")
        left_layout.addWidget(prompt_label)

        self.video_prompt = QLineEdit()
        self.video_prompt.setPlaceholderText("A cat becoming frozen, covered in ice...")
        left_layout.addWidget(self.video_prompt)

        # Settings
        # Settings - Only Duration (FPS removed)
        duration_label = QLabel("Duration (seconds)")
        duration_label.setObjectName("sectionTitle")
        left_layout.addWidget(duration_label)

        self.video_duration = QSpinBox()
        self.video_duration.setRange(1, 10)
        self.video_duration.setValue(3)
        left_layout.addWidget(self.video_duration)

        left_layout.addStretch()

        # Generate Button
        self.video_generate_btn = QPushButton("⭐ Generate Premium Video")
        self.video_generate_btn.setFixedHeight(50)
        self.video_generate_btn.clicked.connect(self.generate_video)
        left_layout.addWidget(self.video_generate_btn)

        # Progress
        self.video_progress = QProgressBar()
        self.video_progress.setVisible(False)
        left_layout.addWidget(self.video_progress)

        self.video_status = QLabel("")
        self.video_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        left_layout.addWidget(self.video_status)

        layout.addWidget(left_panel, stretch=1)

        # Right side - Preview
        right_panel = self.create_preview_panel("video")
        layout.addWidget(right_panel, stretch=1)

        return tab

    def create_image_gen_tab(self) -> QWidget:
        """Create the Image Generation tab."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setSpacing(24)

        # Left side - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(16)

        # FREE Badge
        free_layout = QHBoxLayout()
        free_badge = QLabel("🆓 FREE")
        free_badge.setStyleSheet(f"""
            background-color: {SUCCESS_COLOR};
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-weight: bold;
        """)
        free_layout.addWidget(free_badge)
        free_layout.addStretch()
        left_layout.addLayout(free_layout)

        info_label = QLabel("Generate images using Pollinations.ai (Flux Model) - No API key required!")
        info_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        info_label.setWordWrap(True)
        left_layout.addWidget(info_label)

        # Prompt Input
        prompt_label = QLabel("Prompt")
        prompt_label.setObjectName("sectionTitle")
        left_layout.addWidget(prompt_label)

        self.image_prompt = QLineEdit()
        self.image_prompt.setPlaceholderText("A beautiful sunset over mountains...")
        left_layout.addWidget(self.image_prompt)

        hint_label = QLabel("Describe the image you want to generate")
        hint_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        left_layout.addWidget(hint_label)

        # Size Settings
        size_group = QGroupBox("Image Size")
        size_layout = QGridLayout(size_group)

        # Width
        width_label = QLabel("Width")
        width_label.setObjectName("sectionTitle")
        size_layout.addWidget(width_label, 0, 0)

        self.image_width = QSpinBox()
        self.image_width.setRange(256, 2048)
        self.image_width.setValue(1024)
        self.image_width.setSingleStep(64)
        size_layout.addWidget(self.image_width, 1, 0)

        # Height
        height_label = QLabel("Height")
        height_label.setObjectName("sectionTitle")
        size_layout.addWidget(height_label, 0, 1)

        self.image_height = QSpinBox()
        self.image_height.setRange(256, 2048)
        self.image_height.setValue(1024)
        self.image_height.setSingleStep(64)
        size_layout.addWidget(self.image_height, 1, 1)

        # # Preset buttons
        # preset_label = QLabel("Presets:")
        # preset_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
        # size_layout.addWidget(preset_label, 2, 0, 1, 2)
        #
        # preset_layout = QHBoxLayout()
        #
        # square_btn = QPushButton("1:1")
        # square_btn.setObjectName("secondaryBtn")
        # square_btn.setFixedWidth(60)
        # square_btn.clicked.connect(lambda: self.set_image_size(1024, 1024))
        # preset_layout.addWidget(square_btn)
        #
        # landscape_btn = QPushButton("16:9")
        # landscape_btn.setObjectName("secondaryBtn")
        # landscape_btn.setFixedWidth(60)
        # landscape_btn.clicked.connect(lambda: self.set_image_size(1920, 1080))
        # preset_layout.addWidget(landscape_btn)
        #
        # portrait_btn = QPushButton("9:16")
        # portrait_btn.setObjectName("secondaryBtn")
        # portrait_btn.setFixedWidth(60)
        # portrait_btn.clicked.connect(lambda: self.set_image_size(1080, 1920))
        # preset_layout.addWidget(portrait_btn)
        #
        # wide_btn = QPushButton("21:9")
        # wide_btn.setObjectName("secondaryBtn")
        # wide_btn.setFixedWidth(60)
        # wide_btn.clicked.connect(lambda: self.set_image_size(2048, 878))
        # preset_layout.addWidget(wide_btn)
        #
        # preset_layout.addStretch()
        # size_layout.addLayout(preset_layout, 3, 0, 1, 2)

        left_layout.addWidget(size_group)

        # Seed
        # seed_layout = QHBoxLayout()
        #
        # seed_label = QLabel("Seed")
        # seed_label.setObjectName("sectionTitle")
        # seed_layout.addWidget(seed_label)
        #
        # self.image_seed = QSpinBox()
        # self.image_seed.setRange(1, 99999)
        # self.image_seed.setValue(42)
        # seed_layout.addWidget(self.image_seed)
        #
        # random_seed_btn = QPushButton("🎲")
        # random_seed_btn.setObjectName("secondaryBtn")
        # random_seed_btn.setFixedWidth(40)
        # random_seed_btn.setToolTip("Random seed")
        # random_seed_btn.clicked.connect(self.randomize_seed)
        # seed_layout.addWidget(random_seed_btn)
        #
        # seed_layout.addStretch()
        # left_layout.addLayout(seed_layout)

        left_layout.addStretch()

        # Generate Button
        self.image_generate_btn = QPushButton("🖼️ Generate Image")
        self.image_generate_btn.setFixedHeight(50)
        self.image_generate_btn.clicked.connect(self.generate_image)
        left_layout.addWidget(self.image_generate_btn)

        # Progress
        self.image_progress = QProgressBar()
        self.image_progress.setVisible(False)
        left_layout.addWidget(self.image_progress)

        self.image_status = QLabel("")
        self.image_status.setStyleSheet(f"color: {TEXT_SECONDARY};")
        left_layout.addWidget(self.image_status)

        layout.addWidget(left_panel, stretch=1)

        # Right side - Preview
        right_panel = self.create_preview_panel("image")
        layout.addWidget(right_panel, stretch=1)

        return tab

    # def set_image_size(self, width: int, height: int):
    #     """Set image dimensions from preset."""
    #     self.image_width.setValue(width)
    #     self.image_height.setValue(height)
    #
    # def randomize_seed(self):
    #     """Set a random seed."""
    #     import random
    #     self.image_seed.setValue(random.randint(1, 99999))

    def create_preview_panel(self, panel_type: str) -> QFrame:
        """Create a preview panel."""
        frame = QFrame()
        frame.setObjectName("previewFrame")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Preview")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        layout.addWidget(title)

        # Preview area
        preview_container = QWidget()
        preview_container.setStyleSheet(f"background-color: {DARKER_BG}; border-radius: 8px;")
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Preview label (for image/animation)
        preview_label = QLabel()
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setMinimumSize(400, 400)

        # Store reference based on panel type
        if panel_type == "sticker":
            self.sticker_preview_label = preview_label
        elif panel_type == "animation":
            self.animation_preview_label = preview_label
        elif panel_type == "image":
            self.image_preview_label = preview_label
        else:
            self.video_preview_label = preview_label

        # Placeholder
        placeholder = QLabel("🖼️\n\nNo preview yet\nGenerate something to see it here")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet(f"color: {TEXT_SECONDARY};")

        if panel_type == "sticker":
            self.sticker_placeholder = placeholder
        elif panel_type == "animation":
            self.animation_placeholder = placeholder
        elif panel_type == "image":
            self.image_placeholder = placeholder
        else:
            self.video_placeholder = placeholder

        preview_layout.addWidget(placeholder)
        preview_layout.addWidget(preview_label)
        preview_label.setVisible(False)

        layout.addWidget(preview_container, stretch=1)

        # Save button
        # Save button(s)
        save_btn = QPushButton("💾 Save Sticker")
        save_btn.setObjectName("secondaryBtn")
        save_btn.clicked.connect(lambda: self.save_sticker(panel_type))

        if panel_type == "sticker":
            self.sticker_save_btn = save_btn
        elif panel_type == "animation":
            self.animation_save_btn = save_btn
        elif panel_type == "image":
            save_btn.setText("💾 Save Image")
            self.image_save_btn = save_btn
        else:
            self.video_save_btn = save_btn

            # Add MP4 save button for video
            save_mp4_btn = QPushButton("🎬 Save MP4")
            save_mp4_btn.setObjectName("secondaryBtn")
            save_mp4_btn.clicked.connect(self.save_video_mp4)
            save_mp4_btn.setEnabled(False)
            self.video_save_mp4_btn = save_mp4_btn

        save_btn.setEnabled(False)
        layout.addWidget(save_btn)

        # Add MP4 button only for video panel
        if panel_type == "video":
            layout.addWidget(self.video_save_mp4_btn)

        return frame

    # ============== EVENT HANDLERS ==============

    def on_sticker_generator_selected(self, name: str):
        """Handle sticker generator selection."""
        self.current_generator = name

        for card in self.sticker_cards:
            card.setSelected(card.name == name)

        # Update button text
        self.sticker_generate_btn.setText(f"🎨 Generate {name}")

        # Show/hide reference image option for Gemini
        self.ref_image_group.setVisible(name == "Gemini Sticker")

    def on_animation_generator_selected(self, name: str):
        """Handle animation generator selection."""
        self.current_animation_generator = name

        for card in self.animation_cards:
            card.setSelected(card.name == name)

        # Update button text
        self.animation_generate_btn.setText(f"🎬 Generate {name}")

        # Show/hide reference image option for Gemini
        self.anim_ref_image_group.setVisible(name == "Gemini Animation")

    def browse_reference_image(self):
        """Browse for reference image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Image", "",
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if file_path:
            self.ref_image_path.setText(file_path)

    def browse_anim_reference_image(self):
        """Browse for animation reference image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Image", "",
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if file_path:
            self.anim_ref_image_path.setText(file_path)

    def generate_sticker(self):
        """Generate sticker based on selected generator."""
        prompt = self.sticker_prompt.text().strip()
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter a prompt")
            return

        # Determine task type
        task_map = {
            "Free Sticker": "free_sticker",
            "Replicate Sticker": "replicate_sticker",
            "Gemini Sticker": "gemini_sticker"
        }

        task_type = task_map.get(self.current_generator, "free_sticker")

        params = {
            "prompt": prompt,
            "animation": self.sticker_animation.currentText(),
            "output_file": "output_sticker.webp",
            "reference_image": self.ref_image_path.text() if self.ref_image_path.text() else None
        }

        self.start_worker(task_type, params, "sticker")

    def generate_animation(self):
        """Generate animation based on selected generator."""
        prompt = self.animation_prompt.text().strip()
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter a concept")
            return

        task_map = {
            "Free Animation": "free_animation",
            "Replicate Animation": "replicate_animation",
            "Gemini Animation": "gemini_animation"
        }

        task_type = task_map.get(self.current_animation_generator, "free_animation")

        params = {
            "prompt": prompt,
            "num_frames": self.animation_frames.value(),
            "fps": 3,  # Fixed FPS
            "output_file": "output_animation.webp",
            "reference_image": self.anim_ref_image_path.text() if self.anim_ref_image_path.text() else None
        }

        self.start_worker(task_type, params, "animation")

    def generate_video(self):
        """Generate premium video animation."""
        prompt = self.video_prompt.text().strip()
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter a prompt")
            return

        params = {
            "prompt": prompt,
            "duration": self.video_duration.value(),
            "fps": 10
        }

        self.start_worker("video_animation", params, "video")

    def generate_image(self):
        """Generate image using Pollinations."""
        prompt = self.image_prompt.text().strip()
        if not prompt:
            QMessageBox.warning(self, "Error", "Please enter a prompt")
            return

        import random
        params = {
            "prompt": prompt,
            "width": self.image_width.value(),
            "height": self.image_height.value(),
            "seed": random.randint(1, 99999),
            "output_file": "output_image.jpg"
        }

        self.start_worker("image_generation", params, "image")

    def start_worker(self, task_type: str, params: dict, panel_type: str):
        """Start background worker for generation."""
        # Disable button and show progress
        if panel_type == "sticker":
            self.sticker_generate_btn.setEnabled(False)
            self.sticker_progress.setVisible(True)
            self.sticker_progress.setRange(0, 0)  # Indeterminate
            self.sticker_status.setText("Starting...")
        elif panel_type == "animation":
            self.animation_generate_btn.setEnabled(False)
            self.animation_progress.setVisible(True)
            self.animation_progress.setRange(0, 0)
            self.animation_status.setText("Starting...")

        elif panel_type == "image":
            self.image_generate_btn.setEnabled(False)
            self.image_progress.setVisible(True)
            self.image_progress.setRange(0, 0)
            self.image_status.setText("Starting...")

        else:
            self.video_generate_btn.setEnabled(False)
            self.video_progress.setVisible(True)
            self.video_progress.setRange(0, 0)
            self.video_status.setText("Starting...")

        # Create and start worker
        self.worker = WorkerThread(task_type, params)
        self.worker.finished.connect(lambda path: self.on_generation_finished(path, panel_type))
        self.worker.error.connect(lambda err: self.on_generation_error(err, panel_type))
        self.worker.progress.connect(lambda msg: self.on_generation_progress(msg, panel_type))
        self.worker.start()

    def on_generation_progress(self, message: str, panel_type: str):
        """Update progress message."""
        if panel_type == "sticker":
            self.sticker_status.setText(message)
        elif panel_type == "animation":
            self.animation_status.setText(message)
        else:
            self.video_status.setText(message)

    def on_generation_finished(self, output_path: str, panel_type: str):
        """Handle generation completion."""
        # self.current_preview_path = output_path

        # Update UI
        if panel_type == "sticker":
            self.sticker_generate_btn.setEnabled(True)
            self.sticker_progress.setVisible(False)
            self.sticker_preview_path = output_path
            self.sticker_status.setText(f"✅ Saved: {output_path}")
            self.sticker_save_btn.setEnabled(True)
            self.update_preview(output_path, self.sticker_preview_label, self.sticker_placeholder)

        elif panel_type == "animation":
            self.animation_generate_btn.setEnabled(True)
            self.animation_progress.setVisible(False)
            self.animation_preview_path = output_path
            self.animation_status.setText(f"✅ Saved: {output_path}")
            self.animation_save_btn.setEnabled(True)
            self.update_preview(output_path, self.animation_preview_label, self.animation_placeholder)


        elif panel_type == "image":
            self.image_generate_btn.setEnabled(True)
            self.image_progress.setVisible(False)
            self.image_preview_path = output_path
            self.image_status.setText(f"✅ Saved: {output_path}")
            self.image_save_btn.setEnabled(True)
            self.update_preview(output_path, self.image_preview_label, self.image_placeholder)



        else:
            # Handle video with both paths (webp|mp4)
            if "|" in output_path:
                webp_path, mp4_path = output_path.split("|")
                self.video_preview_path = webp_path
                self.current_video_mp4_path = mp4_path
                output_path = webp_path

            self.video_generate_btn.setEnabled(True)
            self.video_progress.setVisible(False)
            self.video_status.setText(f"✅ Saved: {output_path}")
            self.video_save_btn.setEnabled(True)
            self.video_save_mp4_btn.setEnabled(True)
            self.update_preview(output_path, self.video_preview_label, self.video_placeholder)

    def on_generation_error(self, error: str, panel_type: str):
        """Handle generation error."""
        if panel_type == "sticker":
            self.sticker_generate_btn.setEnabled(True)
            self.sticker_progress.setVisible(False)
            self.sticker_status.setText(f"❌ Error: {error}")
        elif panel_type == "animation":
            self.animation_generate_btn.setEnabled(True)
            self.animation_progress.setVisible(False)
            self.animation_status.setText(f"❌ Error: {error}")

        elif panel_type == "image":
            self.image_generate_btn.setEnabled(True)
            self.image_progress.setVisible(False)
            self.image_status.setText(f"❌ Error: {error}")

        else:
            self.video_generate_btn.setEnabled(True)
            self.video_progress.setVisible(False)
            self.video_status.setText(f"❌ Error: {error}")

        QMessageBox.critical(self, "Generation Error", str(error))

    def update_preview(self, path: str, label: QLabel, placeholder: QLabel):
        """Update preview with generated image/animation."""
        placeholder.setVisible(False)
        label.setVisible(True)

        if path.endswith('.webp') or path.endswith('.gif'):
            # Animated preview
            movie = QMovie(path)
            movie.setScaledSize(QSize(300, 300))
            label.setMovie(movie)
            movie.start()
        else:
            # Static image
            pixmap = QPixmap(path)
            pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)

    def save_sticker(self, panel_type: str):
        path_map = {
            "sticker": self.sticker_preview_path,
            "animation": self.animation_preview_path,
            "image": self.image_preview_path,
            "video": self.video_preview_path,
        }

        source_path = path_map.get(panel_type)

        if not source_path or not os.path.exists(source_path):
            QMessageBox.warning(self, "Error", "No valid file to save.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save File",
            os.path.basename(source_path),
            "WebP Files (*.webp);;All Files (*)"
        )

        if save_path:
            import shutil
            shutil.copy(source_path, save_path)
            QMessageBox.information(self, "Saved", f"Saved to:\n{save_path}")

    def save_video_mp4(self):
        """Save the generated MP4 video to user-selected location."""
        if not self.current_video_mp4_path:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Video", "video.mp4",
            "MP4 Files (*.mp4);;All Files (*)"
        )

        if save_path:
            import shutil
            shutil.copy(self.current_video_mp4_path, save_path)
            QMessageBox.information(self, "Saved", f"Video saved to:\n{save_path}")


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Set dark palette
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(DARK_BG))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Base, QColor(DARKER_BG))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Button, QColor(CARD_BG))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT_COLOR))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_COLOR))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(TEXT_COLOR))
    app.setPalette(palette)

    window = StickerGeneratorApp()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
