#
# editor.py
# 
# Copyright (C) 2021 Till Harbaum <till@harbaum.org>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import sys, os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# Python highlighting
# https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting

class PythonHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
       """

    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
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
       
    def __init__( self, parent):
        QSyntaxHighlighter.__init__( self, parent )

        # Syntax styles that can be shared by all languages
        STYLES = {
            'keyword': PythonHighlighter.format('darkBlue'),
            'operator': PythonHighlighter.format('darkRed'),
            'brace': PythonHighlighter.format('#404040'),
            'defclass': PythonHighlighter.format('darkcyan'),
            'string': PythonHighlighter.format('darkMagenta'),
            'comment': PythonHighlighter.format('darkRed'),
            'self': PythonHighlighter.format('black', 'italic'),
            'numbers': PythonHighlighter.format('darkGreen'),
        }
    
        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string'])
  
        # Python keywords
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
  
            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
            
            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),  
        ]
  
        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]
    
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
 
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return Qsize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    run = pyqtSignal(str, str)
    save = pyqtSignal(str, str)
    stop = pyqtSignal()
    modified = pyqtSignal(str, bool)
    
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.code = ""
        self.error = None
        self.lineNumberArea = LineNumberArea(self)
        self.setMouseTracking(True)
        
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        
        self.updateLineNumberAreaWidth(0)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        font = QFont("Mono", 10)
        font.setStyleHint(QFont.Monospace);
        font.setFixedPitch(True)
        self.setFont(font)

        self.highlighter = PythonHighlighter(self.document())

        # overlay run button
        self.btn_run = QPushButton(QIcon(self.resource_path("assets/editor_run.svg")), "", self)
        self.btn_run.setIconSize(QSize(32,32));
        self.btn_run.setFlat(True)
        self.btn_run.resize(32, 32)
        self.btn_run.setStyleSheet("background-color: rgba(255, 255, 255, 0);");
        self.btn_run.pressed.connect(self.on_run)
        
        # overlay save button
        self.btn_save = QPushButton(QIcon(self.resource_path("assets/editor_save.svg")), "", self)
        self.btn_save.setIconSize(QSize(32,32));
        self.btn_save.setFlat(True)
        self.btn_save.resize(32, 32)
        self.btn_save.setStyleSheet("background-color: rgba(255, 255, 255, 0);");
        self.btn_save.pressed.connect(self.on_save)
        self.btn_save.setToolTip(self.tr("Save this code") + " (CTRL-S)");
        self.btn_save.setHidden(True)
        
        self.set_button_mode(True)

        # some extra keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.on_save)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.on_run)

        # start a timer to track modifications at a low rate of max 10Hz to
        # reduce work load a little bit
        self.timer = None
        self.code_is_modified = False
        self.textChanged.connect(self.on_edit)

    def isModified(self):
        return self.code_is_modified
        
    def checkModified(self):
        return self.text() != self.code
        
    def on_edit(self):
        # check for text change
        if self.timer is None:
            self.timer = QTimer(self)
            self.timer.singleShot(100, self.on_timer)

    def on_timer(self):
        self.timer = None
        m = self.checkModified()
        if m != self.code_is_modified:
            self.updateModifyState(m)

    def updateModifyState(self, m):
        self.code_is_modified = m
        self.modified.emit(self.name, m)

        # the user may be editing the file while it's running and while
        # the board is busy.
        if self.button_mode:
            self.btn_save.setHidden(not m)
        
        # if edited clear any error highlight
        if m: self.highlight(None)        
            
    def setCode(self, code):
        self.code = code   # save code

        if code is not None:        
            # the editor works internally with \n only
            code = code.replace('\r', '')        
            self.setPlainText(code)
        
    def set_button_mode(self, mode):
        # True = run, False = stop, None = disabled
        self.button_mode = mode
        if mode == True:
            self.btn_run.setHidden(False)
            self.btn_run.setIcon(QIcon(self.resource_path("assets/editor_run.svg")))
            self.btn_run.setToolTip(self.tr("Run this code") + " (CTRL-R)");
            self.btn_save.setHidden(not self.checkModified())
        elif mode == False:
            self.btn_run.setHidden(False)
            self.btn_run.setIcon(QIcon(self.resource_path("assets/editor_stop.svg")))
            self.btn_run.setToolTip(self.tr("Stop running code") + " (CTRL-R)");
            self.btn_save.setHidden(True)  # cannot save while running
        else:
            self.btn_run.setHidden(True)
            self.btn_save.setHidden(True)

    def event(self, event):
        if self.error is not None and event.type() == QEvent.ToolTip:
            if self.cursorForPosition(event.pos()).blockNumber() == self.error["line"]:
                QToolTip.showText(event.globalPos(), self.error["msg"]);
            else:
                QToolTip.hideText();
                
            return True

        return QPlainTextEdit.event(self, event)

    def on_save(self):
        # only really emit this signal if the save button is enabled
        if self.btn_save.isVisible():        
            self.save.emit(self.name, self.text())
        
    def on_run(self):
        if self.btn_run.isVisible():        
            if self.button_mode == True:
                self.run.emit(self.name, self.text())
            elif self.button_mode == False:
                self.stop.emit()

    def resource_path(self, relative_path):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
   
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            self.textCursor().insertText(" " * (4 - self.textCursor().columnNumber() % 4))
            event.accept()
        else:
            QPlainTextEdit.keyPressEvent(self, event )

    def lineNumberAreaWidth(self):
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count /= 10
            digits += 1
            
        space = 3 + self.fontMetrics().width('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)


    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(),
                                       rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)


    def resizeEvent(self, event):
        super().resizeEvent(event)

        # relocate the run and save icons
        self.btn_run.move(QPoint(self.width()-56, self.height()-56))
        self.btn_save.move(QPoint(self.width()-100, self.height()-56))
        
        cr = self.contentsRect();
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(),
                     self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(Qt.lightGray).lighter(120))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Just to make sure we use the right font
        height = self.fontMetrics().height()
        while block.isValid() and (top <= event.rect().bottom()):
            if block.isVisible() and (bottom >= event.rect().top()):
                number = str(blockNumber + 1)
                painter.setPen(Qt.black)
                painter.drawText(0, top, self.lineNumberArea.width()-2, height,
                                 Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def text(self):
        return self.toPlainText()

    def rename(self, new):
        self.name = new
        
    def saved(self):
        # the current code has been saved. So it becomes the
        # unmodified one
        self.code = self.text()
        self.updateModifyState(False)
    
    def highlight(self, line, msg = None):
        self.error = None
        
        if line is None:
            self.setExtraSelections([])
            return

        block = self.document().findBlockByLineNumber(line)
        blockPos = block.position()

        selection = QTextEdit.ExtraSelection()
        
        # highlight formatting
        selection.format = QTextCharFormat()
        selection.format.setBackground(QColor(Qt.red).lighter(180))
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        if msg:
            # setToolTip does not work. So we store the error and handle it explicitely
            # selection.format.setToolTip(msg)
            self.error = { "line": line, "msg": msg }        

        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        selection.cursor.setPosition(blockPos)
        selection.cursor.select(QTextCursor.LineUnderCursor);
        selection.cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor) 
        
        self.setExtraSelections([selection])
