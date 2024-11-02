from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import sys
import asyncio
import websockets
import json
import base64
from datetime import datetime
from plyer import notification 

from theme_manager import ThemeManager
import os

class ProfileEditDialog(QDialog):
    def __init__(self, username, current_profile, parent=None):
        super().__init__(parent)
        self.username = username
        self.current_profile = current_profile
        self.profile_image_data = None
        self.additional_image_data = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('Edit Profile')
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: white;
                font-size: 14px;
                margin-top: 10px;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 5px;
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                margin-bottom: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 5px;
                background-color: #3B82F6;
                color: white;
                border: none;
                margin-top: 15px;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton#cancelButton {
                background-color: #4B5563;
            }
            QPushButton#cancelButton:hover {
                background-color: #374151;
            }
            QPushButton#imageButton {
                margin-top: 5px;
                background-color: #4B5563;
                padding: 5px 10px;
            }
            QPushButton#imageButton:hover {
                background-color: #374151;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Profile Picture Section
        layout.addWidget(QLabel('Profile Picture:'))
        profile_image_layout = QHBoxLayout()
        
        # Profile picture preview container
        profile_container = QWidget()
        profile_container.setFixedSize(128, 128) 
        profile_layout = QVBoxLayout(profile_container)
        profile_layout.setContentsMargins(0, 0, 0, 0)
        
        self.profile_preview = QLabel()
        self.profile_preview.setFixedSize(128, 128)
        self.profile_preview.setStyleSheet("""
            background-color: #2d2d2d;
            border-radius: 64px;
        """)
        
        if self.current_profile.get('profile_image'):
            self.set_profile_preview(self.current_profile['profile_image'])
        else:
            self.profile_preview.setText(self.username[0].upper())
            self.profile_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        profile_layout.addWidget(self.profile_preview)
        profile_image_layout.addWidget(profile_container)
        
        profile_btn_container = QVBoxLayout()
        self.select_profile_btn = QPushButton('Select New Profile Picture')
        self.select_profile_btn.setObjectName('imageButton')
        self.select_profile_btn.clicked.connect(self.select_profile_image)
        profile_btn_container.addWidget(self.select_profile_btn)
        profile_image_layout.addLayout(profile_btn_container)
        
        layout.addLayout(profile_image_layout)
        
        # Display Name
        layout.addWidget(QLabel('Display Name:'))
        self.display_name_input = QLineEdit()
        self.display_name_input.setText(self.current_profile.get('display_name', ''))
        self.display_name_input.setPlaceholderText('Enter new display name')
        layout.addWidget(self.display_name_input)
        
        # Current Password
        layout.addWidget(QLabel('Current Password:'))
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password.setPlaceholderText('Enter current password')
        layout.addWidget(self.current_password)
        
        # New Password
        layout.addWidget(QLabel('New Password:'))
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password.setPlaceholderText('Enter new password (leave blank if no change)')
        layout.addWidget(self.new_password)
        
        # Confirm New Password
        layout.addWidget(QLabel('Confirm New Password:'))
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password.setPlaceholderText('Confirm new password')
        layout.addWidget(self.confirm_password)
        
        # Additional Image
        layout.addWidget(QLabel('Additional Image:'))
        image_layout = QHBoxLayout()
        
        self.additional_preview = QLabel()
        self.additional_preview.setFixedSize(200, 100)
        self.additional_preview.setStyleSheet("""
            background-color: #2d2d2d;
            border-radius: 5px;
            padding: 5px;
        """)
        
        if self.current_profile.get('additional_image'):
            pixmap = QPixmap()
            pixmap.loadFromData(base64.b64decode(self.current_profile['additional_image']))
            pixmap = pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio)
            self.additional_preview.setPixmap(pixmap)
        
        image_layout.addWidget(self.additional_preview)
        
        self.select_additional_btn = QPushButton('Select New Additional Image')
        self.select_additional_btn.setObjectName('imageButton')
        self.select_additional_btn.clicked.connect(self.select_additional_image)
        image_layout.addWidget(self.select_additional_btn)
        
        layout.addLayout(image_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton('Save Changes')
        save_btn.clicked.connect(self.save_changes)
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setObjectName('cancelButton')
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)

    def set_profile_preview(self, image_data, is_base64=True):
        try:
            if is_base64:
                image_data = base64.b64decode(image_data)
            
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, 
                                        Qt.TransformationMode.SmoothTransformation)
            
            rounded = QPixmap(scaled_pixmap.size())
            rounded.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            path = QPainterPath()
            path.addEllipse(0, 0, 100, 100)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, scaled_pixmap)
            painter.end()
            
            self.profile_preview.setPixmap(rounded)
        except Exception as e:
            print(f"Error setting profile preview: {e}")

    def select_profile_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Profile Picture",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            with open(file_path, 'rb') as f:
                image_data = f.read()
                self.profile_image_data = base64.b64encode(image_data).decode('utf-8')
                self.set_profile_preview(image_data, is_base64=False)

    def select_additional_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Additional Image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            with open(file_path, 'rb') as f:
                self.additional_image_data = base64.b64encode(f.read()).decode('utf-8')
            
            pixmap = QPixmap(file_path)
            pixmap = pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio)
            self.additional_preview.setPixmap(pixmap)
    
    def save_changes(self):
        if self.new_password.text():
            if self.new_password.text() != self.confirm_password.text():
                QMessageBox.warning(self, 'Error', 'New passwords do not match!')
                return
            if not self.current_password.text():
                QMessageBox.warning(self, 'Error', 'Please enter current password!')
                return
        
        confirm = QMessageBox.question(
            self,
            'Confirm Changes',
            'Are you sure you want to save these changes?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            self.accept()

    def get_updated_data(self):
        data = {
            'display_name': self.display_name_input.text(),
            'current_password': self.current_password.text(),
            'new_password': self.new_password.text() if self.new_password.text() else None
        }
        
        if self.profile_image_data:
            data['profile_image'] = self.profile_image_data
            
        if self.additional_image_data:
            data['additional_image'] = self.additional_image_data
            
        return data

class MessageBubble(QWidget):
    def __init__(self, message, timestamp, is_sender=False, profile_image=None, parent=None):
        super().__init__(parent)
        self.setProperty("is_sender", is_sender)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 2, 10, 2)
        main_layout.setSpacing(8)
        
        if is_sender:
            main_layout.addStretch()
        
        if not is_sender:
            profile_frame = QFrame()
            profile_frame.setStyleSheet("""
                QFrame {
                    background: transparent;
                    border: none;
                    min-width: 45px;
                    min-height: 45px;
                    max-width: 45px;
                    max-height: 45px;
                }
            """)
            
            profile_frame_layout = QGridLayout(profile_frame)
            profile_frame_layout.setContentsMargins(0, 0, 0, 0)
            profile_frame_layout.setSpacing(0)
            
            profile_container = QLabel()
            profile_container.setFixedSize(45, 45)
            profile_container.setStyleSheet("""
                QLabel {
                    background-color: #2d2d2d;
                    border-radius: 22.5px;
                    padding: 0px;
                    margin: 0px;
                }
            """)
            
            if profile_image:
                try:
                    pixmap = QPixmap()
                    pixmap.loadFromData(base64.b64decode(profile_image))
                    
                    target_size = 45
                    aspect_ratio = pixmap.width() / pixmap.height()
                    
                    if aspect_ratio > 1:
                        height = target_size
                        width = int(height * aspect_ratio)
                    else:
                        width = target_size
                        height = int(width / aspect_ratio)
                    
                    scaled_pixmap = pixmap.scaled(width, height, 
                                                Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
                    
                    if width > height:
                        x = (width - target_size) // 2
                        y = 0
                    else:
                        x = 0
                        y = (height - target_size) // 2
                        
                    cropped_pixmap = scaled_pixmap.copy(x, y, target_size, target_size)
                    
                    final_pixmap = QPixmap(target_size, target_size)
                    final_pixmap.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(final_pixmap)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    
                    path = QPainterPath()
                    path.addEllipse(0, 0, target_size, target_size)
                    painter.setClipPath(path)
                    
                    painter.drawPixmap(0, 0, cropped_pixmap)
                    painter.end()
                    
                    profile_container.setPixmap(final_pixmap)
                except Exception as e:
                    print(f"Error processing profile image: {e}")
            
            profile_frame_layout.addWidget(profile_container, 0, 0, Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(profile_frame)
        
        # Message Container
        message_container = QWidget()
        message_layout = QVBoxLayout(message_container)
        message_layout.setContentsMargins(0, 0, 0, 0)
        message_layout.setSpacing(1)
        
        #message_label = QLabel()
        #message_label.setWordWrap(True)
        #message_label.setTextFormat(Qt.TextFormat.RichText)
        formatted_message = message.replace(' ', '&nbsp;')
        formatted_message = formatted_message.replace('<br>', '<br/>')
        formatted_message = formatted_message.replace('\n', '<br/>')

        message_label = QLabel()
        message_label.setWordWrap(True)
        message_label.setTextFormat(Qt.TextFormat.RichText)
        message_label.setProperty("class", "message")
        message_label.setText(formatted_message)

        #formatted_message = message.replace(' ', '&nbsp;')
        #formatted_message = formatted_message.replace('<br>', '<br/>')
        #formatted_message = formatted_message.replace('\n', '<br/>')
        
        message_label.setText(formatted_message)
        
        message_label.setMinimumWidth(50)
        message_label.setMaximumWidth(400) 
        
        message_label.setStyleSheet(f"""
            QLabel {{
                background-color: {'#0084FF' if is_sender else '#E4E6EB'};
                color: {'white' if is_sender else 'black'};
                border-radius: 15px;
                padding: 8px 12px;
                margin: 0px;
                font-size: 14px;
                line-height: 1.4;  /* เพิ่ม line height เพื่อให้อ่านง่ายขึ้น */
            }}
        """)
        message_layout.addWidget(message_label)
        
        time_label = QLabel(timestamp)
        time_label.setStyleSheet("""
            color: #65676B;
            font-size: 10px;
            margin-top: 2px;
        """)
        time_label.setAlignment(Qt.AlignmentFlag.AlignLeft if not is_sender else Qt.AlignmentFlag.AlignRight)
        message_layout.addWidget(time_label)
        
        if is_sender:
            message_container.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        main_layout.addWidget(message_container)
        
        if not is_sender:
            main_layout.addStretch()
        
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        message_container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

class ChatHistory(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #2d2d2d;
                border: none;
            }
        """)
        
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setSpacing(2) 
        self.messages_layout.setContentsMargins(10, 5, 10, 5)
        self.messages_layout.addStretch()
        
        self.scroll_area.setWidget(self.messages_widget)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.scroll_area)
    
    def add_message(self, message, timestamp, is_sender=False, profile_image=None, image_label=None):
        bubble = MessageBubble(message, timestamp, is_sender, profile_image)
        
        style = "sent_message" if is_sender else "received_message"
        if self.parent() and hasattr(self.parent(), 'theme_manager'):
            self.parent().theme_manager.apply_theme_to_widget(bubble, style)
        
        if image_label:
            bubble.message_layout.addWidget(image_label)
        
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
        
    def clear(self):
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

class ContactListItem(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, profile_data):
        super().__init__()
        self.setObjectName("contactListItem")
        
        self.setFixedHeight(74)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 20)
        layout.setSpacing(10)
        
        self.profile_data = profile_data
        
        # Profile Frame
        profile_frame = QFrame()
        profile_frame.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                min-width: 64px;
                min-height: 64px;
                max-width: 64px;
                max-height: 64px;
            }
        """)
        
        profile_frame_layout = QGridLayout(profile_frame)
        profile_frame_layout.setContentsMargins(0, 0, 0, 0)
        profile_frame_layout.setSpacing(0)
        
        profile_container = QLabel()
        profile_container.setFixedSize(64, 64)
        profile_container.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border-radius: 32px;
                padding: 0px;
                margin: 0px;
            }
        """)
        profile_frame_layout.addWidget(profile_container, 0, 0, Qt.AlignmentFlag.AlignCenter)
        
        if profile_data.get('profile_image'):
            try:
                pixmap = QPixmap()
                pixmap.loadFromData(base64.b64decode(profile_data['profile_image']))
                
                scaled_size = min(pixmap.width(), pixmap.height())
                scaled_pixmap = pixmap.scaled(scaled_size, scaled_size, 
                                            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                            Qt.TransformationMode.SmoothTransformation)
                
                x = (scaled_pixmap.width() - scaled_size) // 2
                y = (scaled_pixmap.height() - scaled_size) // 2
                cropped_pixmap = scaled_pixmap.copy(x, y, scaled_size, scaled_size)
                
                final_pixmap = QPixmap(64, 64)
                final_pixmap.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(final_pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                path = QPainterPath()
                path.addEllipse(0, 0, 64, 64)
                painter.setClipPath(path)
                
                dest_rect = QRect(0, 0, 64, 64)
                painter.drawPixmap(dest_rect, cropped_pixmap)
                painter.end()
                
                profile_container.setPixmap(final_pixmap)
            except Exception as e:
                print(f"Error processing profile image: {e}")
                profile_container.setText(profile_data['username'][0].upper())
                profile_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            profile_container.setText(profile_data['username'][0].upper())
            profile_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(profile_frame)
        
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        
        text_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.name_label = QLabel(profile_data.get('display_name', profile_data['username']))
        self.name_label.setObjectName("usernameLabel")
        self.name_label.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        text_layout.addWidget(self.name_label)
        
        if profile_data.get('status_message'):
            status_label = QLabel(profile_data['status_message'])
            status_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
            text_layout.addWidget(status_label)
        
        layout.addWidget(text_container, stretch=1)
        
        if profile_data.get('additional_image'):
            tag_container = QLabel()
            tag_container.setFixedSize(64, 40)
            tag_container.setStyleSheet("""
                QLabel {
                    border-radius: 5px;
                    padding: 0px;
                    margin: 0px;
                }
            """)
            
            try:
                tag_pixmap = QPixmap()
                tag_pixmap.loadFromData(base64.b64decode(profile_data['additional_image']))
                scaled_tag = tag_pixmap.scaled(64, 40, 
                                             Qt.AspectRatioMode.KeepAspectRatio,
                                             Qt.TransformationMode.SmoothTransformation)
                tag_container.setPixmap(scaled_tag)
            except Exception as e:
                print(f"Error processing additional image: {e}")
            
            layout.addWidget(tag_container)
        
        self.setStyleSheet("""
            QWidget#contactListItem {
                background-color: transparent;
                border-radius: 8px;
                padding: 0px;
            }
            QWidget#contactListItem:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)


    def get_username(self):
        return self.profile_data['username']

    def get_display_name(self):
        return self.profile_data.get('display_name', self.profile_data['username'])
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class ChatListItem(QWidget):
    clicked = pyqtSignal()
    
    def __init__(self, username, last_message="", time="", is_online=False):
        super().__init__()
        self.setObjectName("chatListItem")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        profile_widget = QLabel()
        profile_widget.setFixedSize(40, 40)
        profile_widget.setStyleSheet("""
            background-color: #3A3B3C;
            border-radius: 20px;
            color: white;
            qproperty-alignment: AlignCenter;
        """)
        profile_widget.setText(username[0].upper())
        
        layout.addWidget(profile_widget)
        
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(10, 0, 0, 0)
        text_layout.setSpacing(0)
        
        name_label = QLabel(username)
        name_label.setStyleSheet("font-weight: bold; color: white; font-size: 14px;")
        text_layout.addWidget(name_label)
        
        message_label = QLabel(last_message)
        message_label.setStyleSheet("color: #8E8E8E; font-size: 13px;")
        text_layout.addWidget(message_label)
        
        layout.addWidget(text_widget, stretch=1)
        
        if time:
            time_label = QLabel(time)
            time_label.setStyleSheet("color: #8E8E8E; font-size: 12px;")
            layout.addWidget(time_label)
        
        if is_online:
            self.setStyleSheet("""
                QWidget#chatListItem {
                    background-color: transparent;
                    border-radius: 8px;
                }
                QWidget#chatListItem:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
            """)
    
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class ChatClient(QMainWindow):
    message_received = pyqtSignal(str, str, str)
    status_updated = pyqtSignal(str, bool)
    
    def __init__(self):
        super().__init__()
        #self.websocket = None
        #self.username = None
        #self.chat_histories = {}
        #self.current_contact = None
        #self.unread_messages = {}
        #self.theme_manager = None
        #self._contacts_data = []
        self.websocket = None
        self.username = None
        self.chat_histories = {}
        self.current_contact = None
        self.unread_messages = {}
        self._contacts_data = []
        

        self.settings_file = "settings.json"
        self.theme_manager = ThemeManager()

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 14px;
                color: white;
                min-height: 40px;
                max-height: 120px;
            }
        """)
        
        document = self.message_input.document()
        document.contentsChanged.connect(self.adjust_input_height)
        
        self.message_input.setFixedHeight(40)
        self.message_input.installEventFilter(self)
        
        self.init_ui()
        QTimer.singleShot(0, self.initialize_theme)

    def initialize_theme(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    current_theme = settings.get('current_theme', 'default')
            else:
                current_theme = 'default'
                self.save_settings({'current_theme': current_theme})
            
            if self.theme_manager.load_theme(current_theme):
                self.apply_current_theme()
            else:
                print(f"ไม่สามารถโหลด theme: {current_theme} ได้ กำลังใช้ default theme แทน")
                self.theme_manager.load_theme('default')
                self.apply_current_theme()
                
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการโหลด theme: {e}")
            self.theme_manager.load_theme('default')
            self.apply_current_theme()

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    current_theme = settings.get('current_theme', 'default')
            else:
                current_theme = 'default'
                self.save_settings({'current_theme': current_theme})
            
            if self.theme_manager.load_theme(current_theme):
                self.apply_current_theme()
            else:
                print(f"Failed to load theme: {current_theme}, falling back to default")
                self.theme_manager.load_theme('default')
                self.apply_current_theme()
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.theme_manager.load_theme('default')
            self.apply_current_theme()

    def save_settings(self, settings):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def adjust_input_height(self):
        doc_height = self.message_input.document().size().height()
        new_height = min(doc_height + 16, 120)
        new_height = max(new_height, 40) 
        self.message_input.setFixedHeight(int(new_height))
    
    def eventFilter(self, obj, event):
        if obj == self.message_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return:
                if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    cursor = self.message_input.textCursor()
                    cursor.insertText('\n')
                    return True
                elif event.modifiers() == Qt.KeyboardModifier.NoModifier:
                    self.send_message()
                    return True
        return super().eventFilter(obj, event)

    def init_ui(self):
        self.setWindowTitle('MomoTalk')
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 20px;
                background-color: #2d2d2d;
                color: white;
                border: none;
            }
            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 20px;
                background-color: #3B82F6;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
            QPushButton#loginButton {
                background-color: #2d2d2d;
                border-radius: 20px;
                padding: 0;
                font-size: 14px;
                color: #999;
            }
            QPushButton#loginButton:hover {
                background-color: #3d3d3d;
                color: white;
            }
            QPushButton#settingsButton {
                background-color: #2d2d2d;
                border-radius: 20px;
                padding: 0;
                font-size: 20px;
                color: #999;
            }
            QPushButton#settingsButton:hover {
                background-color: #3d3d3d;
                color: white;
            }
            QListWidget {
                background-color: #1a1a1a;
                border: none;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: #1a1a1a;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #3d3d3d;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # Main layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left sidebar
        left_sidebar = QWidget()
        left_sidebar.setFixedWidth(50)
        left_sidebar.setStyleSheet("background-color: #141414;")
        left_layout = QVBoxLayout(left_sidebar)
        left_layout.setContentsMargins(5, 10, 5, 10)
        left_layout.setSpacing(10)
        
        # Profile button
        self.profile_btn = QPushButton()
        self.profile_btn.setFixedSize(40, 40)
        self.profile_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border-radius: 20px;
                padding: 0;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        self.profile_btn.setVisible(False)
        left_layout.addWidget(self.profile_btn)
        
        # Profile
        self.edit_profile_btn = QPushButton("📝")
        self.edit_profile_btn.setObjectName("profileButton")
        self.edit_profile_btn.setFixedSize(40, 40)
        self.edit_profile_btn.setStyleSheet("""
            QPushButton#profileButton {
                background-color: #2d2d2d;
                border-radius: 20px;
                padding: 0;
                font-size: 20px;
                color: #999;
            }
            QPushButton#profileButton:hover {
                background-color: #3d3d3d;
                color: white;
            }
        """)
        self.edit_profile_btn.clicked.connect(self.show_profile_editor)
        self.edit_profile_btn.setVisible(False)
        left_layout.addWidget(self.edit_profile_btn)

        # Login button
        self.login_btn = QPushButton("👤")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setFixedSize(40, 40)
        self.login_btn.setStyleSheet("""
            QPushButton#loginButton {
                background-color: #2d2d2d;
                border-radius: 20px;
                padding: 0;
                font-size: 20px;
                color: #999;
            }
            QPushButton#loginButton:hover {
                background-color: #3d3d3d;
                color: white;
            }
        """)
        self.login_btn.clicked.connect(self.show_login_menu)
        left_layout.addWidget(self.login_btn)
        
        left_layout.addStretch()
        
        # Settings button
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("settingsButton")
        settings_btn.setFixedSize(40, 40)
        settings_btn.clicked.connect(self.show_theme_selector)
        left_layout.addWidget(settings_btn)
        
        # Chat container
        chat_container = QSplitter(Qt.Orientation.Horizontal)
        
        # Chat list panel
        chat_list_panel = QWidget()
        chat_list_panel.setMinimumWidth(300)
        chat_list_panel.setStyleSheet("background-color: #1a1a1a;")
        chat_list_layout = QVBoxLayout(chat_list_panel)
        chat_list_layout.setContentsMargins(10, 10, 10, 10)
        
        # Search bar
        search_input = QLineEdit()
        search_input.setPlaceholderText("🔍 Search")
        search_input.setStyleSheet("""
            QLineEdit {
                margin: 5px 0;
                padding: 8px 15px;
                background-color: #2d2d2d;
            }
        """)
        chat_list_layout.addWidget(search_input)
        
        # Contacts list
        self.contacts_list = QListWidget()
        self.contacts_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
            }
            QListWidget::item {
                background: transparent;
                border-radius: 10px;
                padding: 5px;
                margin-bottom: 5px;
            }
            QListWidget::item:selected {
                background-color: #2d2d2d;
            }
            QListWidget::item:hover {
                background-color: #262626;
            }
        """)
        self.contacts_list.itemClicked.connect(self.contact_selected)
        chat_list_layout.addWidget(self.contacts_list)
        
        # Chat area
        chat_area = QWidget()
        chat_area.setStyleSheet("background-color: #2d2d2d;")
        chat_layout = QVBoxLayout(chat_area)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(0)
        
        # Chat header
        chat_header = QWidget()
        chat_header.setFixedHeight(60)
        chat_header.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #3d3d3d;")
        header_layout = QHBoxLayout(chat_header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        self.chat_title = QLabel("Please login first!")
        self.chat_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #999;")
        header_layout.addWidget(self.chat_title)
        
        chat_layout.addWidget(chat_header)
        
        # Chat history (OLD)
        # self.chat_history = QTextEdit()
        # self.chat_history.setReadOnly(True)

        # Neo
        self.chat_history = ChatHistory()
        self.chat_history.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                margin-bottom: 20px;
            }
        """)
        chat_layout.addWidget(self.chat_history)
        
        # Message input area
        input_widget = QWidget()
        input_widget.setFixedHeight(60) 
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(10, 0, 10, 10)  
        input_layout.setSpacing(8)  

        # Container input
        input_container = QWidget()
        input_container.setFixedHeight(35) 
        input_container.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border-radius: 17px;  /* ครึ่งหนึ่งของความสูงเพื่อให้มนพอดี */
            }
        """)

        input_container_layout = QHBoxLayout(input_container)
        input_container_layout.setContentsMargins(10, 0, 10, 0)  
        input_container_layout.setSpacing(0)

        self.message_input.setFixedHeight(50)
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: white;
                font-size: 14px;
                padding: 8px 0;
            }
        """)

        input_container_layout.addWidget(self.message_input)
        input_layout.addWidget(input_container, stretch=1) 

        send_btn = QPushButton("Send")
        send_btn.setFixedSize(70, 35)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        image_btn = QPushButton("Image")
        image_btn.setFixedSize(70, 35)
        image_btn.clicked.connect(self.send_image)
        input_layout.addWidget(image_btn)

        chat_layout.addWidget(input_widget)
        
        chat_container.addWidget(chat_list_panel)
        chat_container.addWidget(chat_area)
        chat_container.setStretchFactor(0, 1)
        chat_container.setStretchFactor(1, 2)
        
        main_layout.addWidget(left_sidebar)
        main_layout.addWidget(chat_container)
        
        self.resize(1200, 800)

    def show_profile_editor(self):
        if not self.username:
            return
            
        current_profile = {}
        for contact in self._contacts_data:
            if contact['username'] == self.username:
                current_profile = contact
                break
        
        dialog = ProfileEditDialog(self.username, current_profile, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_updated_data()
            
            async def update_profile():
                try:
                    await self.websocket.send(json.dumps({
                        'type': 'profile_update',
                        'username': self.username,
                        **updated_data
                    }))
                    
                    QMessageBox.information(self, 'Success', 'Profile update request sent!')
    
                except Exception as e:
                    QMessageBox.warning(self, 'Error', f'Error updating profile: {str(e)}')
            
            asyncio.get_event_loop().create_task(update_profile())

    def show_login_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                color: white;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
        
        login_action = menu.addAction("Login")
        register_action = menu.addAction("Register")
        
        login_action.triggered.connect(self.show_login_dialog)
        register_action.triggered.connect(self.show_register_dialog)
        
        pos = self.login_btn.mapToGlobal(self.login_btn.rect().bottomLeft())
        menu.exec(pos)

    def get_selected_contact_username(self):
        current_item = self.contacts_list.currentItem()
        if current_item:
            return current_item.data(Qt.ItemDataRole.UserRole)
        return None

    def update_contacts_list(self, contacts_data):
        try:
            self.contacts_list.clear()
            self._contacts_data = contacts_data
            for contact in contacts_data:
                if contact['username'] != self.username:
                    item = QListWidgetItem()
                    widget = ContactListItem(contact)
                    item.setSizeHint(widget.sizeHint())
                    print(f"Adding contact: {contact['username']}")
                    self.contacts_list.addItem(item)
                    self.contacts_list.setItemWidget(item, widget)
        except Exception as e:
            print(f"Error updating contacts list: {e}")

    def handle_login_success(self):
        self.login_btn.setVisible(False)
        self.profile_btn.setVisible(True)
        self.edit_profile_btn.setVisible(True)
        self.profile_btn.setText(self.username[0].upper())
        
        if self.current_contact:
            self.chat_title.setText(self.current_contact)
        else:
            self.chat_title.setText("Select a chat")
        self.chat_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

    def contact_selected(self, item):
        contact_widget = self.contacts_list.itemWidget(item)
        if not contact_widget:
            print("No contact widget found")  # Debug log
            return
        
        try:
            self.current_contact = contact_widget.get_username()
            display_name = contact_widget.get_display_name()
            print(f"Selected contact: {self.current_contact} ({display_name})")  # Debug log
            
            if self.current_contact:
                self.chat_title.setText(display_name)
                self.chat_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
                self.chat_history.clear()
                
                if self.current_contact in self.unread_messages:
                    del self.unread_messages[self.current_contact]
                
                if self.current_contact in self.chat_histories:
                    for message in self.chat_histories[self.current_contact]:
                        self.append_chat_message(
                            message['sender'],
                            message['type'],
                            message['content'],
                            message['timestamp']
                        )
        except Exception as e:
            print(f"Error in contact_selected: {e}")
    
    def create_chat_item(self, username, status=""):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        profile_pic = QLabel()
        profile_pic.setFixedSize(40, 40)
        profile_pic.setStyleSheet("""
            background-color: #3d3d3d;
            border-radius: 20px;
            color: white;
            qproperty-alignment: AlignCenter;
        """)
        profile_pic.setText(username[0].upper())
        layout.addWidget(profile_pic)
        
        text_widget = QWidget()
        text_layout = QVBoxLayout(text_widget)
        text_layout.setContentsMargins(10, 0, 0, 0)
        text_layout.setSpacing(2)
        
        name_label = QLabel(username)
        name_label.setStyleSheet("font-weight: bold; color: white;")
        text_layout.addWidget(name_label)
        
        if status:
            status_label = QLabel(status)
            status_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
            text_layout.addWidget(status_label)
        
        layout.addWidget(text_widget)
        
        return widget

    def add_chat_item(self, profile_pic, name, last_message, time, is_online=False):
        item = QListWidgetItem(self.chat_list)
        chat_widget = ChatListItem(profile_pic, name, last_message, time, is_online)
        item.setSizeHint(chat_widget.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, chat_widget)

    def show_theme_selector(self):
        themes = self.theme_manager.get_available_themes()
        if not themes:
            QMessageBox.warning(self, 'Warning', 'ไม่พบ theme ที่ใช้ได้')
            return
        
        current_theme = self.theme_manager.current_theme_name or 'default'
        theme, ok = QInputDialog.getItem(
            self, 
            'เลือก Theme',
            'เลือก theme ที่ต้องการ:',
            themes, 
            themes.index(current_theme) if current_theme in themes else 0, 
            False
        )
        
        if ok and theme:
            try:
                if self.theme_manager.load_theme(theme):
                    self.save_settings({'current_theme': theme})
                    self.apply_current_theme()
                    QMessageBox.information(self, 'สำเร็จ', f'เปลี่ยน theme เป็น "{theme}" เรียบร้อยแล้ว')
                else:
                    QMessageBox.warning(self, 'ผิดพลาด', f'ไม่สามารถโหลด theme "{theme}" ได้')
            except Exception as e:
                QMessageBox.warning(self, 'ผิดพลาด', f'เกิดข้อผิดพลาด: {str(e)}')
    
    def import_theme(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Theme",
            "",
            "Theme Files (*.zip)"
        )
        
        if file_path:
            if self.theme_manager.import_theme(file_path):
                QMessageBox.information(self, 'Success', 'Theme imported successfully')
            else:
                QMessageBox.warning(self, 'Error', 'Failed to import theme')
    
    def export_theme(self):
        if not self.theme_manager.current_theme_name:
            QMessageBox.warning(self, 'Warning', 'No theme currently loaded')
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Theme",
            f"{self.theme_manager.current_theme_name}.zip",
            "Theme Files (*.zip)"
        )
        
        if file_path:
            if self.theme_manager.export_theme(self.theme_manager.current_theme_name, file_path):
                QMessageBox.information(self, 'Success', 'Theme exported successfully')
            else:
                QMessageBox.warning(self, 'Error', 'Failed to export theme')
    
    def apply_current_theme(self):
        try:
            if not self.theme_manager or not self.theme_manager.current_theme:
                return
                
            # Main Window
            self.theme_manager.apply_theme_to_widget(self, "window")
            
            # Left Sidebar
            if hasattr(self, 'left_sidebar'):
                self.theme_manager.apply_theme_to_widget(self.left_sidebar, "sidebar")
            
            # Search Input
            if hasattr(self, 'search_input'):
                self.theme_manager.apply_theme_to_widget(self.search_input, "input_field")
            
            # Chat Area and Components
            if hasattr(self, 'chat_history'):
                self.theme_manager.apply_theme_to_widget(self.chat_history, "chat_area")
            
            if hasattr(self, 'chat_title'):
                self.theme_manager.apply_theme_to_widget(self.chat_title, "window")
                
            if hasattr(self, 'message_input'):
                self.theme_manager.apply_theme_to_widget(self.message_input, "input_field")
            
            # Contact List
            if hasattr(self, 'contacts_list'):
                self.theme_manager.apply_theme_to_widget(self.contacts_list, "contact_list")
            
            # All Buttons
            for button in self.findChildren(QPushButton):
                self.theme_manager.apply_theme_to_widget(button, "buttons")
                
            # Special Buttons
            if hasattr(self, 'send_btn'):
                self.theme_manager.apply_theme_to_widget(self.send_btn, "buttons")
            if hasattr(self, 'image_btn'):
                self.theme_manager.apply_theme_to_widget(self.image_btn, "buttons")
            
            # Message Bubbles
            for bubble in self.findChildren(MessageBubble):
                is_sender = bubble.property("is_sender")
                style = "sent_message" if is_sender else "received_message"
                self.theme_manager.apply_theme_to_widget(bubble, style)
                
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการใช้ theme: {e}")

    def show_register_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Register')
        dialog.setModal(True)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border-radius: 20px;
                background-color: #2d2d2d;
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton {
                padding: 8px 15px;
                border-radius: 20px;
                background-color: #3B82F6;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #2563EB;
            }
        """)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(10)
        
        # Username
        layout.addWidget(QLabel('Username:'))
        username_input = QLineEdit()
        username_input.setPlaceholderText('Enter username')
        layout.addWidget(username_input)
        
        # Display name
        layout.addWidget(QLabel('Display name:'))
        display_name_input = QLineEdit()
        display_name_input.setPlaceholderText('Enter display name')
        layout.addWidget(display_name_input)
        
        # Profile Image
        profile_image_layout = QHBoxLayout()
        layout.addWidget(QLabel('Profile Image:'))
        self.profile_image_path = ''
        profile_image_preview = QLabel()
        profile_image_preview.setFixedSize(100, 100)
        profile_image_preview.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border-radius: 50px;
            }
        """)
        profile_image_layout.addWidget(profile_image_preview)
        
        profile_image_btn = QPushButton('Select Image')
        profile_image_layout.addWidget(profile_image_btn)
        layout.addLayout(profile_image_layout)
        
        # Additional Image
        additional_image_layout = QHBoxLayout()
        layout.addWidget(QLabel('Additional Image:'))
        self.additional_image_path = ''
        additional_image_preview = QLabel()
        additional_image_preview.setFixedSize(200, 100)
        additional_image_preview.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border-radius: 10px;
            }
        """)
        additional_image_layout.addWidget(additional_image_preview)
        
        additional_image_btn = QPushButton('Select Image')
        additional_image_layout.addWidget(additional_image_btn)
        layout.addLayout(additional_image_layout)
        
        # Password
        layout.addWidget(QLabel('Password:'))
        password_input = QLineEdit()
        password_input.setPlaceholderText('Enter password')
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_input)
        
        # Confirm Password
        layout.addWidget(QLabel('Confirm Password:'))
        confirm_password_input = QLineEdit()
        confirm_password_input.setPlaceholderText('Confirm password')
        confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(confirm_password_input)
        
        # Status label
        status_label = QLabel('')
        status_label.setStyleSheet('color: #FF4444;')
        layout.addWidget(status_label)
        
        # Register button
        register_button = QPushButton('Register')
        layout.addWidget(register_button)
        
        def select_profile_image():
            file_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Select Profile Image",
                "",
                "Images (*.png *.jpg *.jpeg)"
            )
            if file_path:
                self.profile_image_path = file_path
                pixmap = QPixmap(file_path)
                pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                
                # Create circular mask
                rounded = QPixmap(pixmap.size())
                rounded.fill(Qt.GlobalColor.transparent)
                
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                
                path = QPainterPath()
                path.addEllipse(0, 0, pixmap.width(), pixmap.height())
                painter.setClipPath(path)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                
                profile_image_preview.setPixmap(rounded)
        
        def select_additional_image():
            file_path, _ = QFileDialog.getOpenFileName(
                dialog,
                "Select Additional Image",
                "",
                "Images (*.png *.jpg *.jpeg)"
            )
            if file_path:
                self.additional_image_path = file_path
                pixmap = QPixmap(file_path)
                pixmap = pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                additional_image_preview.setPixmap(pixmap)
        
        profile_image_btn.clicked.connect(select_profile_image)
        additional_image_btn.clicked.connect(select_additional_image)
        
        async def register():
            if not all([username_input.text(), display_name_input.text(), 
                    password_input.text(), confirm_password_input.text()]):
                status_label.setText('Please fill in all fields')
                return
            
            if password_input.text() != confirm_password_input.text():
                status_label.setText('Passwords do not match')
                return
            
            if not self.profile_image_path:
                status_label.setText('Please select a profile image')
                return
                
            try:
                if not self.websocket:
                    self.websocket = await websockets.connect(
                        'ws://localhost:8765',
                        max_size=100 * 1024 * 1024  # 100MB
                    )
                
                # Convert images to base64
                with open(self.profile_image_path, 'rb') as f:
                    profile_image = base64.b64encode(f.read()).decode('utf-8')
                
                additional_image = None
                if self.additional_image_path:
                    with open(self.additional_image_path, 'rb') as f:
                        additional_image = base64.b64encode(f.read()).decode('utf-8')
                
                await self.websocket.send(json.dumps({
                    'type': 'register',
                    'username': username_input.text(),
                    'display_name': display_name_input.text(),
                    'password': password_input.text(),
                    'profile_image': profile_image,
                    'additional_image': additional_image
                }))
                
                response = json.loads(await self.websocket.recv())
                
                if response.get('status') == 'success':
                    QMessageBox.information(dialog, 'Success', 'Registration successful!')
                    dialog.accept()
                else:
                    status_label.setText(response.get('message', 'Registration failed'))
            
            except Exception as e:
                status_label.setText(f'Error: {str(e)}')
        
        register_button.clicked.connect(
            lambda: asyncio.get_event_loop().create_task(register())
        )
        
        dialog.exec()

    def show_login_dialog(self):
        print("Opening login dialog")
        dialog = QDialog(self)
        dialog.setWindowTitle('Login')
        dialog.setModal(True)
        layout = QVBoxLayout(dialog)
        
        username_input = QLineEdit()
        username_input.setPlaceholderText('Username')
        password_input = QLineEdit()
        password_input.setPlaceholderText('Password')
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        status_label = QLabel('')
        status_label.setStyleSheet('color: red')
        
        login_button = QPushButton('Login')
        
        layout.addWidget(username_input)
        layout.addWidget(password_input)
        layout.addWidget(status_label)
        layout.addWidget(login_button)
        
        async def login():
            try:
                print("Login button clicked")
                username = username_input.text()
                password = password_input.text()
                
                if not username or not password:
                    status_label.setText('Please enter username and password')
                    status_label.setStyleSheet('color: red')
                    print("Empty username or password")
                    return
                
                status_label.setText('Connecting to server...')
                print("Attempting to connect to server")
                
                if not self.websocket:
                    try:
                        print("Creating new websocket connection")
                        self.websocket = await websockets.connect('ws://localhost:8765')
                        print("Websocket connection established")
                    except Exception as e:
                        print(f"Websocket connection error: {e}")
                        status_label.setText(f'Connection error: {str(e)}')
                        return
                
                login_data = {
                    'type': 'login',
                    'username': username,
                    'password': password
                }
                print(f"Sending login request: {login_data}")
                
                try:
                    await self.websocket.send(json.dumps(login_data))
                    print("Login request sent")
                except Exception as e:
                    print(f"Error sending login request: {e}")
                    status_label.setText('Error sending login request')
                    return
                
                status_label.setText('Waiting for response...')
                print("Waiting for server response")
                
                try:
                    response = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
                    print(f"Received response: {response}")
                    response_data = json.loads(response)
                except asyncio.TimeoutError:
                    print("Server response timeout")
                    status_label.setText('Server response timeout')
                    return
                except Exception as e:
                    print(f"Error receiving response: {e}")
                    status_label.setText('Error receiving response')
                    return
                
                if response_data['status'] == 'success':
                    print("Login successful")
                    self.username = username
                    self.setWindowTitle(f'Chat Application - {self.username}')
                    
                    self.update_contacts_list(response_data['contacts'])

                    if 'chat_history' in response_data:
                        for chat in response_data['chat_history']:
                            contact = chat['receiver'] if chat['sender'] == self.username else chat['sender']
                            if contact not in self.chat_histories:
                                self.chat_histories[contact] = []
                            
                            self.chat_histories[contact].append({
                                'timestamp': chat['timestamp'],
                                'sender': chat['sender'],
                                'type': chat['message_type'],
                                'content': chat['content']
                            })
                    
                    print("Starting message receiving loop")
                    asyncio.get_event_loop().create_task(self.receive_messages())
                    
                    self.handle_login_success()
                    
                    QMessageBox.information(dialog, 'Success', 'Login successful')
                    dialog.accept()
                else:
                    error_msg = response_data.get('message', 'Login failed')
                    print(f"Login failed: {error_msg}")
                    status_label.setText(error_msg)
                    status_label.setStyleSheet('color: red')
            
            except Exception as e:
                print(f"Unexpected error during login: {e}")
                status_label.setText(f'Error: {str(e)}')
                status_label.setStyleSheet('color: red')
        
        def handle_login():
            print("Login button clicked - creating task")
            asyncio.get_event_loop().create_task(login())

        login_button.clicked.connect(handle_login)

        def handle_return_pressed():
            if username_input.text() and password_input.text():
                handle_login()

        username_input.returnPressed.connect(lambda: password_input.setFocus())
        password_input.returnPressed.connect(handle_return_pressed)

        print("Showing login dialog")
        dialog.exec()
    
    def append_message(self, sender, message_type, content):
        if not self.current_contact:
            return
            
        timestamp = datetime.now().strftime('%H:%M')
        
        if self.current_contact not in self.chat_histories:
            self.chat_histories[self.current_contact] = []
        
        self.chat_histories[self.current_contact].append({
            'timestamp': timestamp,
            'sender': sender,
            'type': message_type,
            'content': content
        })
        
        profile_image = None
        for contact in self._contacts_data:
            if contact['username'] == sender:
                profile_image = contact.get('profile_image')
                break
        
        if message_type == 'text':
            self.chat_history.add_message(
                content,
                timestamp,
                sender == self.username,
                profile_image
            )
        elif message_type == 'image':
            image_data = base64.b64decode(content)
            image = QImage.fromData(image_data)
            if not image.isNull():
                pixmap = QPixmap.fromImage(image)
                if pixmap.width() > 300:
                    pixmap = pixmap.scaledToWidth(300)
                
                image_label = QLabel()
                image_label.setPixmap(pixmap)
                image_label.setStyleSheet("""
                    border-radius: 15px;
                    padding: 5px;
                """)
                
                self.chat_history.add_message(
                    "", 
                    timestamp,
                    sender == self.username,
                    profile_image,
                    image_label
                )

    def display_message(self, message):
        try:
            timestamp = message.get('timestamp', datetime.now().strftime('%H:%M'))
            sender = message.get('sender', 'Unknown')
            msg_type = message.get('type', 'text')
            content = message.get('content', '')
            
            profile_image = None
            for contact in self._contacts_data:
                if contact['username'] == sender:
                    profile_image = contact.get('profile_image')
                    break
            
            if msg_type == 'text':
                self.chat_history.add_message(
                    content,
                    timestamp,
                    sender == self.username,
                    profile_image
                )
            elif msg_type == 'image':
                image_data = base64.b64decode(content)
                image = QImage.fromData(image_data)
                if not image.isNull():
                    pixmap = QPixmap.fromImage(image)
                    if pixmap.width() > 300:
                        pixmap = pixmap.scaledToWidth(300)
                    
                    image_label = QLabel()
                    image_label.setPixmap(pixmap)
                    image_label.setStyleSheet("""
                        border-radius: 15px;
                        padding: 5px;
                    """)
                    
                    self.chat_history.add_message(
                        "",  
                        timestamp,
                        sender == self.username,
                        profile_image,
                        image_label
                    )
                    
        except Exception as e:
            print(f"Error displaying message: {e}")

    def append_chat_message(self, sender, message_type, content, timestamp):
        try:
            if not self.current_contact:
                return
                
            if self.current_contact not in self.chat_histories:
                self.chat_histories[self.current_contact] = []
                
            message = {
                'timestamp': timestamp,
                'sender': sender,
                'type': message_type,
                'content': content
            }
            
            self.chat_histories[self.current_contact].append(message)
            
            QTimer.singleShot(0, lambda: self.display_message(message))
                
        except Exception as e:
            print(f"Error in append_chat_message: {e}")

    async def receive_messages(self):
        while True:
            try:
                message = json.loads(await self.websocket.recv())
                print(f"Received message: {message}") 
                
                if message['type'] == 'message':
                    sender = message['sender']
                    message_type = message['message_type']
                    content = message['content']
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    
                    if sender == self.current_contact:
                        self.append_chat_message(sender, message_type, content, timestamp)
                    
                    if sender not in self.chat_histories:
                        self.chat_histories[sender] = []
                    
                    self.chat_histories[sender].append({
                        'timestamp': timestamp,
                        'sender': sender,
                        'type': message_type,
                        'content': content
                    })
                    
                    if sender != self.current_contact:
                        items = self.contacts_list.findItems(sender, Qt.MatchFlag.MatchExactly)
                        if items:
                            items[0].setForeground(QColor(255, 0, 0))
                            items[0].setText(f"{sender} (New Message!)")
                        
                        try:
                            notification_text = f"Image from {sender}" if message_type == 'image' else f"{sender}: {content}"
                            notification.notify(
                                title='New Message',
                                message=notification_text,
                                app_icon=None,
                                timeout=5
                            )
                        except:
                            print("Failed to show notification")
                
                elif message['type'] == 'profile_update_result':
                    if message['status'] == 'success':
                        QMessageBox.information(self, 'Success', 'Profile updated successfully!')
                    else:
                        QMessageBox.warning(self, 'Error', 'Failed to update profile')
                elif message['type'] == 'status_update':
                    username = message['username']
                    is_online = message['status'] == 'online'
                    
                    if username != self.username:
                        for i in range(self.contacts_list.count()):
                            item = self.contacts_list.item(i)
                            widget = self.contacts_list.itemWidget(item)
                            if widget and widget.get_username() == username:
                                break
                        else: 
                            item = QListWidgetItem()
                            widget = ContactListItem({
                                'username': username,
                                'display_name': username
                            })
                            item.setSizeHint(widget.sizeHint())
                            self.contacts_list.addItem(item)
                            self.contacts_list.setItemWidget(item, widget)
                            print(f"Added new contact: {username}")
                    
                    self.status_updated.emit(username, is_online)
                    
            except Exception as e:
                print(f"Error in receive_messages: {e}")
                break

    def send_message(self):
        if not self.current_contact:
            QMessageBox.warning(self, 'Warning', 'Please select a contact first')
            return
        
        content = self.message_input.toPlainText().strip() 
        if not content:
            return
                
        async def send():
            try:
                formatted_content = content.replace('\n', '<br>')
                
                message_data = {
                    'type': 'message',
                    'message_type': 'text',
                    'sender': self.username,
                    'receiver': self.current_contact,
                    'content': formatted_content
                }
                
                print(f"Sending message: {message_data}")
                await self.websocket.send(json.dumps(message_data))
                
                self.message_input.clear()
                timestamp = datetime.now().strftime('%H:%M')
                self.append_chat_message(self.username, 'text', formatted_content, timestamp)
                
            except Exception as e:
                print(f"Error sending message: {e}")
                QMessageBox.warning(self, 'Error', f'Failed to send message: {str(e)}')
        
        asyncio.get_event_loop().create_task(send())
        self.message_input.setFixedHeight(40)

    def send_image(self):
        if not self.current_contact: 
            QMessageBox.warning(self, 'Warning', 'Please select a contact first')
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )
        
        if file_path:
            with open(file_path, 'rb') as file:
                image_data = base64.b64encode(file.read()).decode('utf-8')
                
                async def send():
                    try:
                        await self.websocket.send(json.dumps({
                            'type': 'message',
                            'message_type': 'image',
                            'sender': self.username,
                            'receiver': self.current_contact,
                            'content': image_data
                        }))
                        
                        timestamp = datetime.now().strftime('%H:%M:%S')
                        self.append_chat_message(self.username, 'image', image_data, timestamp)
                        
                    except Exception as e:
                        QMessageBox.warning(self, 'Error', f'Failed to send image: {str(e)}')
                
                asyncio.get_event_loop().create_task(send())

    def handle_message_received(self, sender, message_type, content):
        contact_name = sender if sender != self.username else self.current_contact
        
        if contact_name not in self.chat_histories:
            self.chat_histories[contact_name] = []
            
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.chat_histories[contact_name].append({
            'timestamp': timestamp,
            'sender': sender,
            'type': message_type,
            'content': content
        })
        
        if sender != self.username and contact_name != self.current_contact:
            if contact_name not in self.unread_messages:
                self.unread_messages[contact_name] = 0
            self.unread_messages[contact_name] += 1
            
            items = self.contacts_list.findItems(contact_name, Qt.MatchFlag.MatchExactly)
            if items:
                items[0].setForeground(QColor(255, 0, 0))
                items[0].setText(f"{contact_name} (New Message!)")
            
            try:
                notification_text = f"Image from {sender}" if message_type == 'image' else f"{sender}: {content}"
                notification.notify(
                    title='New Message',
                    message=notification_text,
                    app_icon=None, 
                    timeout=5 
                )
            except:
                print("Failed to show notification")
        
        if contact_name == self.current_contact:
            self.append_message(sender, message_type, content)
        
    def handle_status_update(self, username, is_online):
        items = self.contacts_list.findItems(username, Qt.MatchFlag.MatchExactly)
        if not items:
            item = QListWidgetItem(username)
            self.contacts_list.addItem(item)
        else:
            item = items[0]
        
        item.setForeground(
            QColor(0, 128, 0) if is_online else QColor(128, 128, 128)
        )


    
    def contact_selected(self, item):
        try:
            contact_widget = self.contacts_list.itemWidget(item)
            if not contact_widget:
                print("No contact widget found")
                return
            
            username = contact_widget.get_username()
            display_name = contact_widget.get_display_name()
            
            print(f"Selected contact: {username} ({display_name})")
            
            self.current_contact = username
            self.chat_history.clear()
            
            self.chat_title.setText(display_name)
            self.chat_title.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
            
            QTimer.singleShot(0, lambda: self.display_chat_history(username))
                    
        except Exception as e:
            print(f"Error in contact_selected: {e}")

    def display_chat_history(self, username):
        try:
            if username in self.chat_histories:
                for message in self.chat_histories[username]:
                    timestamp = message.get('timestamp', datetime.now().strftime('%H:%M'))
                    sender = message.get('sender', 'Unknown')
                    msg_type = message.get('type', 'text')
                    content = message.get('content', '')
                    
                    profile_image = None
                    for contact in self._contacts_data:
                        if contact['username'] == sender:
                            profile_image = contact.get('profile_image')
                            break
                    
                    if msg_type == 'text':
                        self.chat_history.add_message(
                            content,
                            timestamp,
                            sender == self.username,
                            profile_image
                        )
                    elif msg_type == 'image':
                        try:
                            image_data = base64.b64decode(content)
                            image = QImage.fromData(image_data)
                            if not image.isNull():
                                pixmap = QPixmap.fromImage(image)
                                if pixmap.width() > 300:
                                    pixmap = pixmap.scaledToWidth(300)
                                
                                image_label = QLabel()
                                image_label.setPixmap(pixmap)
                                image_label.setStyleSheet("""
                                    border-radius: 15px;
                                    padding: 5px;
                                """)
                                
                                self.chat_history.add_message(
                                    "",
                                    timestamp,
                                    sender == self.username,
                                    profile_image,
                                    image_label
                                )
                        except Exception as e:
                            print(f"Error displaying image: {e}")
                            
        except Exception as e:
            print(f"Error loading chat history: {e}")
        
    def closeEvent(self, event):
        if self.websocket:
            asyncio.get_event_loop().create_task(
                self.websocket.send(json.dumps({
                    'type': 'save_unread',
                    'username': self.username,
                    'unread_messages': self.unread_messages
                }))
            )
        event.accept()

    def handle_profile_update(self, username: str, profile: dict):
        self.profiles[username] = profile
        
        items = self.contacts_list.findItems(username, Qt.MatchFlag.MatchExactly)
        if items:
            item = items[0]
            display_name = profile.get('display_name', username)
            status = profile.get('status_message', '')
            item.setText(f"{display_name}\n{status}" if status else display_name)
            
            if profile.get('profile_picture'):
                pixmap = QPixmap()
                pixmap.loadFromData(base64.b64decode(profile['profile_picture']))
                pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio)
                item.setIcon(QIcon(pixmap))


if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        client = ChatClient()
        client.show()
        
        timer = QTimer()
        timer.setInterval(50)
        
        def process_async_tasks():
            loop.stop()
            loop.run_forever()
        
        timer.timeout.connect(process_async_tasks)
        timer.start()
        
        app.exec()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        loop.close()
        sys.exit()