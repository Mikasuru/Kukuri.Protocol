import os
import json
import shutil
from pathlib import Path
from PyQt6.QtGui import QColor, QFont, QImage
from PyQt6.QtWidgets import QMessageBox
from typing import Optional, Dict, Any

class ThemeManager:
    def __init__(self, themes_dir: str = "themes"):
        self.themes_dir = Path(themes_dir)
        self.current_theme: Optional[Dict[str, Any]] = None
        self.current_theme_name: Optional[str] = None
        
        if not self.themes_dir.exists():
            self.themes_dir.mkdir()
        
        if not (self.themes_dir / "default").exists():
            self._create_default_theme()
    
    def _validate_theme(self, theme_data: dict) -> bool:
        """ตรวจสอบความถูกต้องของ theme"""
        required_fields = ["name", "author", "version", "styles"]
        if not all(field in theme_data for field in required_fields):
            print("Missing required fields in theme")
            return False
            
        required_styles = ["window", "chat_area", "buttons", "input_field", "contact_list"]
        if not all(style in theme_data["styles"] for style in required_styles):
            print("Missing required styles in theme")
            return False
            
        if "assets" in theme_data and self.current_theme_name:
            theme_dir = self.themes_dir / self.current_theme_name
            for asset_name, asset_path in theme_data["assets"].items():
                full_path = theme_dir / asset_path
                if not full_path.exists():
                    print(f"Missing asset file: {asset_path}")
                    return False
                
        return True

    def get_available_themes(self) -> list[str]:
        """รับรายชื่อ theme ที่มีทั้งหมด"""
        themes = []
        if self.themes_dir.exists():
            for theme_dir in self.themes_dir.iterdir():
                if theme_dir.is_dir() and (theme_dir / "theme.json").exists():
                    themes.append(theme_dir.name)
        return themes

    def _create_default_theme(self):
        """สร้าง default theme"""
        default_theme = {
            "name": "Default Theme",
            "author": "System",
            "version": "1.0",
            "assets": {},
            "styles": {
                "window": {
                    "background": "#FFFFFF",
                    "font_family": "Arial",
                    "font_size": 12
                },
                "chat_area": {
                    "background": "#F5F5F5",
                    "text_color": "#000000",
                    "message_spacing": 5,
                    "sent_message_bg": "#DCF8C6",
                    "received_message_bg": "#FFFFFF",
                    "timestamp_color": "#808080",
                    "message_padding": [8, 12, 8, 12]
                },
                "buttons": {
                    "background": "#007BFF",
                    "text_color": "#FFFFFF",
                    "border_radius": 5,
                    "padding": [5, 10, 5, 10],
                    "hover_background": "#0056b3",
                    "pressed_background": "#004085"
                },
                "input_field": {
                    "background": "#FFFFFF",
                    "text_color": "#000000",
                    "border_color": "#CCCCCC"
                },
                "contact_list": {
                    "background": "#FFFFFF",
                    "selected_background": "#E3F2FD",
                    "text_color": "#000000",
                    "offline_color": "#808080",
                    "online_color": "#008000",
                    "unread_color": "#FF0000"
                },
                "scrollbar": {
                    "background": "#F0F0F0",
                    "handle_color": "#C1C1C1",
                    "handle_hover_color": "#A8A8A8",
                    "width": 8
                }
            }
        }
        
        default_dir = self.themes_dir / "default"
        default_dir.mkdir(exist_ok=True)
        
        with open(default_dir / "theme.json", "w", encoding="utf-8") as f:
            json.dump(default_theme, f, indent=4)
    
    def load_theme(self, theme_name: str) -> bool:
        """โหลด theme จากชื่อ"""
        theme_path = self.themes_dir / theme_name / "theme.json"
        if not theme_path.exists():
            print(f"Theme file not found: {theme_path}")
            return False
        
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                theme_data = json.load(f)
            
            self.current_theme_name = theme_name
            
            if not self._validate_theme(theme_data):
                self.current_theme_name = None
                return False
            
            self.current_theme = theme_data
            return True
            
        except Exception as e:
            print(f"Error loading theme: {e}")
            self.current_theme_name = None
            return False
    
    def import_theme(self, theme_path: str) -> bool:
        """นำเข้า theme จากไฟล์ zip"""
        try:
            import zipfile
            with zipfile.ZipFile(theme_path, 'r') as zip_ref:
                if "theme.json" not in [file.filename for file in zip_ref.filelist]:
                    print("No theme.json found in zip file")
                    return False
                
                theme_data = json.loads(zip_ref.read("theme.json"))
                theme_name = theme_data["name"]
                
                theme_dir = self.themes_dir / theme_name
                theme_dir.mkdir(exist_ok=True)
                
                zip_ref.extractall(theme_dir)
                
                return True
        except Exception as e:
            print(f"Error importing theme: {e}")
            return False
    
    def export_theme(self, theme_name: str, export_path: str) -> bool:
        """ส่งออก theme เป็นไฟล์ zip"""
        try:
            import zipfile
            theme_dir = self.themes_dir / theme_name
            
            with zipfile.ZipFile(export_path, 'w') as zip_ref:
                for file_path in theme_dir.rglob("*"):
                    if file_path.is_file():
                        zip_ref.write(file_path, file_path.relative_to(theme_dir))
            return True
        except Exception as e:
            print(f"Error exporting theme: {e}")
            return False
    
    def apply_theme_to_widget(self, widget, widget_type: str):
        """ใช้ theme กับ widget"""
        if not self.current_theme:
            return
        
        styles = self.current_theme["styles"]
        if widget_type not in styles:
            return
        
        style = styles[widget_type]
        stylesheet_parts = []
        
        if widget_type == "buttons":
            base_selector = "QPushButton"
        elif widget_type == "input_field":
            base_selector = "QLineEdit"
        elif widget_type == "chat_area":
            base_selector = "QTextEdit"
        elif widget_type == "contact_list":
            base_selector = "QListWidget"
        elif widget_type == "window":
            base_selector = "QWidget"
        else:
            base_selector = ""
        
        main_style = []
        
        if "background" in style:
            if ("background_image" in style and 
                "assets" in self.current_theme and 
                self.current_theme_name is not None):
                
                image_path = str(self.themes_dir / self.current_theme_name / style["background_image"])
                image_path = image_path.replace('\\', '/') 
                
                if Path(image_path).exists():
                    main_style.append(f"background-image: url('{image_path}');")
                    main_style.append("background-repeat: no-repeat;")
                    main_style.append("background-position: center;")
                    main_style.append("background-attachment: fixed;")
                    if "background_opacity" in style:
                        main_style.append(f"background-color: rgba(255, 255, 255, {style['background_opacity']});")
                else:
                    main_style.append(f"background-color: {style['background']};")
            else:
                main_style.append(f"background-color: {style['background']};")
        
        if "text_color" in style:
            main_style.append(f"color: {style['text_color']};")
        
        if "border_color" in style:
            main_style.append(f"border: 1px solid {style['border_color']};")
        
        if "border_radius" in style:
            main_style.append(f"border-radius: {style['border_radius']}px;")
        
        if "padding" in style:
            padding = style["padding"]
            if isinstance(padding, list) and len(padding) == 4:
                main_style.append(f"padding: {padding[0]}px {padding[1]}px {padding[2]}px {padding[3]}px;")
        
        if main_style:
            stylesheet_parts.append(f"{base_selector} {{ {' '.join(main_style)} }}")
        
        if widget_type == "buttons":
            if "hover_background" in style:
                stylesheet_parts.append(f"{base_selector}:hover {{ background-color: {style['hover_background']}; }}")
            if "pressed_background" in style:
                stylesheet_parts.append(f"{base_selector}:pressed {{ background-color: {style['pressed_background']}; }}")
        
        if widget_type == "contact_list":
            if "selected_background" in style:
                stylesheet_parts.append(f"{base_selector}::item:selected {{ background: {style['selected_background']}; }}")
            if "online_color" in style:
                stylesheet_parts.append(f"{base_selector}::item[online=true] {{ color: {style['online_color']}; }}")
            if "offline_color" in style:
                stylesheet_parts.append(f"{base_selector}::item[online=false] {{ color: {style['offline_color']}; }}")
        
        if "scrollbar" in self.current_theme["styles"]:
            scrollbar = self.current_theme["styles"]["scrollbar"]
            if "width" in scrollbar:
                stylesheet_parts.append(f"{base_selector} QScrollBar:vertical {{ width: {scrollbar['width']}px; }}")
            if "background" in scrollbar:
                stylesheet_parts.append(f"{base_selector} QScrollBar:vertical {{ background: {scrollbar['background']}; }}")
            if "handle_color" in scrollbar:
                stylesheet_parts.append(f"{base_selector} QScrollBar::handle:vertical {{ background: {scrollbar['handle_color']}; }}")
            if "handle_hover_color" in scrollbar:
                stylesheet_parts.append(f"{base_selector} QScrollBar::handle:vertical:hover {{ background: {scrollbar['handle_hover_color']}; }}")
        
        if stylesheet_parts:
            full_stylesheet = " ".join(stylesheet_parts)
            print(f"Applying stylesheet to {widget_type}:")
            print(full_stylesheet)
            try:
                widget.setStyleSheet(full_stylesheet)
            except Exception as e:
                print(f"Error applying stylesheet: {e}")
        
        if "font_family" in style and "font_size" in style:
            font = QFont(style["font_family"], style["font_size"])
            widget.setFont(font)