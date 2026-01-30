from datetime import datetime
from functools import partial
import hashlib
import json
import os
import socket
import sys
import traceback
# ============================================
log_file = 'scale_log.txt'
if os.path.exists(log_file):
    try:
        os.remove(log_file)
    except:
        pass

def log_msg(msg, level='INFO'):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    formatted_msg = f'[{timestamp}] [{level}] {msg}\n'
    print(formatted_msg)
    try:
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(formatted_msg)
    except:
        pass

def get_device_id_s():
    try:
        from kivy.utils import platform
        if platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            content_resolver = PythonActivity.mActivity.getContentResolver()
            Secure = autoclass('android.provider.Settings$Secure')
            android_id = Secure.getString(content_resolver, Secure.ANDROID_ID)
            return str(android_id) if android_id else 'ANDROID_NO_ID'
        else:
            return 'PC_SCALE_DEV_ID'
    except:
        return 'UNKNOWN_ID'

def generate_expected_key_s(device_id):
    salt = f'magpro_scale_mobile_v7_secure_salt_{device_id}'
    return hashlib.sha256(salt.encode()).hexdigest()

try:
    from kivy.config import Config
    Config.set('graphics', 'width', '400')
    Config.set('graphics', 'height', '800')
    Config.set('kivy', 'log_level', 'info')
    from kivy.core.window import Window
    from kivy.lang import Builder
    from kivy.clock import Clock
    from kivy.properties import StringProperty, ObjectProperty, BooleanProperty
    from kivy.network.urlrequest import UrlRequest
    from kivy.storage.jsonstore import JsonStore
    from kivy.utils import platform
    from kivy.core.clipboard import Clipboard
    from kivy.metrics import dp
    from kivy.uix.recycleview import RecycleView
    from kivy.uix.recycleview.views import RecycleDataViewBehavior
    from kivymd.app import MDApp
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.screenmanager import MDScreenManager
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.floatlayout import MDFloatLayout
    from kivymd.uix.card import MDCard
    from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton, MDFillRoundFlatButton
    from kivymd.uix.label import MDLabel, MDIcon
    from kivymd.uix.textfield import MDTextField
    from kivymd.uix.dialog import MDDialog
    from kivymd.uix.list import MDList, OneLineIconListItem, TwoLineIconListItem, IconLeftWidget
    from kivymd.uix.scrollview import MDScrollView
    from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
    from kivy.core.text import LabelBase
    import arabic_reshaper
    from bidi.algorithm import get_display
except Exception as e:
    log_msg(f'Import Error: {traceback.format_exc()}', 'CRITICAL')
    sys.exit(1)

class SmartTextField(MDTextField):

    def __init__(self, **kwargs):
        self._raw_text = ''
        self.base_direction = 'ltr'
        self.halign = 'left'
        self._input_reshaper = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True, 'support_ligatures': False, 'use_unshaped_instead_of_isolated': True})
        super().__init__(**kwargs)
        self.font_name = 'AppFont'
        self.font_name_hint_text = 'AppFont'
        self.keyboard_suggestions = False
        if self.text:
            self._raw_text = self.text
            self._update_display()

    def insert_text(self, substring, from_undo=False):
        self._raw_text += substring
        self._update_display()

    def do_backspace(self, from_undo=False, mode='bkspc'):
        if not self._raw_text:
            self.text = ''
            return
        self._raw_text = self._raw_text[:-1]
        if not self._raw_text:
            self.text = ''
            self._update_alignment(self._raw_text)
            return
        self._update_display()

    def _update_display(self):
        if self._raw_text:
            try:
                reshaped = self._input_reshaper.reshape(self._raw_text)
                bidi_text = get_display(reshaped)
                self.text = bidi_text
            except Exception:
                self.text = self._raw_text
        else:
            self.text = ''
        self._update_alignment(self._raw_text)
        Clock.schedule_once(self._set_cursor_to_end, 0)

    def _set_cursor_to_end(self, dt):
        self.cursor = (len(self.text), 0)

    def _update_alignment(self, text):
        if not text:
            self.halign = 'left'
            self.base_direction = 'ltr'
            return
        has_arabic = any(('\u0600' <= c <= 'ۿ' or 'ݐ' <= c <= 'ݿ' or 'ﭐ' <= c <= 'ﰿ' or ('ﹰ' <= c <= '\ufeff') for c in text))
        if has_arabic:
            self.halign = 'right'
            self.base_direction = 'rtl'
        else:
            self.halign = 'left'
            self.base_direction = 'ltr'

    def get_value(self):
        if not self._raw_text and self.text:
            return self.text
        return self._raw_text

    def on_text(self, instance, value):
        if not value:
            self._raw_text = ''
        pass

# ============================================
KV_BUILDER = '\n<ProductItem>:\n    orientation: \'vertical\'\n    size_hint_y: None\n    height: dp(100)\n    padding: [dp(10), dp(5)]\n    \n    MDCard:\n        orientation: \'horizontal\'\n        radius: [15]\n        elevation: 2\n        ripple_behavior: True\n        on_release: root.on_tap()\n        md_bg_color: 1, 1, 1, 1\n        padding: dp(10)\n        spacing: dp(15)\n\n        MDFloatLayout:\n            size_hint: None, None\n            size: dp(70), dp(70)\n            pos_hint: {\'center_y\': .5}\n            \n            MDCard:\n                radius: [10]\n                md_bg_color: 0.95, 0.95, 0.95, 1\n                size_hint: 1, 1\n                pos_hint: {\'center_x\': .5, \'center_y\': .5}\n                elevation: 0\n\n            FitImage:\n                source: root.image_url\n                radius: [10]\n                mipmap: True\n                pos_hint: {\'center_x\': .5, \'center_y\': .5}\n                opacity: 1 if root.image_url else 0\n                \n            MDIcon:\n                icon: "scale"\n                halign: "center"\n                font_size: "36sp"\n                theme_text_color: "Hint"\n                pos_hint: {\'center_x\': .5, \'center_y\': .5}\n                opacity: 0 if root.image_url else 1\n\n        MDBoxLayout:\n            orientation: \'vertical\'\n            pos_hint: {\'center_y\': .5}\n            adaptive_height: True\n            spacing: dp(5)\n            \n            MDLabel:\n                text: root.text_name\n                font_style: \'Subtitle1\'\n                bold: True\n                theme_text_color: "Custom"\n                text_color: 0.2, 0.2, 0.2, 1\n                font_name: "AppFont"\n                halign: "left"\n                adaptive_height: True\n                text_size: self.width, None\n                max_lines: 2\n                line_height: 1.1\n            \n            MDLabel:\n                text: root.text_price\n                font_style: \'H6\'\n                theme_text_color: "Custom"\n                text_color: 0, 0.7, 0, 1\n                bold: True\n                font_name: "AppFont"\n                halign: "left"\n                adaptive_height: True\n\n<LoginScreen>:\n    name: \'login\'\n    \n    MDFloatLayout:\n        md_bg_color: 0.98, 0.98, 0.98, 1\n        \n        MDBoxLayout:\n            orientation: \'horizontal\'\n            adaptive_size: True\n            pos_hint: {\'top\': 0.98, \'right\': 0.98}\n            spacing: dp(5)\n            padding: dp(10)\n            \n            MDIcon:\n                icon: \'circle\'\n                theme_text_color: "Custom"\n                text_color: (0, 0.8, 0, 1) if app.is_connected else (0.8, 0, 0, 1)\n                font_size: "14sp"\n                pos_hint: {\'center_y\': 0.5}\n                \n            MDIconButton:\n                icon: \'cog\'\n                on_release: app.open_settings_dialog()\n\n        MDBoxLayout:\n            orientation: \'vertical\'\n            size_hint: 0.85, None\n            height: dp(400)\n            pos_hint: {\'center_x\': 0.5, \'center_y\': 0.55}\n            spacing: dp(20)\n            \n            MDIcon:\n                icon: \'scale-balance\'\n                font_size: \'90sp\'\n                halign: \'center\'\n                theme_text_color: "Primary"\n            \n            MDLabel:\n                text: "MagPro Scale"\n                halign: \'center\'\n                font_style: "H4"\n                bold: True\n                font_name: "AppFont"\n                \n            MDLabel:\n                text: "Connexion Système"\n                halign: \'center\'\n                font_style: "Caption"\n                theme_text_color: "Hint"\n                font_name: "AppFont"\n\n            # Using SmartTextField for correct Arabic Input\n            SmartTextField:\n                id: user_field\n                text: "ADMIN"\n                hint_text: "Utilisateur"\n                icon_right: "account"\n                mode: "fill"\n                font_name: "AppFont"\n                radius: [10, 10, 0, 0]\n\n            SmartTextField:\n                id: pass_field\n                hint_text: "Mot de passe"\n                password: True\n                icon_right: "key"\n                mode: "fill"\n                font_name: "AppFont"\n                radius: [0, 0, 10, 10]\n\n            MDRaisedButton:\n                text: "SE CONNECTER"\n                font_size: "18sp"\n                size_hint_x: 1\n                height: dp(55)\n                font_name: "AppFont"\n                md_bg_color: app.theme_cls.primary_color\n                on_release: app.do_login(user_field.get_value(), pass_field.get_value())\n\n<MainScaleScreen>:\n    name: \'scale\'\n    \n    MDBottomNavigation:\n        id: bottom_nav\n        selected_color_background: "blue"\n        text_color_active: 0, 0, 0, 1\n        font_name: "AppFont"\n\n        MDBottomNavigationItem:\n            name: \'screen_products\'\n            text: \'Produits\'\n            icon: \'package-variant\'\n            \n            MDBoxLayout:\n                orientation: \'vertical\'\n                md_bg_color: 0.98, 0.98, 0.98, 1\n                \n                MDBoxLayout:\n                    size_hint_y: None\n                    height: dp(70)\n                    padding: [dp(10), dp(5)]\n                    spacing: dp(10)\n                    md_bg_color: 1, 1, 1, 1\n                    elevation: 1\n                    \n                    MDIconButton:\n                        icon: \'logout\'\n                        theme_text_color: "Error"\n                        on_release: app.logout()\n                        pos_hint: {\'center_y\': 0.5}\n                        \n                    SmartTextField:\n                        id: search_box\n                        hint_text: "Rechercher..."\n                        mode: "rectangle"\n                        icon_right: "magnify"\n                        font_name: "AppFont"\n                        size_hint_y: None\n                        height: dp(45)\n                        pos_hint: {\'center_y\': 0.5}\n                        on_text: app.filter_products(self.get_value())\n                        \n                    MDIcon:\n                        icon: \'circle\'\n                        theme_text_color: "Custom"\n                        text_color: (0, 0.8, 0, 1) if app.is_connected else (0.8, 0, 0, 1)\n                        font_size: "16sp"\n                        pos_hint: {\'center_y\': 0.5}\n\n                RecycleView:\n                    id: rv\n                    viewclass: \'ProductItem\'\n                    bar_width: dp(0)\n                    \n                    RecycleBoxLayout:\n                        default_size: None, dp(100)\n                        default_size_hint: 1, None\n                        size_hint_y: None\n                        height: self.minimum_height\n                        orientation: \'vertical\'\n                        spacing: dp(2)\n                        padding: [0, dp(10), 0, dp(80)]\n\n        MDBottomNavigationItem:\n            name: \'screen_weigh\'\n            text: \'Balance\'\n            icon: \'scale\'\n            \n            MDBoxLayout:\n                orientation: \'vertical\'\n                spacing: dp(10)\n                padding: dp(15)\n                md_bg_color: 0.98, 0.98, 0.98, 1\n                \n                MDCard:\n                    orientation: \'vertical\'\n                    size_hint_y: None\n                    height: dp(140)\n                    padding: dp(15)\n                    radius: [15]\n                    elevation: 1\n                    md_bg_color: 1, 1, 1, 1\n                    \n                    MDLabel:\n                        text: "PRODUIT SÉLECTIONNÉ"\n                        halign: \'center\'\n                        font_style: \'Overline\'\n                        font_name: "AppFont"\n                        theme_text_color: \'Secondary\'\n                        size_hint_y: None\n                        height: dp(20)\n                        \n                    MDLabel:\n                        id: lbl_name\n                        text: "---"\n                        halign: \'center\'\n                        font_style: \'H5\'\n                        bold: True\n                        font_name: "AppFont"\n                        theme_text_color: "Primary"\n                        shorten: True\n                        size_hint_y: 1\n                        \n                    MDBoxLayout:\n                        size_hint_y: None\n                        height: dp(30)\n                        MDLabel:\n                            text: "PRIX / KG:"\n                            font_name: "AppFont"\n                            halign: \'left\'\n                            font_style: \'Body2\'\n                        MDLabel:\n                            id: lbl_price_unit\n                            text: "0.00 DA"\n                            halign: \'right\'\n                            bold: True\n                            theme_text_color: "Custom"\n                            text_color: 0, 0.6, 0, 1\n                            font_size: "18sp"\n\n                MDGridLayout:\n                    cols: 2\n                    spacing: dp(10)\n                    size_hint_y: None\n                    height: dp(80)\n\n                    MDCard:\n                        padding: dp(5)\n                        radius: [10]\n                        md_bg_color: 1, 1, 1, 1\n                        MDTextField:\n                            id: txt_weight\n                            hint_text: "POIDS (g)"\n                            font_size: "26sp"\n                            halign: \'center\'\n                            input_filter: \'int\'\n                            mode: "line"\n                            line_color_normal: 0,0,0,0\n                            line_color_focus: 0,0,0,0\n                            readonly: True\n                            font_name: "AppFont"\n\n                    MDCard:\n                        padding: dp(10)\n                        radius: [10]\n                        md_bg_color: 0.1, 0.1, 0.1, 1\n                        MDBoxLayout:\n                            orientation: \'vertical\'\n                            MDLabel:\n                                text: "TOTAL"\n                                color: 1, 1, 1, 0.7\n                                font_style: \'Caption\'\n                                halign: \'center\'\n                            MDLabel:\n                                id: lbl_total\n                                text: "0.00"\n                                halign: \'center\'\n                                color: 0, 1, 0, 1\n                                font_style: \'H5\'\n                                bold: True\n\n                MDGridLayout:\n                    cols: 3\n                    spacing: dp(8)\n                    size_hint_y: 1\n                    \n                    MDRaisedButton:\n                        text: "7"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("7")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                    MDRaisedButton:\n                        text: "8"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("8")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                    MDRaisedButton:\n                        text: "9"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("9")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                        \n                    MDRaisedButton:\n                        text: "4"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("4")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                    MDRaisedButton:\n                        text: "5"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("5")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                    MDRaisedButton:\n                        text: "6"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("6")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                        \n                    MDRaisedButton:\n                        text: "1"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("1")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                    MDRaisedButton:\n                        text: "2"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("2")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                    MDRaisedButton:\n                        text: "3"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("3")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                        \n                    MDRaisedButton:\n                        text: "C"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        md_bg_color: 0.9, 0.9, 0.9, 1\n                        text_color: 0.8, 0, 0, 1\n                        on_release: app.clear_weight()\n                        elevation: 1\n                    MDRaisedButton:\n                        text: "0"\n                        font_size: "24sp"\n                        size_hint: 1, 1\n                        on_release: app.add_digit("0")\n                        md_bg_color: 1, 1, 1, 1\n                        text_color: 0, 0, 0, 1\n                        elevation: 1\n                    MDIconButton:\n                        icon: "backspace"\n                        size_hint: 1, 1\n                        icon_size: "30sp"\n                        on_release: app.backspace()\n                        theme_text_color: "Custom"\n                        text_color: 0.3, 0.3, 0.3, 1\n\n                MDFillRoundFlatButton:\n                    text: "IMPRIMER"\n                    font_name: "AppFont"\n                    font_size: "20sp"\n                    size_hint_x: 1\n                    height: dp(55)\n                    md_bg_color: 0, 0.7, 0, 1\n                    on_release: app.send_print_command()\n'
# ============================================
class ProductItem(RecycleDataViewBehavior, MDBoxLayout):
    index = None
    text_name = StringProperty('')
    text_price = StringProperty('')
    image_url = StringProperty('')
    product_data = ObjectProperty(None)

    def refresh_view_attrs(self, rv, index, data):
        self.index = index
        self.text_name = data.get('text_name', '')
        self.text_price = data.get('text_price', '')
        self.image_url = data.get('image_url', '')
        self.product_data = data.get('product_data')
        return super().refresh_view_attrs(rv, index, data)

    def on_tap(self):
        MDApp.get_running_app().select_product(self.product_data)

class LoginScreen(MDScreen):
    pass

class MainScaleScreen(MDScreen):
    pass

class ScaleApp(MDApp):
    is_connected = BooleanProperty(False)
    selected_product = None
    all_products = []
    dialog = None
    dialog_loading = None
    dialog_exit = None
    wifi_ip = '192.168.1.100'
    ethernet_ip = ''
    server_port = '5000'
    sticker_size = '40x20'
    available_ips = []
    current_ip_index = 0
    license_store = None
    cache_store = None
    activation_dialog_ref = None
    heartbeat_event = None

    def build(self):
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.accent_palette = 'Amber'
        self.theme_cls.theme_style = 'Light'
        self.title = 'MagPro Scale'
        try:
            self.data_dir = self.user_data_dir
            if not os.path.exists(self.data_dir):
                os.makedirs(self.data_dir)
            self.image_cache_dir = os.path.join(self.data_dir, 'img_cache')
            if not os.path.exists(self.image_cache_dir):
                os.makedirs(self.image_cache_dir)
        except Exception as e:
            log_msg(f'FS Error: {e}', 'ERROR')
        global KV_BUILDER
        font_path = 'font.ttf'
        if os.path.exists(font_path):
            try:
                LabelBase.register(name='AppFont', fn_regular=font_path, fn_bold=font_path)
            except Exception as e:
                log_msg(f'Error registering font: {e}', 'ERROR')
                KV_BUILDER = KV_BUILDER.replace('font_name: "AppFont"', '')
        else:
            log_msg('font.ttf not found. Using system defaults.', 'WARNING')
            KV_BUILDER = KV_BUILDER.replace('font_name: "AppFont"', '')
        try:
            self.reshaper = arabic_reshaper.ArabicReshaper(configuration={'delete_harakat': True, 'support_ligatures': True})
        except:
            pass
        self.load_settings()
        Builder.load_string(KV_BUILDER)
        self.sm = MDScreenManager()
        self.sm.add_widget(LoginScreen())
        self.sm.add_widget(MainScaleScreen())
        return self.sm

    def load_settings(self):
        try:
            self.store = JsonStore(os.path.join(self.data_dir, 'scale_settings.json'))
            self.license_store = JsonStore(os.path.join(self.data_dir, 'scale_license.json'))
            self.cache_store = JsonStore(os.path.join(self.data_dir, 'products_cache.json'))
            if self.store.exists('config'):
                config = self.store.get('config')
                self.wifi_ip = config.get('wifi_ip', self.wifi_ip)
                self.ethernet_ip = config.get('eth_ip', self.ethernet_ip)
                self.sticker_size = config.get('sticker_size', self.sticker_size)
            self.available_ips = []
            if self.wifi_ip and self.is_valid_ip(self.wifi_ip):
                self.available_ips.append(self.wifi_ip)
            if self.ethernet_ip and self.is_valid_ip(self.ethernet_ip):
                self.available_ips.append(self.ethernet_ip)
            if not self.available_ips:
                self.available_ips = ['192.168.1.100']
        except:
            pass

    def is_valid_ip(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except:
            return False

    def on_start(self):
        if platform == 'android':
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PythonActivity.mActivity.getWindow().addFlags(128)
        Window.bind(on_keyboard=self.on_keyboard_handler)
        if not self.check_license():
            Clock.schedule_once(lambda dt: self.show_activation_dialog(), 0.5)
            return
        self.start_heartbeat()
        if self.sm.has_screen('login'):
            login_screen = self.sm.get_screen('login')
            if self.store.exists('credentials'):
                creds = self.store.get('credentials')
                user = creds.get('username', 'ADMIN')
                pwd = creds.get('password', '')
                login_screen.ids.user_field.text = user
                login_screen.ids.pass_field.text = pwd
                if user:
                    Clock.schedule_once(lambda dt: self.do_login(user, pwd), 1)
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE])

    def on_keyboard_handler(self, window, key, *args):
        if key == 27:
            if self.dialog and self.dialog._is_open:
                self.dialog.dismiss()
                return True
            if self.dialog_loading and self.dialog_loading._is_open:
                return True
            if self.activation_dialog_ref and self.activation_dialog_ref._is_open:
                return True
            if self.sm.current == 'scale':
                self.show_exit_confirmation()
                return True
            elif self.sm.current == 'login':
                self.show_exit_confirmation()
                return True
            return True
        return False

    def show_exit_confirmation(self):
        if self.dialog_exit:
            self.dialog_exit.dismiss()
        self.dialog_exit = MDDialog(title='Quitter ?', text="Voulez-vous fermer l'application ?", buttons=[MDFlatButton(text='NON', on_release=lambda x: self.dialog_exit.dismiss()), MDRaisedButton(text='OUI', md_bg_color=(0.8, 0, 0, 1), on_release=lambda x: sys.exit(0))])
        self.dialog_exit.open()

    def start_heartbeat(self):
        if not self.heartbeat_event:
            self.heartbeat_event = Clock.schedule_interval(self.check_connection_status, 5)

    def check_connection_status(self, dt):
        if not self.available_ips:
            self.is_connected = False
            return
        ip = self.available_ips[self.current_ip_index]
        url = f'http://{ip}:{self.server_port}/api/products'
        UrlRequest(url, method='HEAD', on_success=lambda r, res: setattr(self, 'is_connected', True), on_failure=lambda r, e: setattr(self, 'is_connected', False), on_error=lambda r, e: setattr(self, 'is_connected', False), timeout=1.5)

    def check_license(self):
        if not self.license_store.exists('license'):
            return False
        data = self.license_store.get('license')
        stored_key = data.get('activ_key')
        if not stored_key:
            return False
        dev_id = get_device_id_s()
        expected = generate_expected_key_s(dev_id)
        return stored_key == expected

    def show_activation_dialog(self):
        dev_id = get_device_id_s()
        content = MDBoxLayout(orientation='vertical', spacing='12dp', size_hint_y=None, adaptive_height=True, padding=['20dp', '20dp', '20dp', '10dp'])
        content.add_widget(MDIcon(icon='shield-lock', halign='center', font_size='64sp', theme_text_color='Custom', text_color=self.theme_cls.primary_color, pos_hint={'center_x': 0.5}))
        content.add_widget(MDLabel(text='Activation Requise', halign='center', font_style='H5', bold=True, theme_text_color='Primary', adaptive_height=True))
        id_card = MDCard(orientation='vertical', radius=[10], padding=['15dp', '12dp', '15dp', '12dp'], md_bg_color=(0.96, 0.96, 0.96, 1), elevation=0, size_hint_y=None, adaptive_height=True, spacing='5dp')
        id_card.add_widget(MDLabel(text='ID Appareil :', halign='left', font_style='Caption', theme_text_color='Secondary', adaptive_height=True))
        id_row = MDBoxLayout(orientation='horizontal', spacing='10dp', adaptive_height=True)
        self.field_id = MDTextField(text=dev_id, readonly=True, font_size='16sp', mode='line', active_line=False, size_hint_x=0.85, pos_hint={'center_y': 0.5})
        btn_copy = MDIconButton(icon='content-copy', theme_text_color='Custom', text_color=self.theme_cls.primary_color, on_release=lambda x: Clipboard.copy(dev_id), pos_hint={'center_y': 0.5}, icon_size='22sp')
        id_row.add_widget(self.field_id)
        id_row.add_widget(btn_copy)
        id_card.add_widget(id_row)
        content.add_widget(id_card)
        key_row = MDBoxLayout(orientation='horizontal', spacing='10dp', adaptive_height=True)
        self.field_key = MDTextField(hint_text='Saisir la clé de licence', mode='rectangle', size_hint_x=0.85, pos_hint={'center_y': 0.5})
        btn_paste = MDIconButton(icon='content-paste', theme_text_color='Custom', text_color=self.theme_cls.primary_color, on_release=lambda x: setattr(self.field_key, 'text', Clipboard.paste()), pos_hint={'center_y': 0.5}, icon_size='22sp')
        key_row.add_widget(self.field_key)
        key_row.add_widget(btn_paste)
        content.add_widget(key_row)
        btn_activate = MDRaisedButton(text='ACTIVER', md_bg_color=(0, 0.7, 0, 1), font_size='16sp', elevation=1, size_hint_x=1, size_hint_y=None, height='52dp', on_release=lambda x: self.validate_activation(self.field_key.text))
        content.add_widget(btn_activate)
        self.activation_dialog_ref = MDDialog(title='', type='custom', content_cls=content, size_hint=(0.9, None), auto_dismiss=False, radius=[16, 16, 16, 16])
        self.activation_dialog_ref.open()

    def validate_activation(self, input_key):
        dev_id = get_device_id_s()
        expected = generate_expected_key_s(dev_id)
        if input_key.strip() == expected:
            self.license_store.put('license', activ_key=expected)
            self.show_alert('Succès', 'Application activée !')
            if self.activation_dialog_ref:
                self.activation_dialog_ref.dismiss()
            self.on_start()
        else:
            self.show_alert('Erreur', 'Clé invalide !')

    def fix_text(self, text):
        if not text or not isinstance(text, str):
            return str(text) if text is not None else ''
        if any(('\u0600' <= c <= 'ۿ' for c in text)):
            try:
                reshaped_text = self.reshaper.reshape(text)
                return get_display(reshaped_text)
            except Exception:
                return text
        return text

    def get_active_url(self, endpoint):
        if not self.available_ips:
            return None
        ip = self.available_ips[self.current_ip_index]
        return f'http://{ip}:{self.server_port}{endpoint}'

    def switch_ip_and_retry(self, endpoint, method, body, headers, success_callback, failure_callback, original_req=None):
        self.current_ip_index += 1
        if self.current_ip_index >= len(self.available_ips):
            self.current_ip_index = 0
            self.is_connected = False
            if failure_callback:
                failure_callback(original_req, 'Connexion perdue')
            return
        new_ip = self.available_ips[self.current_ip_index]
        url = f'http://{new_ip}:{self.server_port}{endpoint}'
        UrlRequest(url, req_body=body, req_headers=headers, method=method, on_success=lambda r, res: self._wrap_success(r, res, success_callback), on_error=lambda r, err: self.switch_ip_and_retry(endpoint, method, body, headers, success_callback, failure_callback, r), on_failure=lambda r, err: self.switch_ip_and_retry(endpoint, method, body, headers, success_callback, failure_callback, r), timeout=2)

    def send_request(self, endpoint, method='GET', body=None, headers=None, on_success=None, on_failure=None):
        if headers is None:
            headers = {'Content-type': 'application/json'}
        url = self.get_active_url(endpoint)
        if not url:
            if on_failure:
                on_failure(None, 'Aucune IP configurée')
            return
        UrlRequest(url, req_body=body, req_headers=headers, method=method, on_success=lambda r, res: self._wrap_success(r, res, on_success), on_error=lambda r, err: self.switch_ip_and_retry(endpoint, method, body, headers, on_success, on_failure, r), on_failure=lambda r, err: self.switch_ip_and_retry(endpoint, method, body, headers, on_success, on_failure, r), timeout=2)

    def _wrap_success(self, req, res, original_callback):
        self.is_connected = True
        if original_callback:
            original_callback(req, res)

    def open_settings_dialog(self):
        content_box = MDBoxLayout(orientation='vertical', size_hint_y=None, height=dp(400))
        scroll = MDScrollView()
        list_layout = MDList()
        header_net = OneLineIconListItem(text='Configuration Réseau', bg_color=(0.95, 0.95, 0.95, 1))
        header_net.add_widget(IconLeftWidget(icon='lan'))
        list_layout.add_widget(header_net)
        self.tf_wifi = MDTextField(text=self.wifi_ip, hint_text='IP WIFI', mode='rectangle')
        item_wifi = MDBoxLayout(padding=dp(20), size_hint_y=None, height=dp(80))
        item_wifi.add_widget(self.tf_wifi)
        list_layout.add_widget(item_wifi)
        self.tf_eth = MDTextField(text=self.ethernet_ip, hint_text='IP ETHERNET', mode='rectangle')
        item_eth = MDBoxLayout(padding=dp(20), size_hint_y=None, height=dp(80))
        item_eth.add_widget(self.tf_eth)
        list_layout.add_widget(item_eth)
        header_print = OneLineIconListItem(text='Configuration Étiquette', bg_color=(0.95, 0.95, 0.95, 1))
        header_print.add_widget(IconLeftWidget(icon='printer-settings'))
        list_layout.add_widget(header_print)
        size_box = MDBoxLayout(orientation='horizontal', spacing=dp(10), padding=dp(20), size_hint_y=None, height=dp(60), pos_hint={'center_x': 0.5})

        def set_size(inst):
            self.sticker_size = inst.text
            self.show_alert('Info', f'Taille définie: {self.sticker_size}')
            self.dialog.dismiss()
            self.open_settings_dialog()
        current_size = self.sticker_size
        for s in ['40x20', '45x35', '60x40']:
            if s == current_size:
                btn = MDRaisedButton(text=s, md_bg_color=(0, 0.7, 0, 1), elevation=2)
            else:
                btn = MDRaisedButton(text=s, md_bg_color=(0.8, 0.8, 0.8, 1), text_color=(0, 0, 0, 1), elevation=0)
            btn.bind(on_release=set_size)
            size_box.add_widget(btn)
        list_layout.add_widget(size_box)
        scroll.add_widget(list_layout)
        content_box.add_widget(scroll)

        def save(x):
            self.wifi_ip = self.tf_wifi.text.strip()
            self.ethernet_ip = self.tf_eth.text.strip()
            self.available_ips = []
            if self.wifi_ip and self.is_valid_ip(self.wifi_ip):
                self.available_ips.append(self.wifi_ip)
            if self.ethernet_ip and self.is_valid_ip(self.ethernet_ip):
                self.available_ips.append(self.ethernet_ip)
            self.current_ip_index = 0
            self.store.put('config', wifi_ip=self.wifi_ip, eth_ip=self.ethernet_ip, sticker_size=self.sticker_size)
            if self.dialog:
                self.dialog.dismiss()
            self.show_alert('Succès', 'Paramètres enregistrés')
        self.dialog = MDDialog(title='Paramètres', type='custom', content_cls=content_box, buttons=[MDFlatButton(text='ANNULER', on_release=lambda x: self.dialog.dismiss()), MDRaisedButton(text='SAUVEGARDER', md_bg_color=(0, 0.7, 0, 1), on_release=save)], size_hint=(0.9, 0.8))
        self.dialog.open()

    def do_login(self, username, password):
        if not username:
            self.show_alert('Erreur', 'Nom utilisateur requis')
            return
        body = json.dumps({'username': username, 'password': password})
        self.dialog_loading = MDDialog(text='Connexion en cours...', auto_dismiss=False)
        self.dialog_loading.open()
        self.send_request('/api/login', 'POST', body, on_success=self.on_login_success, on_failure=self.on_login_fail)

    def on_login_success(self, req, res):
        if self.dialog_loading:
            self.dialog_loading.dismiss()
        if res.get('status') == 'success':
            self.store.put('credentials', username=self.root.get_screen('login').ids.user_field.get_value(), password=self.root.get_screen('login').ids.pass_field.get_value())
            self.root.current = 'scale'
            self.fetch_products()
        else:
            self.show_alert('Échec', 'Identifiants incorrects')

    def on_login_fail(self, req, err):
        if self.dialog_loading:
            self.dialog_loading.dismiss()
        self.show_alert('Erreur', 'Serveur inaccessible')

    def logout(self):
        self.root.current = 'login'
        self.selected_product = None

    def fetch_products(self):
        self.send_request('/api/products', 'GET', on_success=self.on_products_loaded, on_failure=self.on_products_fail)

    def on_products_fail(self, req, err):
        log_msg(f'Products Fail: {err}', 'ERROR')
        if self.cache_store.exists('products_data'):
            cached = self.cache_store.get('products_data').get('items', [])
            if cached:
                self.show_alert('Mode Hors Ligne', 'Chargement depuis le cache local.')
                self.on_products_loaded(None, cached)
                return
        self.show_alert('Erreur', f'Échec du chargement:\n{err}')

    def get_cached_image_url(self, image_path_from_server):
        if not image_path_from_server:
            return ''
        try:
            filename = os.path.basename(image_path_from_server.replace('\\', '/'))
            local_path = os.path.join(self.image_cache_dir, filename)
            if os.path.exists(local_path):
                return local_path
            if not self.available_ips:
                return ''
            ip = self.available_ips[self.current_ip_index]
            img_url = f'http://{ip}:{self.server_port}/api/images/{filename}'
            UrlRequest(img_url, on_success=lambda r, res: open(local_path, 'wb').write(res))
            return img_url
        except:
            return ''

    def on_products_loaded(self, req, res):
        if res and isinstance(res, list):
            self.cache_store.put('products_data', items=res)
        self.all_products = []
        valid_units = ['kg', 'g', 'gramme', 'kilogramme', 'كغ', 'غرام', 'kilo', 'لتر', 'l', 'litre']
        server_image_filenames = set()
        for p in res:
            try:
                price = float(str(p.get('price', 0)).replace(',', '.'))
            except:
                price = 0.0
            if price <= 0:
                continue
            unit = str(p.get('unit', '')).lower().strip()
            if not any((u in unit for u in valid_units)):
                continue
            img_path = p.get('image', '')
            if img_path:
                filename = os.path.basename(img_path.replace('\\', '/'))
                server_image_filenames.add(filename)
            self.all_products.append({'id': p['id'], 'name': p['name'], 'price': price, 'image': img_path, 'ref': str(p.get('ref', ''))})
        if os.path.exists(self.image_cache_dir):
            try:
                cached_files = os.listdir(self.image_cache_dir)
                for f in cached_files:
                    if f not in server_image_filenames:
                        try:
                            full_path = os.path.join(self.image_cache_dir, f)
                            os.remove(full_path)
                        except:
                            pass
            except Exception as e:
                pass
        self.update_rv(self.all_products)
        if not self.all_products:
            self.show_alert('Info', 'Aucun produit pesable trouvé (kg, g...).')

    def update_rv(self, products):
        data = []
        for p in products:
            img_src = self.get_cached_image_url(p['image'])
            data.append({'text_name': self.fix_text(p['name']), 'text_price': f"{p['price']:.2f} DA", 'image_url': img_src, 'product_data': p})
        self.root.get_screen('scale').ids.rv.data = data
        self.root.get_screen('scale').ids.rv.refresh_from_data()

    def filter_products(self, text):
        if not text:
            self.update_rv(self.all_products)
            return
        q = text.lower()
        filtered = [p for p in self.all_products if q in p['name'].lower()]
        self.update_rv(filtered)

    def select_product(self, product):
        self.selected_product = product
        screen = self.root.get_screen('scale')
        screen.ids.bottom_nav.switch_tab('screen_weigh')
        screen.ids.lbl_name.text = self.fix_text(product['name'])
        screen.ids.lbl_price_unit.text = f"{product['price']:.2f} DA"
        self.clear_weight()

    def add_digit(self, digit):
        if not self.selected_product:
            return
        screen = self.root.get_screen('scale')
        curr = screen.ids.txt_weight.text
        if len(curr) >= 5:
            return
        screen.ids.txt_weight.text = curr + digit
        self.calculate_total()

    def backspace(self):
        screen = self.root.get_screen('scale')
        curr = screen.ids.txt_weight.text
        if curr:
            screen.ids.txt_weight.text = curr[:-1]
            self.calculate_total()

    def clear_weight(self):
        self.root.get_screen('scale').ids.txt_weight.text = ''
        self.calculate_total()

    def calculate_total(self):
        screen = self.root.get_screen('scale')
        w_str = screen.ids.txt_weight.text
        try:
            if not w_str:
                screen.ids.lbl_total.text = '0.00 DA'
                return
            weight = float(w_str)
            price = self.selected_product['price']
            total = weight / 1000.0 * price
            from decimal import Decimal, ROUND_HALF_UP
            d_total = Decimal(str(total)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            screen.ids.lbl_total.text = f'{d_total} DA'
        except:
            screen.ids.lbl_total.text = '0.00 DA'

    def send_print_command(self):
        if not self.selected_product:
            self.show_alert('Attention', 'Veuillez sélectionner un produit')
            return
        w_str = self.root.get_screen('scale').ids.txt_weight.text
        if not w_str:
            self.show_alert('Attention', 'Veuillez saisir le poids')
            return
        try:
            w_mm, h_mm = map(int, self.sticker_size.split('x'))
        except:
            w_mm, h_mm = (40, 20)
        data = json.dumps({'product_id': self.selected_product['id'], 'weight': int(w_str), 'width_mm': w_mm, 'height_mm': h_mm})
        self.dialog_loading = MDDialog(text='Impression en cours...', auto_dismiss=False)
        self.dialog_loading.open()
        self.send_request('/api/print_scale_label', 'POST', data, on_success=self.on_print_success, on_failure=self.on_print_fail)

    def on_print_success(self, req, res):
        if self.dialog_loading:
            self.dialog_loading.dismiss()
        self.show_alert('Succès', 'Commande envoyée')
        self.clear_weight()

    def on_print_fail(self, req, err):
        if self.dialog_loading:
            self.dialog_loading.dismiss()
        self.show_alert('Erreur', "Vérifiez l'imprimante ou la connexion")

    def show_alert(self, title, text):
        if self.dialog:
            self.dialog.dismiss()
        self.dialog = MDDialog(title=title, text=text, buttons=[MDFlatButton(text='OK', on_release=lambda x: self.dialog.dismiss())])
        self.dialog.open()

if __name__ == '__main__':
    try:
        ScaleApp().run()
    except Exception as e:
        log_msg(f'MAIN ERROR: {traceback.format_exc()}', 'CRITICAL')
