import sys
import os
import json
import requests
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QAction, QTabWidget, 
    QVBoxLayout, QWidget, QLabel, QStatusBar, QMenu, QMenuBar, QFileDialog, 
    QInputDialog, QColorDialog, QDialog, QFormLayout, QPushButton, QTreeWidget, 
    QTreeWidgetItem, QMessageBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings, QWebEnginePage, QWebEngineProfile
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtGui import QColor

class BrowserTab(QWebEngineView):
    def __init__(self, parent=None, incognito=False):
        super(BrowserTab, self).__init__(parent)
        self.incognito = incognito
        self.setSettings()

    def setSettings(self):
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, not self.incognito)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setAttribute(QWebEngineSettings.Accelerated2dCanvasEnabled, True)
        settings.setAttribute(QWebEngineSettings.AutoLoadImages, True)
        settings.setAttribute(QWebEngineSettings.ErrorPageEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        if self.incognito:
            profile = QWebEngineProfile()
            profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
            self.setPage(QWebEnginePage(profile, self))
        else:
            self.setPage(QWebEnginePage(QWebEngineProfile.defaultProfile(), self))

class SimpleBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.history = []   
        self.bookmarks = [] 
        self.downloads = [] 

        self.browser_tabs = QTabWidget()
        self.browser_tabs.setDocumentMode(True)
        self.browser_tabs.currentChanged.connect(self.update_url)
        self.browser_tabs.setTabsClosable(True)
        self.browser_tabs.tabCloseRequested.connect(self.close_current_tab)
        
        self.setCentralWidget(self.browser_tabs)
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        nav_bar = QToolBar("Navigation")
        self.addToolBar(nav_bar)

        back_btn = QAction(QIcon('icons/back.png'), 'Back', self)
        back_btn.triggered.connect(lambda: self.browser_tabs.currentWidget().back())
        nav_bar.addAction(back_btn)

        forward_btn = QAction(QIcon('icons/forward.png'), 'Forward', self)
        forward_btn.triggered.connect(lambda: self.browser_tabs.currentWidget().forward())
        nav_bar.addAction(forward_btn)

        reload_btn = QAction(QIcon('icons/reload.png'), 'Reload', self)
        reload_btn.triggered.connect(lambda: self.browser_tabs.currentWidget().reload())
        nav_bar.addAction(reload_btn)

        home_btn = QAction(QIcon('icons/home.png'), 'Home', self)
        home_btn.triggered.connect(self.navigate_home)
        nav_bar.addAction(home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)

        self.url_bar.setStyleSheet('''
            QLineEdit {
                padding: 5px;
                border: 2px solid #ccc;
                border-radius: 5px;
                min-width: 200px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50; 
            }
        ''')

        self.url_bar.mousePressEvent = lambda event: self.url_bar.selectAll()

        nav_bar.addWidget(self.url_bar)

        stop_btn = QAction(QIcon('icons/stop.png'), 'Stop', self)
        stop_btn.triggered.connect(lambda: self.browser_tabs.currentWidget().stop())
        nav_bar.addAction(stop_btn)

        new_tab_btn = QAction(QIcon('icons/new_tab.png'), 'New Tab', self)
        new_tab_btn.triggered.connect(lambda _: self.add_new_tab())
        nav_bar.addAction(new_tab_btn)

        save_page_btn = QAction(QIcon('icons/save.png'), 'Save Page As...', self)
        save_page_btn.triggered.connect(self.save_page)
        nav_bar.addAction(save_page_btn)
        
        find_text_btn = QAction(QIcon('icons/find.png'), 'Find...', self)
        find_text_btn.triggered.connect(self.find_text)
        nav_bar.addAction(find_text_btn)

        developer_tools_btn = QAction(QIcon('icons/developer_tools.png'), 'Developer Tools', self)
        developer_tools_btn.triggered.connect(self.toggle_developer_tools)
        nav_bar.addAction(developer_tools_btn)

        adblock_btn = QAction(QIcon('icons/adblock.png'), 'Toggle Adblock', self)
        adblock_btn.triggered.connect(self.toggle_adblock)
        nav_bar.addAction(adblock_btn)

        dark_mode_btn = QAction(QIcon('icons/dark_mode.png'), 'Toggle Dark Mode', self)
        dark_mode_btn.triggered.connect(self.toggle_dark_mode)
        nav_bar.addAction(dark_mode_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.status.addPermanentWidget(self.progress_bar)
        
        self.add_new_tab(QUrl("http://www.google.com"), "Homepage")
        
        menubar = self.menuBar()
        
        file_menu = QMenu("File", self)
        new_tab_action = QAction("New Tab", self)
        new_tab_action.triggered.connect(self.add_new_tab)
        file_menu.addAction(new_tab_action)
        
        new_incognito_tab_action = QAction("New Incognito Tab", self)
        new_incognito_tab_action.triggered.connect(lambda: self.add_new_tab(incognito=True))
        file_menu.addAction(new_incognito_tab_action)
        
        save_page_action = QAction("Save Page As...", self)
        save_page_action.triggered.connect(self.save_page)
        file_menu.addAction(save_page_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        menubar.addMenu(file_menu)
        
        edit_menu = QMenu("Edit", self)
        find_action = QAction("Find...", self)
        find_action.triggered.connect(self.find_text)
        edit_menu.addAction(find_action)
        
        menubar.addMenu(edit_menu)
        
        view_menu = QMenu("View", self)
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        full_screen_action = QAction("Full Screen", self)
        full_screen_action.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(full_screen_action)
        
        menubar.addMenu(view_menu)
        
        history_menu = QMenu("History", self)
        view_history_action = QAction("View History", self)
        view_history_action.triggered.connect(self.view_history)
        history_menu.addAction(view_history_action)
        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self.clear_history)
        history_menu.addAction(clear_history_action)
        menubar.addMenu(history_menu)
        
        bookmarks_menu = QMenu("Bookmarks", self)
        view_bookmarks_action = QAction("View Bookmarks", self)
        view_bookmarks_action.triggered.connect(self.view_bookmarks)
        bookmarks_menu.addAction(view_bookmarks_action)
        add_bookmark_action = QAction("Add Bookmark", self)
        add_bookmark_action.triggered.connect(self.add_bookmark)
        bookmarks_menu.addAction(add_bookmark_action)
        menubar.addMenu(bookmarks_menu)
        
        downloads_menu = QMenu("Downloads", self)
        view_downloads_action = QAction("View Downloads", self)
        view_downloads_action.triggered.connect(self.view_downloads)
        downloads_menu.addAction(view_downloads_action)
        menubar.addMenu(downloads_menu)
        
        settings_menu = QMenu("Settings", self)
        preferences_action = QAction("Preferences", self)
        preferences_action.triggered.connect(self.open_preferences)
        settings_menu.addAction(preferences_action)
        menubar.addMenu(settings_menu)
        
        help_menu = QMenu("Help", self)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        menubar.addMenu(help_menu)

        self.showMaximized()

    def add_new_tab(self, qurl=None, label="Blank", incognito=False):
        if qurl is None:
            qurl = QUrl("http://www.google.com")
        elif isinstance(qurl, str):
            qurl = QUrl.fromUserInput(qurl)
        
        browser_tab = BrowserTab(incognito=incognito)
        browser_tab.setUrl(qurl)  
        i = self.browser_tabs.addTab(browser_tab, label)
        self.browser_tabs.setCurrentIndex(i)
        
        browser_tab.urlChanged.connect(lambda qurl, browser_tab=browser_tab: self.update_url_bar(qurl, browser_tab))
        browser_tab.loadFinished.connect(lambda _, i=i, browser_tab=browser_tab: self.browser_tabs.setTabText(i, browser_tab.page().title()))

        browser_tab.loadProgress.connect(self.progress_bar.setValue)
        browser_tab.loadStarted.connect(lambda: self.progress_bar.setVisible(True))
        browser_tab.loadFinished.connect(lambda: self.progress_bar.setVisible(False))
        
        if not incognito:
            self.history.append(qurl.toString())

    def close_current_tab(self, i):
        if self.browser_tabs.count() < 2:
            return
        self.browser_tabs.removeTab(i)
        
    def update_url(self, i):
        qurl = self.browser_tabs.currentWidget().url()
        self.update_url_bar(qurl, self.browser_tabs.currentWidget())
        self.update_title(self.browser_tabs.currentWidget())
        
    def navigate_home(self):
        self.browser_tabs.currentWidget().setUrl(QUrl("http://www.google.com"))
        
    def navigate_to_url(self):
        q = QUrl(self.url_bar.text())
        if q.scheme() == "":
            q.setScheme("http")
        self.browser_tabs.currentWidget().setUrl(q)
        
    def update_url_bar(self, qurl, browser_tab=None):
        if browser_tab != self.browser_tabs.currentWidget():
            return
        self.url_bar.setText(qurl.toString())
        self.url_bar.setCursorPosition(0)
        
    def update_title(self, browser_tab=None):
        if browser_tab != self.browser_tabs.currentWidget():
            return
        title = self.browser_tabs.currentWidget().page().title()
        self.setWindowTitle(f"{title} Apex Browser")
        
    def save_page(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getSaveFileName(self, "Save Page As...", "", "HTML Files (*.html);;All Files (*)", options=options)
        if filename:
            self.browser_tabs.currentWidget().page().save(filename)
            
    def find_text(self):
        text, ok = QInputDialog.getText(self, "Find Text", "Enter the text to find:")
        if ok and text:
            self.browser_tabs.currentWidget().findText(text)
    
    def zoom_in(self):
        current_tab = self.browser_tabs.currentWidget()
        current_tab.setZoomFactor(current_tab.zoomFactor() + 0.1)
    
    def zoom_out(self):
        current_tab = self.browser_tabs.currentWidget()
        current_tab.setZoomFactor(current_tab.zoomFactor() - 0.1)
    
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    def toggle_developer_tools(self):
        current_page = self.browser_tabs.currentWidget().page()
        if not hasattr(self, 'dev_tools'):
            self.dev_tools = QWebEngineView()
            current_page.setDevToolsPage(self.dev_tools.page())
        if self.dev_tools.isVisible():
            self.dev_tools.hide()
        else:
            self.dev_tools.show()
    
    def toggle_adblock(self):
        pass
    
    def toggle_dark_mode(self):
        palette = self.palette()
        if palette.color(palette.Window) == QColor(255, 255, 255):
            palette.setColor(palette.Window, QColor(53, 53, 53))
            palette.setColor(palette.WindowText, QColor(255, 255, 255))
        else:
            palette.setColor(palette.Window, QColor(255, 255, 255))
            palette.setColor(palette.WindowText, QColor(0, 0, 0))
        self.setPalette(palette)
        
    def view_history(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("History")
        layout = QVBoxLayout()
        history_view = QTreeWidget()
        history_view.setHeaderLabels(["Title", "URL"])
        for url in self.history:
            QTreeWidgetItem(history_view, ["Title", url])
        layout.addWidget(history_view)
        dialog.setLayout(layout)
        dialog.exec_()
        
    def clear_history(self):
        self.history = []
        QMessageBox.information(self, "Clear History", "History cleared.")
        
    def view_bookmarks(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Bookmarks")
        layout = QVBoxLayout()
        bookmarks_view = QTreeWidget()
        bookmarks_view.setHeaderLabels(["Title", "URL"])
        for title, url in self.bookmarks:
            QTreeWidgetItem(bookmarks_view, [title, url])
        layout.addWidget(bookmarks_view)
        dialog.setLayout(layout)
        dialog.exec_()
        
    def add_bookmark(self):
        current_tab = self.browser_tabs.currentWidget()
        title = current_tab.page().title()
        url = current_tab.url().toString()
        self.bookmarks.append((title, url))
        QMessageBox.information(self, "Add Bookmark", f"Bookmark added for {title} ({url})")
        
    def view_downloads(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Downloads")
        layout = QVBoxLayout()
        downloads_view = QTreeWidget()
        downloads_view.setHeaderLabels(["File Name", "URL", "Progress"])
        layout.addWidget(downloads_view)
        dialog.setLayout(layout)
        dialog.exec_()
        
    def open_preferences(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        layout = QFormLayout()
        home_page_input = QLineEdit()
        layout.addRow("Home Page:", home_page_input)
        default_search_engine_input = QLineEdit()
        layout.addRow("Default Search Engine:", default_search_engine_input)
        save_btn = QPushButton("Save")
        layout.addWidget(save_btn)
        dialog.setLayout(layout)
        dialog.exec_()

    def show_about(self):
        QMessageBox.about(self, "About", "Welcome to Apex Browser, crafted by Shah Ram. Dive into a seamless browsing experience.")

app = QApplication(sys.argv)
QApplication.setApplicationName("Apex Browser")
window = SimpleBrowser()
app.exec_()
