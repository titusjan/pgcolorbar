""" Demo program for the pgcolorbar module

    TODO:
        setData(array)
        setRange
        setHistogram(bool)
        setLut(lut)
"""

import logging
import numpy as np

import pyqtgraph as pg

from pyqtgraph.Qt import QtWidgets

from pgcolorbar.colorlegend import ColorLegendItem



logger = logging.getLogger(__name__)


class MyWindow(QtWidgets.QMainWindow):

    def __init__(self, lut, parent=None):
        super().__init__(parent=parent)

        self._setupActions()
        self._setupMenus()
        self._setupViews(lut)


    def _setupActions(self):
        """ Creates the UI actions.
        """
        self.resetAction = QtWidgets.QAction("reset", self)
        self.resetAction.triggered.connect(self.resetScale)
        self.resetAction.setShortcut("Ctrl+0")
        self.addAction(self.resetAction)

        self.noiseImgAction = QtWidgets.QAction("Noise", self)
        self.noiseImgAction.setToolTip("Sets the image data to noise.")
        self.noiseImgAction.triggered.connect(self._setDataToNoise)
        self.noiseImgAction.setShortcut("Ctrl+N")
        self.addAction(self.noiseImgAction)

        self.myTestAction = QtWidgets.QAction("My Test", self)
        self.myTestAction.setToolTip("My test")
        self.myTestAction.triggered.connect(self.myTest)
        self.myTestAction.setShortcut("Ctrl+T")
        self.addAction(self.myTestAction)


    def _setupMenus(self):
        """ Sets up the menus.
        """
        self.menuBar = QtWidgets.QMenuBar() # Make a menu without parent.
        self.setMenuBar(self.menuBar)

        self.dataMenu = self.menuBar.addMenu("&Data")
        self.dataMenu.addAction(self.noiseImgAction)



    def _setupViews(self, lut):
        """ Creates the UI widgets.
        """
        self.mainWidget = QtWidgets.QWidget()
        self.setCentralWidget(self.mainWidget)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.mainWidget.setLayout(self.mainLayout)

        self.plotItem = pg.PlotItem()

        viewBox = self.plotItem.getViewBox()
        viewBox.disableAutoRange(pg.ViewBox.XYAxes)

        self.imageItem = pg.ImageItem()
        self.imageItem.setLookupTable(lut)
        self.plotItem.addItem(self.imageItem)

        self.colorLegendItem = ColorLegendItem(lut=lut, imageItem=self.imageItem)
        self.colorLegendItem.setMinimumHeight(60)
        #self.colorLegendItem.setLut(lut) # It doesn't work when this is not set.

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.graphicsLayoutWidget.addItem(self.plotItem, 0, 0)
        self.graphicsLayoutWidget.addItem(self.colorLegendItem, 0, 1)

        self.mainLayout.addWidget(self.graphicsLayoutWidget)

        self._setDataToNoise()


    def resetScale(self):
        logger.debug("Reset scale")

        img = self.imageItem.image
        assert isinstance(img, np.ndarray)

        if 0:
            levels = (np.nanmin(img), np.nanmax(img))
        else:
            levels = (0.0, 1.0)
        self.colorLegendItem.setLevels(levels)


    def setImage(self, img):
        """ Sets the image data
        """
        # PyQtGraph uses the following dimension order: T, X, Y, Color.
        self.imageItem.setImage(img.T)
        nRows, nCols = img.shape
        self.plotItem.setRange(xRange=[0, nCols], yRange=[0, nRows])


    def _setDataToNoise(self):
        """ Sets image data to noise
        """
        logger.debug("_setDataToNoise")
        ## Create random 3D data set with noisy signals
        #img = pg.gaussianFilter(np.random.normal(size=(300, 200)), (5, 5)) * 20
        #img = np.random.normal(size=(300, 200)) * 100
        maxVal = 1.0
        img = np.random.uniform(0.0, 1.0, size=(300, 300)) * maxVal
        img[200:205, :] = maxVal
        self.setImage(img)


    def myTest(self):

        logger.info("myTest called")
        self.colorLegendItem.colorScaleViewBox.setRange(
            xRange=[0, 1], yRange=[0,5], padding=0.0)


def main():

    app = QtWidgets.QApplication([])

    #cmap = pg.ColorMap([0, 0.25, 0.75, 1], [[0, 0, 0, 255], [255, 0, 0, 255], [255, 255, 0, 255], [255, 255, 255, 255]])
    #lut0 = cmap.getLookupTable()
    lut1 = np.array([(237,248,251), (178,226,226), (102,194,164), (35,139,69), (0, 0, 0)])
    lut2 = np.array([(237,248,251), (204,236,230), (153,216,201), (102,194,164),
                     (65,174,118), (35,139,69), (0,88,36)])

    # if 0:
    #     lut1 = np.array([(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)])
    #     data = np.array([[0.0, 0.25], [0.9999, 1.0]])
    #     logger.debug("data: {}".format(data.shape))
    #
    #     res, hasAlpha = pg.makeARGB(data, lut1, levels=(0, 1), scale=3)
    #
    #     logger.debug("scale=3, res (shape={}): \n{}".format(res.shape, res))
    #
    #     res, hasAlpha = pg.makeARGB(data, lut1, levels=(0, 1), scale=4)
    #     logger.debug("scale=4, res (shape={}): \n{}".format(res.shape, res))
    #
    #     return

    ## Create window with ImageView widget
    win = MyWindow(lut=np.flipud(lut1))


    win.setGeometry(400, 100, 700, 600)
    win.setWindowTitle('pyqtgraph example: ImageView')
    win.show()


    QtWidgets.QApplication.instance().exec_()


if __name__ == '__main__':
    LOG_FMT = '%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: pid=%(process)d: %(message)s'
    logging.basicConfig(level='INFO', format=LOG_FMT)

    main()
