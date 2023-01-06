"""
	NBooks - Bloco de anotações hierárquico com múltiplos arquivos
    Copyright (C) 2022  ehcelino

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import (QMainWindow, QToolBar, QAction, QTextEdit, QAbstractItemView, QWidget,
                              QMessageBox, QMenu, QFileDialog, QSystemTrayIcon, QDesktopWidget,
                             QListWidgetItem, QListWidget, QColorDialog)
from PyQt5.QtCore import (QItemSelectionModel, QCoreApplication, Qt, QObject, pyqtSignal,
                          QSize, QPoint, QFile, QTextStream)
from PyQt5.QtGui import (QIcon, QFont, QStandardItemModel, QStandardItem, QKeySequence,
                         QColorConstants, QColor, QTextList, QTextListFormat, QTextCursor, QPalette,
                         QMouseEvent, QClipboard, QCursor, QTextCharFormat)
from PyQt5.uic import loadUi
from PyQt5.QtPrintSupport import QPrintDialog, QPrintPreviewDialog, QPrinter
import sys, os, sqlite3
from main import Ui_MainWindow

try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'section.nbooks.sec.1'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

basedir = os.path.dirname(__file__)

HTML_EXTENSIONS = ['.htm', '.html']

def splitext(p):
    return os.path.splitext(p)[1].lower()

QCoreApplication.setOrganizationName('Empty')
QCoreApplication.setOrganizationDomain('empty.empty.com')
QCoreApplication.setApplicationName('nome_do_programa')

# QCoreApplication.setOrganizationName('Section')
# QCoreApplication.setOrganizationDomain('section.operations.com')
# QCoreApplication.setApplicationName('NBooks')  # test00


app = QtWidgets.QApplication(sys.argv)
app.setStyle('Fusion')

# Cria o objeto de ajustes do programa
settings = QtCore.QSettings()
# settings.clear()

tmp = settings.value('statusbar', False)
if tmp:
    app.setQuitOnLastWindowClosed(False)

# Classe de comunicação entre a janela de ícone flutuante e a principal
class Communicate(QObject):
    openWindow = pyqtSignal()

com = Communicate()


# def light_mode():
#     QtGui.QGuiApplication.setPalette(app.style().standardPalette())

lightpalette = app.style().standardPalette()

darkpalette = QPalette()
darkpalette.setColor(QPalette.Window, QColor(60, 63, 65))
darkpalette.setColor(QPalette.WindowText, QColor(118, 122, 123))
darkpalette.setColor(QPalette.Button, QColor(60, 63, 65))
darkpalette.setColor(QPalette.ButtonText, QColor(162, 172, 176))
darkpalette.setColor(QPalette.Text, QColor(162, 172, 176))  # (215, 221, 224)
darkpalette.setColor(QPalette.Base, QColor(43, 43, 43))
darkpalette.setColor(QPalette.Dark, QColor(43, 43, 43))
darkpalette.setColor(QPalette.Mid, QColor(43, 43, 43))
darkpalette.setColor(QPalette.Light, QColor(43, 43, 43))
darkpalette.setColor(QPalette.AlternateBase, QColor(102, 179, 255))
darkpalette.setColor(QPalette.ToolTipBase, QColor(43, 43, 43))
darkpalette.setColor(QPalette.ToolTipText, QColor(162, 172, 176))
darkpalette.setColor(QPalette.Active, QPalette.Button, QColor(43, 43, 43))
# palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
darkpalette.setColor(QPalette.Highlight, QColor(55, 71, 82))
darkpalette.setColor(QPalette.HighlightedText, QColor(162, 172, 176))
darkpalette.setColor(QPalette.Link, QColor(42, 130, 218))

bluepalette = QPalette()
bluepalette.setColor(QPalette.Window, QColor(4, 20, 93))
bluepalette.setColor(QPalette.WindowText, QColor(0, 191, 255))
bluepalette.setColor(QPalette.Button, QColor(0, 133, 178))
bluepalette.setColor(QPalette.ButtonText, QColor(0, 191, 255))
bluepalette.setColor(QPalette.Text, QColor(0, 191, 255))  # (215, 221, 224)
bluepalette.setColor(QPalette.Base, QColor(0, 75, 101))
bluepalette.setColor(QPalette.Dark, QColor(0, 75, 101))
bluepalette.setColor(QPalette.Mid, QColor(0, 75, 101))
bluepalette.setColor(QPalette.Light, QColor(0, 75, 101))
bluepalette.setColor(QPalette.AlternateBase, QColor(0, 103, 139))
bluepalette.setColor(QPalette.ToolTipBase, QColor(43, 43, 43))
bluepalette.setColor(QPalette.ToolTipText, QColor(162, 172, 176))
bluepalette.setColor(QPalette.Active, QPalette.Button, QColor(43, 43, 43))
# palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
bluepalette.setColor(QPalette.Highlight, QColor(0, 159, 215))
bluepalette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))
bluepalette.setColor(QPalette.Link, QColor(42, 130, 218))

# Modelo de busca
class SearchProxyModel(QtCore.QSortFilterProxyModel):
    def setFilterRegExp(self, pattern):
        if isinstance(pattern, str):
            pattern = QtCore.QRegExp(
                pattern, QtCore.Qt.CaseInsensitive,
                QtCore.QRegExp.FixedString)
        super(SearchProxyModel, self).setFilterRegExp(pattern)
    def _accept_index(self, idx):
        if idx.isValid():
            text = idx.data(QtCore.Qt.DisplayRole)
            if self.filterRegExp().indexIn(text) >= 0:
                return True
            for row in range(idx.model().rowCount(idx)):
                if self._accept_index(idx.model().index(row, 0, idx)):
                    return True
        return False
    def filterAcceptsRow(self, sourceRow, sourceParent):
        idx = self.sourceModel().index(sourceRow, 0, sourceParent)
        return self._accept_index(idx)

# Classe da janela que gera um ícone flutuante na área de trabalho
class IconWindow(QtWidgets.QWidget):
    def __init__(self):
        super(IconWindow, self).__init__()
        self.initUI()
    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        # self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)
        self.window().setWindowIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))
        self.setAttribute(Qt.WA_TranslucentBackground)

    def sizeHint(self):
        return QSize(36, 36) # Set this to the exact image resolution

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        pixmap = QtGui.QPixmap()
        pixmap.load('./icons/icon.png')
        qp.drawPixmap(QPoint(0, 0), pixmap)
        qp.end()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()
        # print(event.button())
        # if event.button() == QtCore.Qt.LeftButton:
        #     print('left button')
        #     self.oldPos = event.globalPos()
        # elif event.button() == QtCore.Qt.RightButton:
        #     print('right button')
        #     self.close()
        # As ações acima funcionam, mas passam a ativação do botão do mouse para a janela que estiver
        # abaixo desta quando ela fecha.

    def mouseDoubleClickEvent(self, QMouseEvent):
        print('double click!')
        # self.doubleclick = True
        com.openWindow.emit()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, QMouseEvent):
        if QMouseEvent.button() == QtCore.Qt.RightButton:
            self.close()


# Classe da janela novo item da árvore
class JanelaNovo(QWidget):
    def __init__(self):
        super().__init__()
        loadUi(os.path.join(basedir, 'ui', 'novo.ui'), self)
        theme = settings.value('theme', 'light')
        if theme == 'dark':
            self.setPalette(darkpalette)
        else:
            self.setPalette(lightpalette)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.window().setWindowIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))

# Classe da janela renomear
class JanelaRename(QWidget):
    def __init__(self):
        super().__init__()
        loadUi(os.path.join(basedir, 'ui', 'rename.ui'), self)
        theme = settings.value('theme', 'light')
        if theme == 'dark':
            self.setPalette(darkpalette)
        else:
            self.setPalette(lightpalette)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.window().setWindowIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))

# Classe da janela buscar
class JanelaBuscar(QWidget):
    def __init__(self):
        super().__init__()
        loadUi(os.path.join(basedir, 'ui', 'buscar.ui'), self)
        theme = settings.value('theme', 'light')
        if theme == 'dark':
            self.setPalette(darkpalette)
        else:
            self.setPalette(lightpalette)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.window().setWindowIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))

# Classe da janela novo notebook
class JanelaNbook(QWidget):
    def __init__(self):
        super().__init__()
        loadUi(os.path.join(basedir, 'ui', 'nv_caderno.ui'), self)
        theme = settings.value('theme', 'light')
        if theme == 'dark':
            self.setPalette(darkpalette)
        else:
            self.setPalette(lightpalette)
        # self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.window().setWindowIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))
        

# Classe da janela ajuda
class JanelaHelp(QWidget):
    def __init__(self):
        super().__init__()
        loadUi(os.path.join(basedir, 'ui', 'help.ui'), self)
        theme = settings.value('theme', 'light')
        if theme == 'dark':
            self.setPalette(darkpalette)
        else:
            self.setPalette(lightpalette)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.window().setWindowIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))

# Classe da janela principal
class MainWindow(QMainWindow, Ui_MainWindow):
    open_db = None
    new_db = None
    db_file = None
    db_address = None
    search_mode = False
    branch_type = 'root'
    iconpath = None
    old_item = None
    fonte_padrao = QFont('Calibri', 12)
    codigo_fonte = QFont('Jetbrains Mono', 10)
    inicio = True
    systray = False
    paste_html = False
    char_format = QTextCharFormat()
    char_format_code = QTextCharFormat()
    char_format_normal = QTextCharFormat()
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        super().setupUi(self)
        # Seta o ícone da janela
        self.setWindowIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))
        # Relação de conexão com a janela de ícone flutuante
        com.openWindow.connect(self.show)
        com.openWindow.connect(self.jan_irg)
        # Busca nas configurações o último banco de dados usado

        if not settings.value('database') == None:
            self.db_file = settings.value('database')
        print(self.db_file)

        self.setWindowTitle(f'NBooks ({self.db_file})')

        # Padrão de caractere, normal e código
        self.char_format.setFont(self.fonte_padrao)
        self.char_format.setForeground(QColor('black'))
        # char_format = QTextCharFormat()
        # char_format.setForeground(Qt.blue)
        self.char_format.setFontWeight(QFont.Normal)
        self.char_format_code.setFont(self.codigo_fonte)
        self.char_format_code.setForeground(QColor(97,132,87))
        self.char_format_code.setFontWeight(QFont.Normal)

        # self.palette = self.palette()

        # ########################################################################
        # Menu no systray
        # ########################################################################
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))
        self.tray.setToolTip('QText')
        self.tray.activated.connect(self.onTrayIconActivated)
        # #############################################
        self.traymenu = QMenu()
        self.action1 = QAction('Abrir janela')
        self.action1.triggered.connect(self.show)
        self.traymenu.addAction(self.action1)
        # #############################################
        self.action2 = QAction('Sair definitivamente')
        self.action2.triggered.connect(self.close_app)
        self.traymenu.addAction(self.action2)
        # #############################################
        self.tray.setContextMenu(self.traymenu)
        tmp = settings.value('statusbar', 'no')
        print('statusbar', tmp)
        if tmp != 'no':
            self.tray.setVisible(True)
            self.tray.setContextMenu(self.traymenu)
            app.setQuitOnLastWindowClosed(False)

        # Toolbar e menu Arquivo
        self.toolbar_arquivo = QToolBar('Arquivo')
        self.addToolBar(self.toolbar_arquivo)
        menu_arquivo = self.menuBar().addMenu('&Arquivo')
        # ###################################################
        self.new_db_action = QAction(QIcon(os.path.join(basedir, 'icons', 'newdb.png')), "Novo banco de dados", self)
        self.new_db_action.setStatusTip('Cria um banco de dados')
        self.new_db_action.triggered.connect(self.jan_nbook)
        menu_arquivo.addAction(self.new_db_action)
        # toolbar_arquivo.addAction(new_db_action)
        # ###################################################
        self.open_db_action = QAction(QIcon(os.path.join(basedir, 'icons', 'opendb.png')), "Abrir banco de dados", self)
        self.open_db_action.setStatusTip('Abre um banco de dados')
        self.open_db_action.triggered.connect(self.jan_openb)
        menu_arquivo.addAction(self.open_db_action)
        # toolbar_arquivo.addAction(open_db_action)
        # ###################################################
        remove_db_action = QAction(QIcon(os.path.join(basedir, 'icons', 'opendb.png')), "Remover notebook", self)
        remove_db_action.setStatusTip('Remove um notebook da lista')
        remove_db_action.triggered.connect(self.notebook_delete)
        menu_arquivo.addAction(remove_db_action)
        # toolbar_arquivo.addAction(open_db_action)
        # ###################################################
        menu_arquivo.addSeparator()
        # ###################################################
        self.insert_root_action = QAction(QIcon(os.path.join(basedir, 'icons', 'parent.png')), "Inserir pai", self)
        self.insert_root_action.setStatusTip('Inserir pai')
        self.insert_root_action.triggered.connect(self.setroot)
        self.insert_root_action.triggered.connect(self.jan_novo)
        menu_arquivo.addAction(self.insert_root_action)
        self.toolbar_arquivo.addAction(self.insert_root_action)
        # ###################################################
        self.insert_child_action = QAction(QIcon(os.path.join(basedir, 'icons', 'child.png')), "Inserir filho", self)
        self.insert_child_action.setStatusTip('Inserir filho')
        self.insert_child_action.triggered.connect(self.setchild)
        self.insert_child_action.triggered.connect(self.jan_novo)
        menu_arquivo.addAction(self.insert_child_action)
        self.toolbar_arquivo.addAction(self.insert_child_action)
        # ###################################################
        self.rename_action = QAction(QIcon(os.path.join(basedir, 'icons', 'rename.png')), "Renomear", self)
        self.rename_action.setStatusTip('Renomear')
        # rename_action.triggered.connect(self.rename_branch)
        self.rename_action.triggered.connect(self.jan_rename)
        menu_arquivo.addAction(self.rename_action)
        self.toolbar_arquivo.addAction(self.rename_action)
        # ###################################################
        self.delete_action = QAction(QIcon(os.path.join(basedir, 'icons', 'delete.png')), "Apagar", self)
        self.delete_action.setStatusTip('Apagar')
        # rename_action.triggered.connect(self.rename_branch)
        self.delete_action.triggered.connect(self.delete_branch)
        menu_arquivo.addAction(self.delete_action)
        self.toolbar_arquivo.addAction(self.delete_action)
        # ###################################################
        self.toolbar_arquivo.addSeparator()
        menu_arquivo.addSeparator()
        # ###################################################
        save_file_action = QAction(QIcon(os.path.join('icons', 'disk.png')), "Salvar", self)
        save_file_action.setStatusTip("Salva o arquivo atual (Ctrl+S)")
        save_file_action.triggered.connect(self.save_current)
        menu_arquivo.addAction(save_file_action)
        self.toolbar_arquivo.addAction(save_file_action)
        self.save_current_file_shortcut = QtWidgets.QShortcut(QKeySequence('Ctrl+S'), self)
        self.save_current_file_shortcut.activated.connect(self.save_current)
        # ###################################################
        export_file_action = QAction(QIcon(os.path.join('icons', 'export.png')), "Exportar", self)
        export_file_action.setStatusTip("Exporta o arquivo atual como HTML")
        export_file_action.triggered.connect(self.export_current)
        menu_arquivo.addAction(export_file_action)
        self.toolbar_arquivo.addAction(export_file_action)
        # ###################################################
        print_action = QAction(QIcon(os.path.join('icons', 'print.png')), "Imprimir", self)
        print_action.setStatusTip("Imprime o arquivo atual")
        print_action.triggered.connect(self.printpreviewDialog)
        menu_arquivo.addAction(print_action)
        self.toolbar_arquivo.addAction(print_action)
        # ###################################################
        menu_arquivo.addSeparator()
        # ###################################################
        quit_action = QAction(QIcon(os.path.join('icons', 'exit.png')), "Sair", self)
        quit_action.setStatusTip("Sai do programa")
        quit_action.triggered.connect(self.close_app)
        menu_arquivo.addAction(quit_action)
        # self.toolbar_arquivo.addAction(quit_action)
        # # ###################################################
        # # Menu de arquivos recentes
        # self.recent_menu = menu_arquivo.addMenu('&Abrir recente')
        # self.recent_menu.aboutToShow.connect(self.update_recent_menu)
        # self.recent_menu.triggered.connect(self.open_file_from_recent)
        # # self.settings = {}
        # ###################################################
        # Toolbar e menu Editar
        self.toolbar_editar = QToolBar("Editar")
        self.addToolBar(self.toolbar_editar)
        menu_editar = self.menuBar().addMenu("&Editar")
        # ###################################################
        search_action = QAction(QIcon(os.path.join('icons', 'search.png')), "Localizar", self)
        search_action.setStatusTip("Localizar")
        search_action.triggered.connect(self.jan_buscar)
        self.toolbar_editar.addAction(search_action)
        menu_editar.addAction(search_action)
        # ###################################################
        undo_action = QAction(QIcon(os.path.join('icons', 'undo.png')), "Desfazer", self)
        undo_action.setStatusTip("Desfazer (Ctrl+Z)")
        undo_action.triggered.connect(self.txtEditor.undo)
        undo_action.setShortcut(QKeySequence.Undo)
        self.toolbar_editar.addAction(undo_action)
        menu_editar.addAction(undo_action)
        # ###################################################
        redo_action = QAction(QIcon(os.path.join('icons', 'redo.png')), "Refazer", self)
        redo_action.setStatusTip("Refazer (Ctrl+Shift+Z)")
        redo_action.triggered.connect(self.txtEditor.redo)
        redo_action.setShortcut(QKeySequence.Redo)
        self.toolbar_editar.addAction(redo_action)
        menu_editar.addAction(redo_action)
        # ###################################################
        self.toolbar_editar.addSeparator()
        menu_editar.addSeparator()
        # ###################################################
        cut_action = QAction(QIcon(os.path.join('icons', 'cut.png')), "Recortar", self)
        cut_action.setStatusTip("Recortar (Ctrl+X)")
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.txtEditor.cut)
        self.toolbar_editar.addAction(cut_action)
        menu_editar.addAction(cut_action)
        # ###################################################
        copy_action = QAction(QIcon(os.path.join('icons', 'copy.png')), "Copiar", self)
        copy_action.setStatusTip("Copiar (Ctrl+C)")
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.txtEditor.copy)
        self.toolbar_editar.addAction(copy_action)
        menu_editar.addAction(copy_action)
        # ###################################################
        self.paste_action = QAction(QIcon(os.path.join(basedir, 'icons', 'paste.png')), "Colar", self)
        self.paste_action.setStatusTip("Colar (Ctrl+V)")
        self.paste_action.setShortcut(QKeySequence.Paste)
        self.paste_action.triggered.connect(self.txtEditor.paste)
        self.toolbar_editar.addAction(self.paste_action)
        menu_editar.addAction(self.paste_action)
        # ###################################################
        self.paste_mode_action = QAction(QIcon(os.path.join(basedir, 'icons', 'paste.png')),
                                         "Colar como HTML", self)
        self.paste_mode_action.setStatusTip("Colar como HTML")
        # self.paste_mode_action.setShortcut(QKeySequence.Paste)
        self.paste_mode_action.triggered.connect(self.paste_as_html)
        # self.toolbar_editar.addAction(self.paste_mode_action)
        menu_editar.addAction(self.paste_mode_action)
        # ###################################################
        self.reset_char_action = QAction(QIcon(os.path.join(basedir, 'icons', 'default_char.png')),
                                         "Resetar caractere padrão", self)
        self.reset_char_action.setStatusTip("Resetar caractere padrão")
        # self.paste_mode_action.setShortcut(QKeySequence.Paste)
        self.reset_char_action.triggered.connect(self.reset_default_char)
        # self.toolbar_editar.addAction(self.paste_mode_action)
        menu_editar.addAction(self.reset_char_action)
        # ###################################################
        menu_editar.addSeparator()
        # ###################################################
        select_action = QAction(QIcon(os.path.join('icons', 'all.png')), "Selecionar tudo", self)
        select_action.setStatusTip("Seleciona todo o texto (Ctrl + A)")
        cut_action.setShortcut(QKeySequence.SelectAll)
        select_action.triggered.connect(self.txtEditor.selectAll)
        menu_editar.addAction(select_action)

        # Toolbar e menu Formatar
        self.toolbar_formatar = QToolBar("Formatar")
        self.addToolBar(self.toolbar_formatar)
        menu_formatar = self.menuBar().addMenu("&Formatar")
        # ###################################################
        self.bold_action = QAction(QIcon(os.path.join(basedir, 'icons', 'bold.png')), "Negrito", self)
        self.bold_action.setStatusTip("Negrito (Ctrl+B)")
        self.bold_action.setShortcut(QKeySequence.Bold)
        self.bold_action.setCheckable(True)
        self.bold_action.toggled.connect(lambda x: self.txtEditor.setFontWeight(QFont.Bold if x else QFont.Normal))
        self.toolbar_formatar.addAction(self.bold_action)
        menu_formatar.addAction(self.bold_action)
        # ###################################################
        self.italic_action = QAction(QIcon(os.path.join(basedir, 'icons', 'italic.png')), "Itálico", self)
        self.italic_action.setStatusTip("Itálico (Ctrl+I)")
        self.italic_action.setShortcut(QKeySequence.Italic)
        self.italic_action.setCheckable(True)
        self.italic_action.toggled.connect(self.txtEditor.setFontItalic)
        self.toolbar_formatar.addAction(self.italic_action)
        menu_formatar.addAction(self.italic_action)
        # ###################################################
        self.underline_action = QAction(QIcon(os.path.join(basedir, 'icons', 'underline.png')), "Sublinhado", self)
        self.underline_action.setStatusTip("Sublinhado (Ctrl+U)")
        self.underline_action.setShortcut(QKeySequence.Underline)
        self.underline_action.setCheckable(True)
        self.underline_action.toggled.connect(self.txtEditor.setFontUnderline)
        self.toolbar_formatar.addAction(self.underline_action)
        menu_formatar.addAction(self.underline_action)
        # ###################################################
        self.toolbar_formatar.addSeparator()
        # ###################################################
        self.default_color = QColorConstants.Transparent
        # self.highlight_color = QColor(52, 65, 52)
        tmp = settings.value('hl_color', '#ffff00')
        self.highlight_color = QColor(tmp)
        self.highlight_action = QAction(QIcon(os.path.join(basedir, 'icons', 'highlight.png')), "Realce", self)
        self.highlight_action.setStatusTip("Realce (Ctrl+R)")
        self.highlight_action.setCheckable(True)
        self.highlight_action.toggled.connect(
            lambda x: self.txtEditor.setTextBackgroundColor(self.highlight_color if x else self.default_color))
        self.toolbar_formatar.addAction(self.highlight_action)
        menu_formatar.addAction(self.highlight_action)
        self.highlight_action.setShortcut(QKeySequence('Ctrl+R'))
        # ###################################################

        # self.codigo_fonte = QFont('Jetbrains Mono', 10)
        self.codigo_action = QAction(QIcon(os.path.join(basedir, 'icons', 'code.png')), "Código", self)
        self.codigo_action.setStatusTip("Código (Ctrl+K)")
        self.codigo_action.setCheckable(True)
        # self.codigo_action.toggled.connect(
        #     lambda x: self.txtEditor.setCurrentFont(self.codigo_fonte if x else self.fonte_padrao))
        self.codigo_action.toggled.connect(
            lambda x: self.txtEditor.setCurrentCharFormat(self.char_format_code if x else self.char_format))
        self.toolbar_formatar.addAction(self.codigo_action)
        menu_formatar.addAction(self.codigo_action)
        self.codigo_action.setShortcut(QKeySequence('Ctrl+K'))
        # ###################################################
        self.bullet_action = QAction(QIcon(os.path.join(basedir, 'icons', 'bullet.png')), "Lista de itens", self)
        self.bullet_action.setStatusTip("Lista de itens")
        self.bullet_action.triggered.connect(self.bullet_list)
        self.toolbar_formatar.addAction(self.bullet_action)
        menu_formatar.addAction(self.bullet_action)
        # ###################################################
        hlcolor_action = QAction(QIcon(os.path.join('icons', 'hlcolor.png')), "Cor de realce", self)
        hlcolor_action.setStatusTip("Altera a cor do realce")
        hlcolor_action.triggered.connect(self.set_highlight_color)
        menu_formatar.addAction(hlcolor_action)
        # self.toolbar_arquivo.addAction(hlcolor_action)
        # ###################################################

        # Toolbar e menu Tema
        # toolbar_tema = QToolBar("Formatar")
        # self.addToolBar(toolbar_tema)
        menu_tema = self.menuBar().addMenu("&Tema")
        light_theme_action = QAction(QIcon(os.path.join('icons', 'light.png')), "Tema claro", self)
        light_theme_action.setStatusTip("Altera o tema do aplicativo")
        light_theme_action.triggered.connect(self.light_mode)
        menu_tema.addAction(light_theme_action)
        # toolbar_tema.addAction(theme_action)
        # ###################################################
        dark_theme_action = QAction(QIcon(os.path.join('icons', 'dark.png')), "Tema escuro", self)
        dark_theme_action.setStatusTip("Altera o tema do aplicativo")
        dark_theme_action.triggered.connect(self.dark_mode)
        menu_tema.addAction(dark_theme_action)
        # toolbar_tema.addAction(theme_action)
        # ###################################################
        blue_theme_action = QAction(QIcon(os.path.join('icons', 'dark.png')), "Tema azul", self)
        blue_theme_action.setStatusTip("Altera o tema do aplicativo")
        blue_theme_action.triggered.connect(self.blue_mode)
        menu_tema.addAction(blue_theme_action)
        # toolbar_tema.addAction(theme_action)
        # ###################################################
        # toolbar_help = QToolBar("Ajuda")
        # self.addToolBar(toolbar_help)
        self.menu_help = self.menuBar().addMenu("Ajuda")
        # ###################################################
        help_action = QAction(QIcon(os.path.join('icons', 'help.png')), "Ajuda", self)
        help_action.setStatusTip("Ajuda do aplicativo")
        help_action.triggered.connect(self.help_mode)
        self.menu_help.addAction(help_action)
        # ###################################################
        self.statusbar_action = QAction(QIcon(os.path.join('icons', 'systray.png')), "Ícone no systray", self, checkable=True)
        self.statusbar_action.setStatusTip("Adiciona um ícone do aplicativo no systray")
        self.statusbar_action.triggered.connect(self.tray_icon)
        self.menu_help.addAction(self.statusbar_action)
        tmp = settings.value('statusbar', 'no')
        print('statusbar', tmp)
        if tmp != 'no':
            self.statusbar_action.setChecked(True)

        self._format_actions = [
            self.bold_action,
            self.italic_action,
            self.underline_action,
            self.highlight_action,
            self.codigo_action,
        ]

        # Inicialização do editor de texto
        self.txtEditor.setAcceptRichText(False)  # <------------ necessário para o colar sem formatação
        self.txtEditor.setFont(self.fonte_padrao)
        self.txtEditor.setFontPointSize(12)
        self.txtEditor.setAutoFormatting(QTextEdit.AutoNone)
        self.txtEditor.setDisabled(True)
        # Ações do editor de texto
        self.txtEditor.selectionChanged.connect(self.update_format)  # com o mouse
        self.txtEditor.cursorPositionChanged.connect(self.update_format)  # com o teclado
        # self.txtEditor.textChanged.connect(self.update_format)  # <----------- TENTATIVA
        # self.textEdit.selectionChanged.connect(self.text_changed)
        self.txtEditor.textChanged.connect(self.text_changed)
        # self.txtEditor.selectionChanged.connect(self.documentWasModified)
        # self.txtEditor.textChanged.connect(self.documentWasModified)

        # Configuração da árvore
        self.treLista.setSelectionMode(QAbstractItemView.SingleSelection)
        self.treLista.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.treLista.header().hide()
        self.treLista.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treLista.customContextMenuRequested.connect(self.menu_lista)
        self.treLista.clicked.connect(self.update_format)  # <------------- TENTATIVA
        # self.treLista.clicked.connect(lambda: self.status.showMessage(''))

        # Configurações dos modelos
        self.model = QStandardItemModel()
        # self.model.dataChanged.connect(self.on_dataChanged)
        self.filter_proxy_model = SearchProxyModel()
        self.filter_proxy_model.setSourceModel(self.model)
        self.filter_proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.treLista.setModel(self.filter_proxy_model)
        self.selection_model = self.treLista.selectionModel()
        self.selection_model.selectionChanged.connect(self.read_content)

        # Janelas
        # Janela novo item
        self.novo = JanelaNovo()
        self.novo.btnPython.clicked.connect(lambda: self.set_icon('python'))
        self.novo.btnCode.clicked.connect(lambda: self.set_icon('code'))
        self.novo.btnAsterisk.clicked.connect(lambda: self.set_icon('asterisk'))
        self.novo.btnNota.clicked.connect(lambda: self.set_icon('nota'))
        self.novo.btnCheck.clicked.connect(lambda: self.set_icon('check'))
        self.novo.btnPasta.clicked.connect(lambda: self.set_icon('pasta'))
        self.novo.btnLinux.clicked.connect(lambda: self.set_icon('linux'))
        self.novo.btnInternet.clicked.connect(lambda: self.set_icon('internet'))
        self.novo.btnWindows.clicked.connect(lambda: self.set_icon('windows'))
        self.novo.btnKey.clicked.connect(lambda: self.set_icon('key'))
        self.novo.btnClip.clicked.connect(lambda: self.set_icon('clip'))
        self.novo.btnDisk.clicked.connect(lambda: self.set_icon('disk'))
        self.novo.btnCriar.clicked.connect(self.insert_branch)
        self.novo.btnCriar.clicked.connect(self.jan_novo)
        self.novo.btnVoltar.clicked.connect(self.jan_novo)
        self.novo.txtName.returnPressed.connect(self.insert_branch)
        self.novo.txtName.returnPressed.connect(self.jan_novo)

        # Janela renomear
        self.rename = JanelaRename()
        self.rename.btnPython.clicked.connect(lambda: self.set_icon('python'))
        self.rename.btnCode.clicked.connect(lambda: self.set_icon('code'))
        self.rename.btnAsterisk.clicked.connect(lambda: self.set_icon('asterisk'))
        self.rename.btnNota.clicked.connect(lambda: self.set_icon('nota'))
        self.rename.btnCheck.clicked.connect(lambda: self.set_icon('check'))
        self.rename.btnPasta.clicked.connect(lambda: self.set_icon('pasta'))
        self.rename.btnLinux.clicked.connect(lambda: self.set_icon('linux'))
        self.rename.btnInternet.clicked.connect(lambda: self.set_icon('internet'))
        self.rename.btnWindows.clicked.connect(lambda: self.set_icon('windows'))
        self.rename.btnKey.clicked.connect(lambda: self.set_icon('key'))
        self.rename.btnClip.clicked.connect(lambda: self.set_icon('clip'))
        self.rename.btnDisk.clicked.connect(lambda: self.set_icon('disk'))
        self.rename.btnRenomear.clicked.connect(self.rename_branch)
        self.rename.btnRenomear.clicked.connect(self.jan_rename)
        self.rename.btnVoltar.clicked.connect(self.jan_rename)
        self.rename.txtName.returnPressed.connect(self.rename_branch)
        self.rename.txtName.returnPressed.connect(self.jan_rename)

        # Janela novo notebook
        self.nbook = JanelaNbook()
        self.nbook.btnPython.clicked.connect(lambda: self.set_icon('python'))
        self.nbook.btnCode.clicked.connect(lambda: self.set_icon('code'))
        self.nbook.btnAsterisk.clicked.connect(lambda: self.set_icon('asterisk'))
        self.nbook.btnNota.clicked.connect(lambda: self.set_icon('nota'))
        self.nbook.btnCheck.clicked.connect(lambda: self.set_icon('check'))
        self.nbook.btnPasta.clicked.connect(lambda: self.set_icon('pasta'))
        self.nbook.btnLinux.clicked.connect(lambda: self.set_icon('linux'))
        self.nbook.btnInternet.clicked.connect(lambda: self.set_icon('internet'))
        self.nbook.btnWindows.clicked.connect(lambda: self.set_icon('windows'))
        self.nbook.btnKey.clicked.connect(lambda: self.set_icon('key'))
        self.nbook.btnClip.clicked.connect(lambda: self.set_icon('clip'))
        self.nbook.btnDisk.clicked.connect(lambda: self.set_icon('disk'))
        self.nbook.btnArquivo.clicked.connect(self.new_db_filechooser)
        self.nbook.btnCriar.clicked.connect(self.new_database)
        self.nbook.btnCriar.clicked.connect(self.jan_nbook)
        self.nbook.btnCancelar.clicked.connect(self.jan_nbook)
        
        # Janela abrir notebook
        self.openb = JanelaNbook()
        self.openb.btnPython.clicked.connect(lambda: self.set_icon('python'))
        self.openb.btnCode.clicked.connect(lambda: self.set_icon('code'))
        self.openb.btnAsterisk.clicked.connect(lambda: self.set_icon('asterisk'))
        self.openb.btnNota.clicked.connect(lambda: self.set_icon('nota'))
        self.openb.btnCheck.clicked.connect(lambda: self.set_icon('check'))
        self.openb.btnPasta.clicked.connect(lambda: self.set_icon('pasta'))
        self.openb.btnLinux.clicked.connect(lambda: self.set_icon('linux'))
        self.openb.btnInternet.clicked.connect(lambda: self.set_icon('internet'))
        self.openb.btnWindows.clicked.connect(lambda: self.set_icon('windows'))
        self.openb.btnKey.clicked.connect(lambda: self.set_icon('key'))
        self.openb.btnClip.clicked.connect(lambda: self.set_icon('clip'))
        self.openb.btnDisk.clicked.connect(lambda: self.set_icon('disk'))
        self.openb.btnArquivo.clicked.connect(self.open_notebook_file)
        self.openb.btnCriar.clicked.connect(self.open_notebook)
        self.openb.btnCriar.clicked.connect(self.jan_openb)
        self.openb.btnCancelar.clicked.connect(self.jan_openb)
        
        # Janela buscar
        self.buscar = JanelaBuscar()
        self.buscar.btnBuscar.clicked.connect(self.busca_no_texto)
        self.buscar.txtBusca.returnPressed.connect(self.busca_no_texto)
        self.buscar.btnVoltar.clicked.connect(self.jan_buscar)

        # Janela ícone flutuante
        self.irg = IconWindow()
        self.irg.mouseDoubleClickEvent(self.show)

        # Janela help
        self.help = JanelaHelp()
        self.help.btnVoltar.clicked.connect(self.jan_help)

        # Ações da janela principal
        self.txtBusca.textChanged.connect(self.search_text_changed)
        self.btnLimpa.clicked.connect(lambda: self.txtBusca.setText(''))
        self.btnLimpa.clicked.connect(self.search_text_changed)
        self.btnLimpa.setToolTip('Limpa a área de pesquisa')
        self.btnSair.clicked.connect(self.bubble)
        self.btnSair.setToolTip('Alterna entre a janela e o ícone flutuante')
        self.btnSairTotal.clicked.connect(self.close_app)
        self.btnSairTotal.setToolTip('Fecha o programa')
        self.btnShrink.clicked.connect(self.mini)
        self.btnShrink.setToolTip('Mini janela de notas')
        self.btnNbs.clicked.connect(self.notebooks_list)
        self.btnNbs.setToolTip('Blocos de notas')
        self.btnNbs.setIcon(QIcon(os.path.join(basedir, 'icons', 'forward.png')))
        self.listWidget.clicked.connect(self.notebook_click)
        self.btnAbreNb.clicked.connect(self.jan_openb)
        self.btnAbreNb.setToolTip('Abrir um bloco de notas')
        self.btnNovoNb.clicked.connect(self.jan_nbook)
        self.btnNovoNb.setToolTip('Criar um bloco de notas')
        self.btnRemoverNb.clicked.connect(self.notebook_delete)
        self.btnRemoverNb.setToolTip('Remover um bloco de notas da lista')

        # Funções de inicialização do programa
        # self.address_database()
        #self.frmLista.setBaseSize(200,200)
        self.splitter.setStretchFactor(1, 30)
        self.splitter.setSizes([200, 300])
        self.read_database()
        self.change_theme()
        self.start()
        self.open_notebooks_db()
        self.frmNbs.hide()
        # self.select_last()


    # #################################################################################
    # Funções de ativação das janelas
    # #################################################################################

    def jan_novo(self):
        if self.novo.isVisible():
            self.novo.hide()
            self.novo.txtName.setText('')
        else:
            self.novo.show()
            # ############# DESABILITADO NA TENTATIVA DE INSERIR BRANCH ATRAVES DA CHILD
            # if self.branch_type == 'child':
            #     selection = self.treLista.selectionModel().selectedRows()
            #     if selection != []:
            #         selection_x = [self.treLista.model().mapToSource(index) for index in selection]
            #         item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
            #         if item.parent() == None:
            #             self.novo.show()
            # else:
            #     self.novo.show()

    def jan_rename(self):
        if self.rename.isVisible():
            self.rename.txtName.setText('')
            self.rename.hide()
        else:
            self.rename.show()
            selection = self.treLista.selectionModel().selectedRows()
            selection_x = [self.treLista.model().mapToSource(index) for index in selection]
            item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
            icone = item.icon()
            self.rename.txtName.setText(item.text())

    def jan_buscar(self):
        if self.buscar.isVisible():
            self.buscar.hide()
        else:
            if self.txtEditor.isEnabled():
                self.buscar.txtBusca.setText('')
                self.buscar.show()

    def jan_irg(self):
        # Janela que funciona como um ícone flutuante
        if self.irg.isVisible():
            self.irg.hide()
        else:
            self.irg.show()

    def jan_help(self):
        # theme = settings.value('theme', 'light')
        # if theme == 'dark':
        #     JanelaHelp().setPalette(darkpalette)
        # else:
        #     JanelaHelp().setPalette(lightpalette)
        if self.help.isVisible():
            self.help.hide()
        else:
            self.help.show()

    def jan_nbook(self):
        if self.nbook.isVisible():
            self.nbook.hide()
        else:
            if self.listWidget.isVisible():
                self.nbook.show()

    def jan_openb(self):
        if self.openb.isVisible():
            self.openb.hide()
        else:
            if self.listWidget.isVisible():
                self.openb.show()

    # def documentWasModified(self):
    #         print('entrou')
    #         self.window().setWindowModified(True)
    #         # self.txtFont.setText(self.txtEditor.currentCharFormat().font().toString())
    #         self.txtFont.setText(self.txtEditor.currentFont().toString())

    # #################################################################################
    # Função do menu da treeView
    # #################################################################################

    def menu_lista(self, pos):
        """
        Menu de contexto da treeView
        :param pos:
        :return:
        """
        self.menu = QMenu(self)
        self.menu.addAction(self.insert_root_action)
        self.menu.addAction(self.insert_child_action)
        self.menu.addAction(self.rename_action)
        self.menu.addAction(self.delete_action)
        self.menu.popup(pos)
        self.menu.exec_(self.treLista.mapToGlobal(pos))

    def tray_icon(self):
        tmp = settings.value('statusbar')
        if tmp == 'no':
            print('ativando icone')
            settings.setValue('statusbar', 'yes')
            self.tray.setVisible(True)
            app.setQuitOnLastWindowClosed(False)
        else:
            print('desativando icone')
            settings.setValue('statusbar', 'no')
            self.tray.setVisible(False)
            app.setQuitOnLastWindowClosed(True)

    def reset_default_char(self):
        self.txtEditor.setCurrentCharFormat(self.char_format)


    def paste_as_html(self):
        """
        Ativa a colagem em modo html no programa
        :return:
        """
        # if not self.paste_html:
        #     print('ativando colagem em html')
        #     self.txtEditor.setAcceptRichText(True)
        #     self.paste_html = True
        # else:
        #     print('desativando colagem em html')
        #     self.txtEditor.setAcceptRichText(False)
        #     self.paste_html = False
        before_char = self.txtEditor.currentCharFormat()
        before_font = self.txtEditor.currentFont()
        self.txtEditor.setAcceptRichText(True)
        self.txtEditor.paste()
        self.txtEditor.setAcceptRichText(False)
        # self.txtEditor.setCurrentFont(before_font)
        # self.txtEditor.setCurrentCharFormat(before_char)
        self.txtEditor.setCurrentCharFormat(self.char_format)
        # newCursor = QTextCursor(self.txtEditor.document())
        # self.txtEditor.setTextCursor(newCursor)
    # #################################################################################
    # Menu de arquivos recentes
    # #################################################################################

    # def load_recent_files(self):
    #     filenames = settings.value("recent_files", [])
    #     for filename in filenames:
    #         self.add_recent_filename(filename)
    #
    # def save_settings(self):
    #     recentfiles = []
    #     for action in self.menu_recentes.actions()[::-1]:
    #         recentfiles.append(action.text())
    #     settings.setValue("recent_files", recentfiles)
    #
    # @QtCore.pyqtSlot(QtWidgets.QAction)
    # def handle_triggered_recentfile(self, action):
    #     self.process_filename(action.text())
    #
    # def add_recent_filename(self, filename):
    #     action = QtWidgets.QAction(filename, self)
    #     actions = self.menu_recentes.actions()
    #     before_action = actions[0] if actions else None
    #     self.menu_recentes.insertAction(before_action, action)
    #
    # def another_task(self):
    #     # DEMO
    #     # load new filenames
    #     counter = len(self.menu_recentes.actions())
    #     filenames = [f"foo {counter}"]
    #     for filename in filenames:
    #         self.add_recent_filename(filename)

    def update_recent_menu(self):
        """
        Atualiza o menu de arquivos recentes buscando nos ajustes do sistema.
        :return:
        """
        self.recent_menu.clear()
        for row, filename in enumerate(self.get_recent_files(), 1):
            recent_action = self.recent_menu.addAction('&{}. {}'.format(
                row, filename))
            recent_action.setData(filename)

    def get_recent_files(self):
        """
        Busca nos ajustes do sistema pela lista de arquivos recentes.
        :return:
        """
        recent_files = settings.value("recent_files", [])
        # recent = self.settings.get('recent files')
        # if not recent:
        #     # just for testing purposes
        #     recent = self.settings['recent files'] = ['filename 4', 'filename1', 'filename2', 'filename3']
        return recent_files

    def open_file_from_recent(self, action):
        """
        Abre um arquivo através do menu recentes, usando as ações como base.
        :param action:
        :return:
        """
        self.open_file(action.data())

    def open_file(self, filename):
        """
        Atualiza as entradas nas configurações do sistema com o novo nome de arquivo.
        :param filename:
        :return:
        """
        recent = self.get_recent_files()
        if filename in recent:
            recent.remove(filename)
        recent.insert(0, filename)
        settings.setValue('recent_files', recent)
        self.opening_database(filename)
        print(filename)

    def remove_filename(self, filename):
        """
        Atualiza as entradas nas configurações do sistema com o novo nome de arquivo.
        :param filename:
        :return:
        """
        recent = self.get_recent_files()
        if filename in recent:
            recent.remove(filename)
        settings.setValue('recent_files', recent)


    # #################################################################################
    # Funções de estilos do documento
    # #################################################################################

    def bullet_list(self):
        """
        Ativa/desativa a formatação de lista com bullets.
        :return:
        """
        if self.txtEditor.isEnabled():
            cursor = self.txtEditor.textCursor()
            textList = cursor.currentList()
            if textList:
                start = cursor.selectionStart()
                end = cursor.selectionEnd()
                removed = 0
                for i in range(textList.count()):
                    item = textList.item(i - removed)
                    if (item.position() <= end and
                            item.position() + item.length() > start):
                        textList.remove(item)
                        blockCursor = QTextCursor(item)
                        blockFormat = blockCursor.blockFormat()
                        blockFormat.setIndent(0)
                        blockCursor.mergeBlockFormat(blockFormat)
                        removed += 1
                self.txtEditor.setTextCursor(cursor)
                self.txtEditor.setFocus()
            else:
                listFormat = QTextListFormat()
                style = QTextListFormat.ListDisc
                listFormat.setStyle(style)
                cursor.createList(listFormat)
                self.txtEditor.setTextCursor(cursor)
                self.txtEditor.setFocus()

    def set_highlight_color(self):
        """
        Altera a cor do realce.
        :return:
        """
        color = QColorDialog.getColor()
        print(color.name())
        if not color.isValid():
            self.set_highlight_color()
        else:
            settings.setValue('hl_color', color)
            self.highlight_color = QColor(color)

    # #################################################################################
    # Funções responsáveis pelos botões de formatação
    # #################################################################################

    def block_signals(self, objects, b):
        for o in objects:
            o.blockSignals(b)

    def clear_format(self):
        """
        Tentativa de retirar a formatação na mudança de ramo da árvore
        :return:
        """
        # self.block_signals(self._format_actions, True)
        self.highlight_action.setChecked(False)
        self.codigo_action.setChecked(False)
        # if self.txtEditor.currentFont().toString()[0] == self.codigo_fonte.toString()[0]:
        #     print('igual')
        self.italic_action.setChecked(False)
        self.underline_action.setChecked(False)
        self.bold_action.setChecked(False)
        # self.block_signals(self._format_actions, False)

    def update_format(self):
        """
        Update the font format toolbar/actions when a new text selection is made. This is neccessary to keep
        toolbars/etc. in sync with the current edit state.
        :return:
        """
        # Disable signals for all format widgets, so changing values here does not trigger further formatting.
        self.block_signals(self._format_actions, True)

        self.highlight_action.setChecked(self.txtEditor.textBackgroundColor() == self.highlight_color)
        self.codigo_action.setChecked(self.txtEditor.currentFont().toString()[0] == self.codigo_fonte.toString()[0])
        # if self.txtEditor.currentFont().toString()[0] == self.codigo_fonte.toString()[0]:
        #     print('igual')
        self.italic_action.setChecked(self.txtEditor.fontItalic())
        self.underline_action.setChecked(self.txtEditor.fontUnderline())
        self.bold_action.setChecked(self.txtEditor.fontWeight() == QFont.Bold)

        self.block_signals(self._format_actions, False)

    # #################################################################################
    # Função de ajuda
    # #################################################################################
    def help_mode(self):
        """
        Abre o conteúdo da ajuda.
        :return:
        """
        self.help.tbrHelp.setReadOnly(True)
        f = QFile(os.path.join(basedir, 'help.html'))
        f.open(QFile.ReadOnly | QFile.Text)
        istream = QTextStream(f)
        self.help.tbrHelp.setHtml(istream.readAll())
        f.close()
        self.jan_help()

    # #################################################################################
    # Ativação do ícone no systray
    # #################################################################################
    def onTrayIconActivated(self, reason):
        """
        Ativação do ícone do systray.
        :param reason:
        :return:
        """
        print("onTrayIconActivated:", reason)
        if reason == 2:
            self.show()

    # #################################################################################
    # Funções de impressão
    # #################################################################################

    # def file_print(self):
    #     dlg = QPrintDialog()
    #     if dlg.exec_():
    #         self.txtEditor.print_(dlg.printer())

    def printpreviewDialog(self):
        """
        Abre uma janela de visualização de impressão.
        :return:
        """
        if self.txtEditor.isEnabled():
            printer = QPrinter(QPrinter.HighResolution)
            previewDialog = QPrintPreviewDialog(printer, self)
            previewDialog.paintRequested.connect(self.printPreview)
            previewDialog.exec_()

    def printPreview(self, printer):
        self.txtEditor.document().print_(printer)

    # #################################################################################
    # Funções de busca
    # #################################################################################

    def search_text_changed(self, text=None):
        """
        Faz uma busca pelo texto na treeView.
        :param text:
        :return:
        """
        self.search_mode = True
        self.filter_proxy_model.setFilterRegExp(self.txtBusca.text())
        self.txtEditor.setText('')
        self.txtEditor.setDisabled(True)
        if len(self.txtBusca.text()) >= 1 and self.filter_proxy_model.rowCount() > 0:
            self.treLista.expandAll()
        else:
            self.treLista.collapseAll()
        self.search_mode = False

    def busca_no_texto(self):
        """
        Faz uma busca no textEdit.
        :return:
        """
        self.txtEditor.find(self.buscar.txtBusca.text())

    # #################################################################################
    # Função de auto salvamento do textEdit quando modificado
    # #################################################################################

    def text_changed(self):
        """
        Salva automaticamente o conteúdo do textEdit quando são feitas modificações.
        :return:
        """
        selection = self.treLista.selectionModel().selectedRows()
        if selection != []:
            selection_x = [self.treLista.model().mapToSource(index) for index in selection]
            # assets = self.treeView.model().sourceModel().getSelectedItems(selection_x)
            item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
            if item.parent() != None:
                if item != self.old_item:
                    self.changed = 0
                    self.old_item = item
                else:
                    self.changed = self.changed + 1
                    if self.changed >= 10:
                        self.save_current()
                        self.changed = 0

    # #################################################################################
    # Funções relacionadas à treeView
    # #################################################################################

    def setroot(self):
        """
        Seta root para a função insert_branch
        :return:
        """
        self.branch_type = 'root'

    def setchild(self):
        """
        Seta child para a função insert_branch
        :return:
        """
        self.branch_type = 'child'

    def insert_branch(self):
        """
        Insere um galho na treeView. Pode ser tanto root quanto child.
        :return:
        """
        if self.branch_type == 'root':
            if self.iconpath != None:
                parent = QStandardItem(self.icon, self.novo.txtName.text())
                self.filter_proxy_model.sourceModel().appendRow(parent)
                conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
                c = conexao.cursor()
                comando = f"""INSERT INTO parent (icon, desc) VALUES ('{self.iconpath}', '{self.novo.txtName.text()}')"""
                c.execute(comando)
                conexao.commit()
                comando = 'SELECT max(idx) FROM parent'
                c.execute(comando)
                dados = c.fetchone()[0]
                parent.setData(str(dados))
                conexao.close()
                ix = self.model.indexFromItem(parent)
                ix_proxy = self.filter_proxy_model.mapFromSource(ix)
                self.treLista.selectionModel().select(ix_proxy, QtCore.QItemSelectionModel.ClearAndSelect)
        else:
            if self.treLista.selectionModel().selectedRows() != []:
                if self.iconpath != None:
                    selection = self.treLista.selectionModel().selectedRows()
                    selection_x = [self.treLista.model().mapToSource(index) for index in selection]
                    parent_item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
                    if parent_item.parent() == None:
                        child = QStandardItem(self.icon, self.novo.txtName.text())
                        parent_item.appendRow(child)
                        child_index = child.index()
                        conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
                        c = conexao.cursor()
                        comando = f"""
                                    INSERT INTO child (icon, desc, rel_parent)
                                    VALUES ('{self.iconpath}',
                                    '{self.novo.txtName.text()}', '{parent_item.data()}')
                                    """
                        c.execute(comando)
                        conexao.commit()
                        comando = 'SELECT max(idx) FROM child'
                        c.execute(comando)
                        dados = c.fetchone()[0]
                        child.setData(str(dados))
                        conexao.close()
                        ix = self.model.indexFromItem(child)
                        ix_proxy = self.filter_proxy_model.mapFromSource(ix)
                        self.treLista.selectionModel().select(ix_proxy, QtCore.QItemSelectionModel.ClearAndSelect)
                        self.treLista.expand(ix_proxy)
                        self.treLista.expand(ix_proxy.parent())
                        # ############# DAQUI PRA BAIXO É A TENTATIVA DE INSERÇÃO A PARTIR DA CHILD
                    else:
                        parent_of_item = parent_item.parent()
                        child = QStandardItem(self.icon, self.novo.txtName.text())
                        parent_of_item.appendRow(child)
                        child_index = child.index()
                        conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
                        c = conexao.cursor()
                        comando = f"""
                                                            INSERT INTO child (icon, desc, rel_parent)
                                                            VALUES ('{self.iconpath}',
                                                            '{self.novo.txtName.text()}', '{parent_of_item.data()}')
                                                            """
                        c.execute(comando)
                        conexao.commit()
                        comando = 'SELECT max(idx) FROM child'
                        c.execute(comando)
                        dados = c.fetchone()[0]
                        child.setData(str(dados))
                        conexao.close()
                        ix = self.model.indexFromItem(child)
                        ix_proxy = self.filter_proxy_model.mapFromSource(ix)
                        self.treLista.selectionModel().select(ix_proxy, QtCore.QItemSelectionModel.ClearAndSelect)
                        self.treLista.expand(ix_proxy)
                        self.treLista.expand(ix_proxy.parent())

    def rename_branch(self):
        """
        Renomeia um galho da treeView. Pode ser tanto root quanto child.
        :return:
        """
        if self.iconpath != None:
            # for index in sorted(self.treeView.selectionModel().selectedRows()):
            selection = self.treLista.selectionModel().selectedRows()
            selection_x = [self.treLista.model().mapToSource(index) for index in selection]
            item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
            texto = item.text()
            statustip = int(item.data())
            newtext = self.rename.txtName.text()
            item.setIcon(self.icon)
            item.setText(self.rename.txtName.text())
            conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
            c = conexao.cursor()
            if item.parent() != None:
                # childstatustip = item.parent().data()
                comando = f"""
                            UPDATE child set icon = '{self.iconpath}', desc = '{newtext}'
                            WHERE idx = '{statustip}'
                            """
                c.execute(comando)
                conexao.commit()
                conexao.close()
            else:
                comando = f"""
                              UPDATE parent set icon = '{self.iconpath}', desc = '{newtext}'
                              WHERE idx = {statustip}
                              """
                c.execute(comando)
                conexao.commit()
                conexao.close()

    def delete_branch(self):
        """
        Apaga um galho da treeView. Pode ser tanto root quanto child.
        :return:
        """
        selection = self.treLista.selectionModel().selectedRows()
        selection_x = [self.treLista.model().mapToSource(index) for index in selection]
        item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
        statustip = item.data()
        statustip = int(statustip)
        if item.parent() != None:
            msgbox = QMessageBox()
            msgbox.setWindowTitle('Tem certeza?')
            msgbox.setText('Tem certeza que deseja apagar este registro?')
            sim = msgbox.addButton('Sim', QMessageBox.YesRole)
            msgbox.addButton('Não', QMessageBox.NoRole)
            msgbox.exec()
            if msgbox.clickedButton() == sim:
                item.parent().removeRow(selection_x[0].row())
                conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
                c = conexao.cursor()
                comando = f"""DELETE FROM contents WHERE rel_child = {statustip}"""
                c.execute(comando)
                conexao.commit()
                comando = f"""DELETE FROM child WHERE idx = {statustip}"""
                c.execute(comando)
                conexao.commit()
                conexao.close()
                self.txtEditor.setText('')
        else:
            if item.hasChildren():
                msgbox = QMessageBox()
                msgbox.setWindowTitle('Erro')
                msgbox.setText('Apague os registros associados a este antes de apagá-lo.')
                sim = msgbox.addButton('Ok', QMessageBox.YesRole)
                msgbox.exec()
            else:
                msgbox = QMessageBox()
                msgbox.setWindowTitle('Tem certeza?')
                msgbox.setText('Tem certeza que deseja apagar este registro?')
                sim = msgbox.addButton('Sim', QMessageBox.YesRole)
                msgbox.addButton('Não', QMessageBox.NoRole)
                msgbox.exec()
                if msgbox.clickedButton() == sim:
                    item.removeRow(selection_x[0].row())
                    self.model.removeRow(selection_x[0].row())
                    conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
                    c = conexao.cursor()
                    comando = f"""DELETE FROM parent WHERE idx = {statustip}"""
                    c.execute(comando)
                    conexao.commit()
                    conexao.close()
                    self.txtEditor.setText('')

    # #################################################################################
    # Função auxiliar das janelas de criação e de renomeio para ajustar o ícone
    # #################################################################################

    def set_icon(self, option):
        """
        Seta a variável que carrega o ícone na criação ou no renomeio de um branch.
        :param option:
        :return:
        """
        if option == 'python':
            self.iconpath = 'python.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'python.png'))
        elif option == 'code':
            self.iconpath = 'code_2.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'code_2.png'))
        elif option == 'asterisk':
            self.iconpath = 'asterisk.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'asterisk.png'))
        elif option == 'nota':
            self.iconpath = 'notesclip.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'notesclip.png'))
        elif option == 'check':
            self.iconpath = 'check.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'check.png'))
        elif option == 'pasta':
            self.iconpath = 'folder.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'folder.png'))
        elif option == 'linux':
            self.iconpath = 'linux.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'linux.png'))
        elif option == 'internet':
            self.iconpath = 'internet.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'internet.png'))
        elif option == 'windows':
            self.iconpath = 'windows.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'windows.png'))
        elif option == 'key':
            self.iconpath = 'key.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'key.png'))
        elif option == 'clip':
            self.iconpath = 'clip.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'clip.png'))
        elif option == 'disk':
            self.iconpath = 'disk.png'
            self.icon = QIcon(os.path.join(basedir, 'icons', 'disk.png'))

    # #################################################################################
    # Funções relacionadas ao banco de dados
    # #################################################################################


    def create_notebooks_db(self):
        """
        Cria o banco de dados que contém os nomes e endereços dos outros bancos de dados.
        :return:
        """
        conexao = sqlite3.connect(os.path.join(basedir, 'notebooks.db'))
        c = conexao.cursor()
        comando = """CREATE TABLE "notebooks" (
                            "idx"	INTEGER,
                            "icon"	TEXT,
                            "desc"	TEXT,
                            "address"	TEXT,
                            PRIMARY KEY("idx")
                            )"""
        c.execute(comando)
        conexao.commit()
        conexao.close()

    def open_notebooks_db(self):
        """
        Abre o arquivo de notebooks e popula a listWidget.
        :return:
        """
        if not os.path.exists(os.path.join(basedir, 'notebooks.db')):
            self.create_notebooks_db()
        conexao = sqlite3.connect(os.path.join(basedir, 'notebooks.db'))
        c = conexao.cursor()
        comando = """SELECT idx, icon, desc, address FROM notebooks"""
        c.execute(comando)
        resultado = c.fetchall()
        conexao.close()
        for idx, icon, desc, addr in resultado:
            self.desc = QListWidgetItem(self.listWidget)
            self.desc.setText(desc)
            self.desc.setIcon(QIcon(os.path.join(basedir, 'icons', icon)))
            self.desc.setData(3, addr)
            self.desc.setData(4, idx)
            # self.listWidget.addItem(desc)

    def notebook_click(self):
        """
        Abre o banco de dados quando é selecionado na listView.
        :return:
        """
        self.search_mode = True
        self.txtEditor.clear()
        self.txtEditor.setDisabled(True)
        # item = self.listWidget.selectedItems()
        # print(item)
        # print(item.index())

        if self.listWidget.currentRow() != -1:
            tmp = self.listWidget.currentItem().text()
            print(tmp)
            settings.setValue('lastnb', tmp)
            dbfile = self.listWidget.currentItem().data(3)
            print(dbfile)
            self.opening_database(dbfile)
            # self.db_file = dbfile
            print(self.listWidget.currentItem().data(4))
            self.search_mode = False



    def open_notebook_file(self):
        """
        *** ASSOCIADA AO BOTÃO ARQUIVO DA JANELA openb ***
        Pede o nome de um arquivo de notebook para abrir.
        :return:
        """
        fname, _ = QFileDialog.getOpenFileName(self.sender(), 'Abrir arquivo',
                                               '', "Nbook(*.nbook);;Todos os arquivos(*)")
        if not fname:
            return
        result = fname
        temp = basedir.replace('\\', '/')
        if temp in result:
            result = result.replace(temp, '')
            result = result.replace('/', '\\')
            result = result[1:]
            # print('result',result)
            # print('basedir + result', basedir + result)
        else:
            result = result.replace('/', '\\')
            # print('result', result)
        print('result (gravar na variavel:', result)
        print('quando unido com os:', os.path.join(basedir, result))
        # print(self.db_file)
        # self.open_file(result)
        # self.opening_database(result)
        self.open_db = result
        self.openb.txtArquivo.setText(result)

    def open_notebook(self):
        """
        *** ASSOCIADA AO BOTÃO CRIAR DA JANELA openb ***
        Pega o retorno da função open_notebook_file através da variável e insere os dados do notebook no
        banco de dados e na listView.
        :return: 
        """
        if self.iconpath != None:
            conexao = sqlite3.connect(os.path.join(basedir, 'notebooks.db'))
            c = conexao.cursor()
            comando = """INSERT INTO notebooks (icon, desc, address) VALUES (?, ?, ?)"""
            dados = (self.iconpath, self.openb.txtNome.text(), self.open_db)
            c.execute(comando, dados)
            conexao.commit()
            comando = 'SELECT max(idx) FROM notebooks'
            c.execute(comando)
            res = c.fetchone()[0]
            conexao.close()
            self.desc = QListWidgetItem(self.listWidget)
            self.desc.setText(self.openb.txtNome.text())
            self.desc.setIcon(QIcon(os.path.join(basedir, 'icons', self.iconpath)))
            self.desc.setData(3, self.open_db)
            self.desc.setData(4, res)
        else:
            msgbox = QMessageBox()
            msgbox.setWindowTitle('Atenção')
            msgbox.setText('Você não selecionou um ícone para o notebook.')
            sim = msgbox.addButton('Ok', QMessageBox.YesRole)
            msgbox.exec()

    def notebook_delete(self):
        """
        Retira um notebook da lista, sem apagar o arquivo.
        :return:
        """
        if self.listWidget.currentRow() != -1:
            tmp = self.listWidget.currentItem().data(4)
            print(tmp)
            conexao = sqlite3.connect(os.path.join(basedir, 'notebooks.db'))
            c = conexao.cursor()
            comando = """DELETE FROM notebooks WHERE idx = ?;"""
            c.execute(comando, (tmp,))
            conexao.commit()
            conexao.close()
            # self.listWidget.removeItemWidget(self.listWidget.currentItem())
            self.listWidget.takeItem(self.listWidget.currentRow())
            self.notebook_click()

    def new_database(self):
        """
        *** ASSOCIADA AO BOTÃO CRIAR DA JANELA nbook ***
        Função que atualiza o db de blocos de notas, e passa parâmetros para a função create_database.
        :return:
        """
        self.db_file = self.new_db
        settings.setValue('database', self.db_file)
        print('db_file askfornewdb', self.db_file)
        conexao = sqlite3.connect(os.path.join(basedir, 'notebooks.db'))
        c = conexao.cursor()
        comando = """INSERT INTO notebooks (icon, desc, address) VALUES (?, ?, ?)"""
        dados = (self.iconpath, self.nbook.txtNome.text(), self.new_db)
        c.execute(comando, dados)
        conexao.commit()
        comando = 'SELECT max(idx) FROM notebooks'
        c.execute(comando)
        res = c.fetchone()[0]
        conexao.close()
        self.desc = QListWidgetItem(self.listWidget)
        self.desc.setText(self.nbook.txtNome.text())
        self.desc.setIcon(QIcon(os.path.join(basedir, 'icons', self.iconpath)))
        self.desc.setData(3, self.new_db)
        self.desc.setData(4, res)
        self.create_database()

    def new_db_filechooser(self):
        """
        *** ASSOCIADA AO BOTÃO ARQUIVO DA JANELA nbook ***
        Função usada pela janela novo bloco de notas para escolher o nome do arquivo do novo bloco. Abre uma
        FileDialog e retorna o nome do arquivo, que vai para a variável self.new_db. Esta função não faz mais
        nada além disso. Depois dela é executada a função new_database, que adiciona o endereço do arquivo no
        banco de dados de blocos de notas, e passa os parâmetros para a função create_database que criará o
        novo bloco de notas.
        :return:
        """
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self.sender(),
                                                            "Novo arquivo",
                                                            "",
                                                            "Nbook(*.nbook)",
                                                            options=options)
        # "Banco de dados(*.db);;Text Files(*.txt)",
        if not fileName:
            # If dialog is cancelled, will return ''
            return

        result = fileName
        temp = basedir.replace('\\', '/')
        if temp in result:
            result = result.replace(temp, '')
            result = result.replace('/', '\\')
            result = result[1:]
            # print('result',result)
            # print('basedir + result', basedir + result)
        else:
            result = result.replace('/', '\\')
        print('result (gravar na variavel:', result)
        print('quando unido com os:', os.path.join(basedir, result))
        self.nbook.txtArquivo.setText(result)
        self.new_db = result

    def open_database(self):
        """
        Abre uma janela para pedir o nome do arquivo a ser aberto, e lida com as variáveis correspondentes.
        :return:
        """
        fname, _ = QFileDialog.getOpenFileName(self.sender(), 'Abrir arquivo',
                                            '', "Nbook(*.nbook);;Todos os arquivos(*)")
        if not fname:
            # If dialog is cancelled, will return ''
            return
        result = fname
        temp = basedir.replace('\\', '/')
        if temp in result:
            result = result.replace(temp, '')
            result = result.replace('/', '\\')
            result = result[1:]
            # print('result',result)
            # print('basedir + result', basedir + result)
        else:
            result = result.replace('/', '\\')
            # print('result', result)
        print('result (gravar na variavel:', result)
        print('quando unido com os:', os.path.join(basedir, result))
        # print(self.db_file)
        self.open_file(result)
        self.opening_database(result)

    def opening_database(self, filename):
        """
        Seta na variável self.db_file o arquivo que será aberto pela função read_database. Caso o arquivo
        não exista por algum motivo, dá uma mensagem de erro (e retira a referência do menu de arquivos
        abertos recentemente).
        :param filename:
        :return:
        """
        # Aqui abre o banco de dados que está setado na self.db_file.
        if os.path.exists(os.path.join(basedir, filename)):
            self.db_file = filename
            settings.setValue('database', self.db_file)
            print('Abrindo banco de dados...')
            # if filename == '' or filename == None:
                # usa a db_file
            self.setWindowTitle(f'NBooks ({self.db_file})')
            self.lblNbook.setText(self.listWidget.currentItem().data(2))
            print(self.db_file)
            print('filename', filename)
            self.read_database()
        else:
            self.remove_filename(filename)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setWindowIcon(QIcon(os.path.join(basedir, 'icons', 'icon.png')))
            msg.setText("Erro")
            msg.setInformativeText("Arquivo não encontrado.")
            msg.setWindowTitle("Erro")
            # msg.setDetailedText("The details are as follows:")
            msg.setStandardButtons(QMessageBox.Ok)  #  | QMessageBox.Cancel
            # msg.buttonClicked.connect(msgbtn)
            retval = msg.exec_()

    def ask_for_new_database(self):
        """
        Pede ao usuário o caminho e o nome de um novo banco de dados.
        :return:
        """
        options = QtWidgets.QFileDialog.Options()
        # options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self.sender(),
                                                            "Novo arquivo",
                                                            "",
                                                            "Nbook(*.nbook)",
                                                            options=options)
        # "Banco de dados(*.db);;Text Files(*.txt)",
        if not fileName:
            # If dialog is cancelled, will return ''
            return

        result = fileName
        temp = basedir.replace('\\', '/')
        if temp in result:
            result = result.replace(temp, '')
            result = result.replace('/', '\\')
            result = result[1:]
            # print('result',result)
            # print('basedir + result', basedir + result)
        else:
            result = result.replace('/', '\\')
        print('result (gravar na variavel:', result)
        print('quando unido com os:', os.path.join(basedir, result))

        self.db_file = result
        settings.setValue('database', self.db_file)
        print('db_file askfornewdb', self.db_file)
        self.create_database()

    def create_database(self):
        """
        Cria um banco de dados qtext vazio.
        :return:
        """
        conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
        c = conexao.cursor()
        comando = """CREATE TABLE "child" (
                    "idx"	INTEGER,
                    "icon"	TEXT,
                    "desc"	TEXT,
                    "rel_parent"	INTEGER,
                    "keywords"	TEXT,
                    PRIMARY KEY("idx")
                    )"""
        c.execute(comando)
        comando = """CREATE TABLE "parent" (
                    "idx"	INTEGER,
                    "icon"	TEXT,
                    "desc"	TEXT,
                    PRIMARY KEY("idx")
                    )"""
        c.execute(comando)
        comando = """CREATE TABLE "contents" (
                    "idx"	INTEGER,
                    "text"	TEXT,
                    "rel_child"	INTEGER,
                    PRIMARY KEY("idx")
                    )"""
        c.execute(comando)
        conexao.commit()
        conexao.close()
        self.read_database()

    def read_database(self):
        """
        Lê o banco de dados qtext atual e popula a árvore.
        :return:
        """
        if self.model != None:
            self.model.setRowCount(0)
        if not os.path.exists(os.path.join(basedir, 'db', 'database.nbook')):
            self.db_file = os.path.join('db', 'database.nbook')
            settings.setValue('database', self.db_file)
            self.create_database()
        if self.db_file == None or self.db_file == '':
            if os.path.exists(os.path.join(basedir, 'db', 'database.nbook')):
                self.db_file = os.path.join('db', 'database.nbook')
                settings.setValue('database', self.db_file)
            else:
                self.db_file = os.path.join('db', 'database.nbook')
                settings.setValue('database', self.db_file)
                self.create_database()
        self.setWindowTitle(f'NBooks ({self.db_file})')
        tmp = settings.value('lastnb', None)
        self.lblNbook.setText(tmp)
        print('read_database - listando de:', self.db_file)
        conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
        c = conexao.cursor()
        comando = """SELECT idx, icon, desc FROM parent"""
        c.execute(comando)
        parents = c.fetchall()
        comando = """SELECT idx, icon, desc, rel_parent, keywords FROM child"""
        c.execute(comando)
        children = c.fetchall()
        conexao.close()
        for index, icon, parent in parents:
            parent_item = QStandardItem(QIcon(os.path.join(basedir, 'icons', icon)), parent)
            self.model.appendRow(parent_item)
            parent_item.setData(str(index))
            for index2, icon2, child, relparent, keywords in children:
                if relparent == index:
                    if keywords:
                        apchild = QStandardItem(QIcon(os.path.join(basedir, 'icons', icon2)), child + ' (' + keywords + ')')
                    else:
                        apchild = QStandardItem(QIcon(os.path.join(basedir, 'icons', icon2)), child)
                    apchild.setData(index2)
                    parent_item.appendRow(apchild)

    # #################################################################################
    # Funções relacionadas ao textEdit
    # #################################################################################

    def read_content(self):
        """
        Lê o texto armazenado no banco de dados.
        :return:
        """
        childidx = None
        # self.txtKeywords.setText('')
        if not self.search_mode:
            self.clear_format()
            selection = self.treLista.selectionModel().selectedRows()
            selection_x = [self.treLista.model().mapToSource(index) for index in selection]
            item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
            if item.data() != None:
                childidx = int(item.data())
            if not item.hasChildren() and item.parent() != None and item.data() != None:
                self.txtEditor.setEnabled(True)
                conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
                c = conexao.cursor()
                comando = f"""SELECT text FROM contents WHERE rel_child = {childidx}"""
                c.execute(comando)
                resultado = c.fetchone()
                if resultado:
                    self.txtEditor.setText(resultado[0])
                    comando = f"""SELECT keywords FROM child WHERE idx = {childidx}"""
                    c.execute(comando)
                    kwords = c.fetchone()
                    # self.txtKeywords.setText(kwords[0])
                    # self.textEdit.setStatusTip(str(childidx))
                else:
                    self.txtEditor.clear()
                    # self.textEdit.setEnabled(False)
                conexao.close()
            else:
                self.txtEditor.clear()
                # self.txtKeywords.setText('')
                self.txtEditor.setEnabled(False)

    def save_current(self):
        """
        Salva o conteúdo do textEdit
        :return:
        """
        selection = self.treLista.selectionModel().selectedRows()
        selection_x = [self.treLista.model().mapToSource(index) for index in selection]
        item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
        childidx = int(item.data())
        text = self.txtEditor.toHtml()
        conexao = sqlite3.connect(os.path.join(basedir, self.db_file))
        c = conexao.cursor()
        comando = f"""SELECT text FROM contents WHERE rel_child = {childidx}"""
        c.execute(comando)
        conteudo = c.fetchone()
        if conteudo:
            comando = f"""UPDATE contents SET text = ? WHERE rel_child = {childidx}"""
            c.execute(comando, (text,))
            conexao.commit()
        else:
            comando = f"""INSERT INTO contents (text, rel_child) VALUES (?, {childidx})"""
            c.execute(comando, (text,))
            conexao.commit()
        # comando = f"""SELECT keywords FROM child WHERE idx = {childidx}"""
        # c.execute(comando)
        # conteudo = c.fetchone()
        # if conteudo:
        #     comando = f"""UPDATE child SET keywords = '{self.txtKeywords.text()}' WHERE idx = {childidx}"""
        #     c.execute(comando)
        #     conexao.commit()
        # else:
        #     comando = f"""INSERT INTO child (keywords)
        #     VALUES ('{self.txtKeywords.text()}') WHERE idx = {childidx}"""
        #     c.execute(comando)
        #     conexao.commit()
        conexao.close()
        self.statusbar.showMessage('Arquivo salvo.')

    def export_current(self):
        """
        Exporta o texto no textEdit.
        :return:
        """
        path, _ = QFileDialog.getSaveFileName(self, "Exportar como", "",
                                              "Documentos HTML (*.html);;"
                                              "Documentos de texto (*.txt);;Todos os arquivos (*.*)")
        if not path:
            return
        text = self.txtEditor.toHtml() if splitext(path) in HTML_EXTENSIONS else self.txtEditor.toPlainText()
        try:
            with open(path, 'w') as f:
                f.write(text)
        except Exception as e:
            self.dialog_critical(str(e))
        else:
            pass

    # #################################################################################
    # Funções relacionadas ao tema do aplicativo
    # #################################################################################

    def dark_mode(self):
        """
        Seta a paleta de cores para o modo escuro.
        :return:
        """
        theme = settings.setValue('theme', 'dark')
        self.setPalette(darkpalette)
        self.help.setPalette(darkpalette)
        self.buscar.setPalette(darkpalette)
        self.openb.setPalette(darkpalette)
        self.nbook.setPalette(darkpalette)
        self.rename.setPalette(darkpalette)
        self.novo.setPalette(darkpalette)

    def blue_mode(self):
        """
        Seta a paleta de cores para o modo azul.
        :return:
        """
        theme = settings.setValue('theme', 'blue')
        self.setPalette(bluepalette)
        self.help.setPalette(bluepalette)
        self.buscar.setPalette(bluepalette)
        self.openb.setPalette(bluepalette)
        self.nbook.setPalette(bluepalette)
        self.rename.setPalette(bluepalette)
        self.novo.setPalette(bluepalette)

    def light_mode(self):
        """
        Seta a paleta de cores para o modo claro.
        :return:
        """
        theme = settings.setValue('theme', 'light')
        self.setPalette(lightpalette)
        self.help.setPalette(lightpalette)
        self.buscar.setPalette(lightpalette)
        self.openb.setPalette(lightpalette)
        self.nbook.setPalette(lightpalette)
        self.rename.setPalette(lightpalette)
        self.novo.setPalette(lightpalette)

    def change_theme(self):
        """
        Ativada na inicialização, seta o tema a partir da configuração armazenada.
        :return:
        """
        theme = settings.value('theme', 'light')
        if theme == 'dark':
            self.setPalette(darkpalette)
        elif theme == 'blue':
            self.setPalette(bluepalette)
        else:
            self.setPalette(lightpalette)

    # #################################################################################
    # Função que alterna o tamanho da janela
    # #################################################################################

    def mini(self):
        """
        Diminui a janela do programa deixando apenas o textEdit, e mantendo a mesma no topo.
        :return:
        """
        frame_open = False
        if self.frmNbs.isVisible():
            msgbox = QMessageBox()
            msgbox.setWindowTitle('Atenção')
            msgbox.setText('Feche a aba blocos de notas.')
            sim = msgbox.addButton('Ok', QMessageBox.YesRole)
            msgbox.exec()
            frame_open = True
        if self.txtEditor.isEnabled() and not frame_open:
            if self.treLista.isVisible():
                self.frmLista.hide()
                self.lblNbook.hide()
                self.treLista.hide()
                self.toolbar_formatar.hide()
                self.toolbar_arquivo.hide()
                self.toolbar_editar.hide()
                self.btnNbs.hide()
                self.resize(200, 280)
                toggleTop()
            else:
                self.frmLista.show()
                self.lblNbook.show()
                self.treLista.show()
                self.toolbar_formatar.show()
                self.toolbar_arquivo.show()
                self.toolbar_editar.show()
                self.btnNbs.show()
                self.btnNbs.setIcon(QIcon(os.path.join(basedir, 'icons', 'forward.png')))
                self.resize(700, 580)
                # Move a janela para o centro da tela.
                qtRectangle = self.frameGeometry()
                centerPoint = QDesktopWidget().availableGeometry().center()
                qtRectangle.moveCenter(centerPoint)
                self.move(qtRectangle.topLeft())
                # ####################################
                toggleTop()

    def notebooks_list(self):
        if self.frmNbs.isVisible():
            self.frmNbs.hide()
            self.btnNbs.setIcon(QIcon(os.path.join(basedir, 'icons', 'forward.png')))
        else:
            self.frmNbs.show()
            self.btnNbs.setIcon(QIcon(os.path.join(basedir, 'icons', 'backward.png')))
        # if self.listWidget.isVisible():
        #     self.listWidget.hide()
        #     self.btnNovoNb.hide()
        #     self.btnAbrirNb.hide()
        #     self.btnRemoveNb.hide()
        #     # self.spc
        #
        # else:
        #     self.listWidget.show()
        #     self.btnNovoNb.show()
        #     self.btnAbrirNb.show()
        #     self.btnRemoveNb.show()

    # #################################################################################
    # Funções relacionadas ao ícone flutuante na área de trabalho
    # #################################################################################

    # def select_last(self):
    #     ix = settings.value('selected_index')
    #     print(ix)
    #     # Para recuperar o item
    #     # ix = self.model.indexFromItem(parent)
    #     if ix != None:
    #         ix_proxy = self.filter_proxy_model.mapFromSource(ix)
    #         self.treLista.selectionModel().select(ix_proxy, QtCore.QItemSelectionModel.ClearAndSelect)

    # def closeEvent(self, event):
    #     """
    #     Redefine o evento de fechamento do sistema.
    #     :param event:
    #     :return:
    #     """
    #     selection = self.treLista.selectionModel().selectedRows()
    #     selection_x = [self.treLista.model().mapToSource(index) for index in selection]
    #     if selection_x != []:
    #         # item = self.treLista.model().sourceModel().itemFromIndex(selection_x[0])
    #         settings.setValue('selected_index', selection_x[0])
    #
    #     # Para recuperar o item
    #     # ix = self.model.indexFromItem(parent)
    #     # ix_proxy = self.filter_proxy_model.mapFromSource(ix)
    #     # self.treLista.selectionModel().select(ix_proxy, QtCore.QItemSelectionModel.ClearAndSelect)
    #     # if self.isVisible():
    #     #     self.jan_irg()
    #     event.accept()

    def bubble(self):
        """
        Abre o ícone de área de trabalho no lugar da janela.
        :return:
        """
        if self.isVisible():
            self.jan_irg()
            self.hide()

    def start(self):
        """
        Define se é a primeira execução do sistema. Se for fecha a janela de ícone.
        :return:
        """
        if self.inicio:
            self.jan_irg()
            self.inicio = False

    def close_app(self):
        """
        Fecha o aplicativo de uma vez.
        :return:
        """
        app.exit(0)

if __name__ == '__main__':
    # import sys
    # app = QtWidgets.QApplication(sys.argv)
    # app.setStyle('Fusion')

    mainWin = MainWindow()


def toggleTop():
    """
    Alterna a janela como "sempre no topo".
    :return:
    """
    on = bool(mainWin.windowFlags() & Qt.WindowStaysOnTopHint)
    mainWin.setWindowFlag(Qt.WindowStaysOnTopHint, not on)
    mainWin.show()

mainWin.show()

sys.exit(app.exec_())