# -*- coding: utf-8 -*-
""" Contains custom widgets """

import os
import time
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QRegExp, QSize
from PyQt5.QtWidgets import (QDialog, QLabel, QVBoxLayout, QHBoxLayout,
                             QPlainTextEdit, QToolBar, QMenuBar, QAction,
                             QDialogButtonBox, QFileDialog, QMessageBox)
from PyQt5.QtGui import (QPixmap, QMovie, QColor, QTextCharFormat, QFont,
                         QSyntaxHighlighter, QFontDatabase, QIcon)
from PyQt5.QtPrintSupport import QPrintDialog


class TicTimer():
    """ A very simple timer
        Usage : my_timer = TicTimer(tic=duration)
                my_timer.start(duration)
                if my_timer.is_finished():
                    do_something
    """
    start_time = 0
    tic_time = 0

    def __init__(self, tic=0):
        self.tic_time = tic

    def start(self, tic):
        if tic != 0:
            self.tic = tic
            self.start_time = time.perf_counter()

    def is_finished(self):
        if((time.perf_counter() - self.start_time) >= self.tic):
            return True
        return False


class SplashScreen(QDialog):
    """ Display a splashscreen
        usage : mysplash = SplashScreen(self, movie=a_movie, image=an_image,
            duration=some_time)
        notice that if a movie is specified, image won't be displayed
    """

    imgset = False
    movieset = False

    def __init__(self, parent=None, movie=None, image=None, duration=None):
        super(SplashScreen, self).__init__()
        self.movie = movie
        self.image = image
        self.duration = duration
        self.timer = QTimer()
        self.setupUI()
        self.setFixedSize(self.width(), self.height())

    def setupUI(self):
        """ init widgets """
        # set flags to display window on top without frame and title
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint
                            | Qt.WindowStaysOnTopHint)
        # create widgets and pack them on a vertical layout
        self.label = QLabel()
        self.textlabel = QLabel()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.textlabel)
        # if a valid image is specified
        if self.image is not None and self.image != '':
            self.pixmap = QPixmap(self.image)
            self.label.setPixmap(self.pixmap)
            self.resize(self.pixmap.width(), self.pixmap.height())
            self.imgset = True
        # if a valid movie is specified
        if self.movie is not None and self.movie != '':
            self.screenmovie = QMovie(self.movie)
            self.label.setMovie(self.screenmovie)
            self.movieset = True

    def start(self):
        """ show dialog """
        if self.movieset:
            self.startanimation()
        if self.duration is not None and self.duration != 0:
            self.timer.singleShot(self.duration, self.stop)
        self.show()

    def stop(self):
        """ close dialog """
        self.stopanimation()
        self.close()

    def startanimation(self):
        """ start movie """
        self.screenmovie.start()

    def stopanimation(self):
        """ stop movie """
        if self.movieset:
            self.screenmovie.stop()

    def setlabeltext(self, textline):
        """ set text on bottom of the dialog """
        self.textlabel.setText(textline)


class ClickableLabel(QLabel):
    """ A clickable label
        usage : mylabel=Label()
                mylabel.clicked.connect(mycallback)
                def mycallback(self):
                    ...
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super(Label, self).__init__()

    def mousePressEvent(self, event):
        """ emit signal if mouse is clicked """
        self.clicked.emit()


class EditorDialog(QDialog):
    """ Open a text editor
        Pass file name as an argument or use controls to load files
    """

    clicked = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(EditorDialog, self).__init__()

        layout = QVBoxLayout()
        toollayout = QHBoxLayout()
        self.editor = QPlainTextEdit() 
        # Setup the QTextEdit editor configuration
        fixedfont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        fixedfont.setPointSize(10)
        self.editor.setFont(fixedfont)
        self.highlighter = PythonHighlighter(self.editor.document())

        # self.path holds the path of the currently open file.
        # If none, we haven't got a file open yet (or creating new).
        self.path = None

        file_toolbar = QToolBar("File")
        file_toolbar.setIconSize(QSize(14, 14))
        toollayout.addWidget(file_toolbar)

        open_file_action = \
            QAction(QIcon(os.path.join('resources/images',
                    'blue-folder-open-document.png')), "Open file...", self)
        open_file_action.setStatusTip("Open file")
        open_file_action.triggered.connect(self.file_open)
        file_toolbar.addAction(open_file_action)

        save_file_action = QAction(QIcon(os.path.join('resources/images',
                                                      'disk.png')),
                                   "Save", self)
        save_file_action.setStatusTip("Save current page")
        save_file_action.triggered.connect(self.file_save)
        file_toolbar.addAction(save_file_action)

        saveas_file_action = QAction(QIcon(os.path.join('resources/images',
                                                        'disk--pencil.png')),
                                     "Save As...", self)
        saveas_file_action.setStatusTip("Save current page to specified file")
        saveas_file_action.triggered.connect(self.file_saveas)
        file_toolbar.addAction(saveas_file_action)

        print_action = QAction(QIcon(os.path.join('resources/images', 'printer.png')), "Print...", self)
        print_action.setStatusTip("Print current page")
        print_action.triggered.connect(self.file_print)
        file_toolbar.addAction(print_action)

        edit_toolbar = QToolBar("Edit")
        edit_toolbar.setIconSize(QSize(16, 16))
        toollayout.addWidget(edit_toolbar)

        undo_action = QAction(QIcon(os.path.join('resources/images', 'arrow-curve-180-left.png')), "Undo", self)
        undo_action.setStatusTip("Undo last change")
        undo_action.triggered.connect(self.editor.undo)

        redo_action = QAction(QIcon(os.path.join('resources/images', 'arrow-curve.png')), "Redo", self)
        redo_action.setStatusTip("Redo last change")
        redo_action.triggered.connect(self.editor.redo)
        edit_toolbar.addAction(redo_action)

        cut_action = QAction(QIcon(os.path.join('resources/images', 'scissors.png')), "Cut", self)
        cut_action.setStatusTip("Cut selected text")
        cut_action.triggered.connect(self.editor.cut)
        edit_toolbar.addAction(cut_action)

        copy_action = QAction(QIcon(os.path.join('resources/images', 'document-copy.png')), "Copy", self)
        copy_action.setStatusTip("Copy selected text")
        copy_action.triggered.connect(self.editor.copy)
        edit_toolbar.addAction(copy_action)

        paste_action = QAction(QIcon(os.path.join('resources/images', 'clipboard-paste-document-text.png')), "Paste", self)
        paste_action.setStatusTip("Paste from clipboard")
        paste_action.triggered.connect(self.editor.paste)
        edit_toolbar.addAction(paste_action)

        select_action = QAction(QIcon(os.path.join('resources/images', 'selection-input.png')), "Select all", self)
        select_action.setStatusTip("Select all text")
        select_action.triggered.connect(self.editor.selectAll)

        # ok , save and cancel buttons
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.onaccept)
        self.buttonBox.rejected.connect(self.onreject)

        self.update_title()
        self.setLayout(layout)
        layout.addLayout(toollayout)
        layout.addWidget(self.editor)
        layout.addWidget(self.buttonBox)
        layout.setAlignment(Qt.AlignBottom)
        self.setGeometry(200,200, 700, 500)
        # self.show()

    def onaccept(self):
        query = QMessageBox.question(self, 'Save file', "Save file before exit?",
                                     QMessageBox.Ok | QMessageBox.Cancel)
        if query == QMessageBox.Ok:
            self.file_save()
            self.clicked.emit(True)
        self.accept()

    def onreject(self):
        self.clicked.emit(False)
        self.reject()

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()

    def file_set(self, filename=None):
        if filename is not None and filename != '':
            self.path = filename
            if self.path:
                self.load_text()

    def load_text(self):
        if self.path:
            try:
                with open(self.path, 'r') as f:
                    text = f.read()

            except Exception as e:
                self.dialog_critical(str(e))

            else:
                self.editor.setPlainText(text)
                self.update_title()

    def file_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open file", "", "Text documents (*.txt);All files (*.*)")

        if path:
            self.path = path
            self.load_text()

    def file_save(self):
        if self.path is None:
            # If we do not have a path, we need to use Save As.
            return self.file_saveas()

        self._save_to_path(self.path)

    def file_saveas(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save file", "", "Text documents (*.txt);All files (*.*)")

        if not path:
            # If dialog is cancelled, will return ''
            return

        self._save_to_path(path)

    def _save_to_path(self, path):
        text = self.editor.toPlainText()
        try:
            with open(path, 'w') as f:
                f.write(text)

        except Exception as e:
            self.dialog_critical(str(e))

        else:
            self.path = path
            self.update_title()

    def file_print(self):
        dlg = QPrintDialog()
        if dlg.exec_():
            self.editor.print_(dlg.printer())

    def update_title(self):
        self.setWindowTitle("%s - Editor" % (os.path.basename(self.path) if self.path else "Untitled"))

    def edit_toggle_wrap(self):
        self.editor.setLineWrapMode( 1 if self.editor.lineWrapMode() == 0 else 0 )


def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue'),
    'operator': format('red'),
    'brace': format('darkGreen'),
    'defclass': format('black', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('darkGray', 'italic'),
    'self': format('black', 'italic'),
    'numbers': format('brown'),
}


class PythonHighlighter (QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False', 'with', 'open'
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
            for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
            for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
            for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]


    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)


    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
