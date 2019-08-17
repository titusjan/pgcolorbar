""" Program to reproduce the error due to PR 942 in PyQtGraph

    On exit it gives the following RuntimeError:
        wrapped C/C++ object of type GraphicsLayoutWidget has been deleted
"""
import sys
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
from PyQt5.Qt import PYQT_VERSION_STR


class DemoWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.mainWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.mainWidget)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)

        self.plotItem = pg.PlotItem()
        self.plotItem.plot([3.5, 5, -4, 0, 0, 3])

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.graphicsLayoutWidget.addItem(self.plotItem, 0, 0)

        self.mainLayout.addWidget(self.graphicsLayoutWidget)


def main():
    print(sys.version)
    print("PyQt version: {}".format(PYQT_VERSION_STR))
    print("PyQtGraph version: {}".format(pg.__version__))
    app = QtWidgets.QApplication([])
    win = DemoWindow()
    win.setGeometry(400, 100, 700, 600)
    win.show()
    app.exec()


if __name__ == '__main__':
    main()
