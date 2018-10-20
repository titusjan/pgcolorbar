"""

"""

import logging
import sys
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

#from pghistlutitem import HistogramLUTItem
from pgcolorbar.colorlegend import ColorLegendItem

if 0:
    import pyqtgraph as pg
    temp = pg.HistogramLUTItem

import pyqtgraph as pg

LOG_FMT = '%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: pid=%(process)d: %(message)s'

logger = logging.getLogger(__name__)


class MyWindow(QtWidgets.QWidget):

    def __init__(self, img, lut, parent=None):
        super().__init__(parent=parent)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.plotItem = pg.PlotItem()

        viewBox = self.plotItem.getViewBox()
        viewBox.disableAutoRange(pg.ViewBox.XYAxes)

        self.imageItem = pg.ImageItem()
        self.plotItem.addItem(self.imageItem)

        nRows, nCols = img.shape
        self.imageItem.setImage(img.T) # PyQtGraph uses the following dimension order: T, X, Y, Color.

        # Duplicate last item because the pyqtgraph.makeARGB function has a wrong default scale. It
        # should be equal to the length of the LUT, but it's set to len(lut)-1. We therefore add a
        # fake LUT entry.
        extendedLut = np.append(lut, [lut[-1, :]], axis=0)
        self.imageItem.setLookupTable(extendedLut)

        self.plotItem.setRange(xRange=[0, nCols], yRange=[0, nRows])

        self.colorLegendItem = ColorLegendItem(lut=lut, imageItem=self.imageItem)
        self.colorLegendItem.setMinimumHeight(60)

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.graphicsLayoutWidget.addItem(self.plotItem, 0, 0)
        self.graphicsLayoutWidget.addItem(self.colorLegendItem, 0, 1)

        self.mainLayout.addWidget(self.graphicsLayoutWidget)

        self.resetAction = QtWidgets.QAction("reset", self)
        self.resetAction.triggered.connect(self.resetScale)
        self.resetAction.setShortcut("Ctrl+0")
        self.addAction(self.resetAction) # Needed to make it work without a button present

        # self.resetButton = QtWidgets.QToolButton()
        # self.resetButton.setDefaultAction(self.resetAction)
        # self.mainLayout.addWidget(self.resetButton)


    def resetScale(self):
        logger.debug("Reset scale")

        img = self.imageItem.image
        assert isinstance(img, np.ndarray)

        if 0:
            levels = (np.nanmin(img), np.nanmax(img))
        else:
            levels = (0.0, 1.0)
        self.colorLegendItem.setLevels(levels)



def main():

    app = QtWidgets.QApplication([])


    ## Create random 3D data set with noisy signals
    #img = pg.gaussianFilter(np.random.normal(size=(300, 200)), (5, 5)) * 20
    #img = np.random.normal(size=(300, 200)) * 100
    img = np.random.uniform(0.0, 1.0, size=(300, 300))
    img[200:250, :] = 0.1

    #cmap = pg.ColorMap([0, 0.25, 0.75, 1], [[0, 0, 0, 255], [255, 0, 0, 255], [255, 255, 0, 255], [255, 255, 255, 255]])
    #lut0 = cmap.getLookupTable()
    lut1 = np.array([(237,248,251), (178,226,226), (102,194,164), (35,139,69), (0, 0, 0)])
    lut2 = np.array([(237,248,251), (204,236,230), (153,216,201), (102,194,164),
                     (65,174,118), (35,139,69), (0,88,36)])


    if 0:
        lut1 = np.array([(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)])
        data = np.array([[0.0, 0.25], [0.9999, 1.0]])

        res = pg.makeARGB(data, lut1, levels=(0, 1), scale=3)
        logger.debug("scale=3, res: \n{}".format(res))

        res = pg.makeARGB(data, lut1, levels=(0, 1), scale=4)
        logger.debug("scale=4, res: \n{}".format(res))

        return




    ## Create window with ImageView widget
    win = MyWindow(img=img, lut=np.flipud(lut1))


    win.setGeometry(400, 100, 700, 600)
    win.setWindowTitle('pyqtgraph example: ImageView')
    win.show()


    QtWidgets.QApplication.instance().exec_()


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG', format=LOG_FMT)

    # Interpret image data as row-major instead of col-major
    #pg.setConfigOptions(imageAxisOrder='row-major')

    main()
