""" Demo program for the pgcolorbar module

    TODO:
        No image data
        Longer and transparent tick marks.
        Lines around color bar
        axis label next to color bar
    Done:
        setHistogram(bool)
        setData(array)
        setRange
        setLut(lut)
"""

import logging
import numpy as np

import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore
from pgcolorbar.colorlegend import ColorLegendItem

logger = logging.getLogger(__name__)


class ImageLevelsConfigWidget(QtWidgets.QWidget):
    """ Config widget with two spinboxes that control the image levels.
    """
    def __init__(self, colorLegendItem, label=None, parent=None):
        """ Constructor
        """
        super().__init__(parent=parent)

        self.colorLegendItem = colorLegendItem

        self.resetAction = QtWidgets.QAction("reset", self)
        self.resetAction.triggered.connect(self.colorLegendItem.resetColorLevels)
        self.resetAction.setShortcut("Ctrl+0")
        self.addAction(self.resetAction)

        self.toggleHistogramAction = QtWidgets.QAction("histogram", self)
        self.toggleHistogramAction.setCheckable(True)
        self.toggleHistogramAction.setChecked(self.colorLegendItem.histogramIsVisible)
        self.toggleHistogramAction.triggered.connect(self.colorLegendItem.showHistogram)
        self.toggleHistogramAction.setShortcut("Ctrl+S")
        self.addAction(self.toggleHistogramAction)

        self.mainLayout = QtWidgets.QHBoxLayout()
        self.mainLayout.setContentsMargins(5, 0, 5, 0) # left, top, right, bottom
        self.mainLayout.setSpacing(3)
        self.setLayout(self.mainLayout)

        if label is None:
            self.label = None
        else:
            self.label = QtWidgets.QLabel(label)
            self.mainLayout.addWidget(self.label)

        self.minLevelSpinBox = QtWidgets.QDoubleSpinBox()
        self.minLevelSpinBox.setKeyboardTracking(False)
        self.minLevelSpinBox.setMinimum(-10000)
        self.minLevelSpinBox.setMaximum(10000)
        self.minLevelSpinBox.setSingleStep(0.1)
        self.minLevelSpinBox.setDecimals(3)
        self.mainLayout.addWidget(self.minLevelSpinBox)

        self.maxLevelSpinBox = QtWidgets.QDoubleSpinBox()
        self.maxLevelSpinBox.setKeyboardTracking(False)
        self.maxLevelSpinBox.setMinimum(-10000)
        self.maxLevelSpinBox.setMaximum(10000)
        self.maxLevelSpinBox.setSingleStep(0.1)
        self.maxLevelSpinBox.setDecimals(3)
        self.mainLayout.addWidget(self.maxLevelSpinBox)

        self.minLevelSpinBox.valueChanged.connect(lambda val: self.setLevels((val, None)))
        self.maxLevelSpinBox.valueChanged.connect(lambda val: self.setLevels((None, val)))
        self.colorLegendItem.sigLevelsChanged.connect(self._updateSpinBoxLevels)

        self.resetButton = QtWidgets.QToolButton()
        self.resetButton.setDefaultAction(self.resetAction)
        self.mainLayout.addWidget(self.resetButton)

        self.histogramButton = QtWidgets.QToolButton()
        self.histogramButton.setDefaultAction(self.toggleHistogramAction)
        self.mainLayout.addWidget(self.histogramButton)



    def finalize(self):
        """ Should be called manually before object deletion
        """
        logger.debug("Finalizing: {}".format(self))
        super().finalize()


    def setLevels(self, levels):
        """ Sets plot levels
            :param levels: (vMin, vMax) tuple
        """
        logger.debug("Setting image levels: {}".format(levels))
        minLevel, maxLevel = levels

        # Replace Nones by the current level
        oldMin, oldMax = self.colorLegendItem.getLevels()
        logger.debug("Old levels: {}".format(levels))

        if minLevel is None: # Only maxLevel was set.
            minLevel = oldMin
            if maxLevel <= minLevel:
                minLevel = maxLevel - 1

        if maxLevel is None: # Only minLevel was set
            maxLevel = oldMax
            if maxLevel <= minLevel:
                maxLevel = minLevel + 1

        self.colorLegendItem.setLevels((minLevel, maxLevel))


    def _updateSpinBoxLevels(self, levels):
        """ Updates the spinboxes given the levels
        """
        minLevel, maxLevel = levels
        logger.debug("_updateSpinBoxLevels: {}".format(levels))
        self.minLevelSpinBox.setValue(minLevel)
        self.maxLevelSpinBox.setValue(maxLevel)




class DemoWindow(QtWidgets.QMainWindow):

    def __init__(self, lut, showHistogram, parent=None):
        super().__init__(parent=parent)

        self._setupActions()
        self._setupMenus()
        self._setupViews(lut, showHistogram)
        self._setDataToNoise()

        self.imgLevelsConfigWidget.toggleHistogramAction.setChecked(showHistogram)



    def _setupActions(self):
        """ Creates the UI actions.
        """
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

        self.viewMenu = self.menuBar.addMenu("&View")

        self.dataMenu = self.menuBar.addMenu("&Data")
        self.dataMenu.addAction(self.noiseImgAction)


    def _setupViews(self, lut, showHistogram):
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

        self.colorLegendItem = ColorLegendItem(
            imageItem=self.imageItem, showHistogram=showHistogram)
        self.colorLegendItem.setMinimumHeight(60)
        #self.colorLegendItem.setLut(lut)

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.graphicsLayoutWidget.addItem(self.plotItem, 0, 0)
        self.graphicsLayoutWidget.addItem(self.colorLegendItem, 0, 1)

        self.mainLayout.addWidget(self.graphicsLayoutWidget)

        # Toolbar
        self.imgToolBar = QtWidgets.QToolBar("Tool Bar", self)
        self.setObjectName("toolbar")
        self.imgToolBar.setFloatable(False)
        self.imgToolBar.setAllowedAreas(QtCore.Qt.TopToolBarArea | QtCore.Qt.BottomToolBarArea)

        self.imgLevelsConfigWidget = ImageLevelsConfigWidget(
            self.colorLegendItem, label="Color Range")
        self.imgToolBar.addWidget(self.imgLevelsConfigWidget)

        self.addToolBar(QtCore.Qt.TopToolBarArea, self.imgToolBar)
        self.viewMenu.addAction(self.imgToolBar.toggleViewAction())


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
    win = DemoWindow(lut=np.flipud(lut1), showHistogram=True)


    win.setGeometry(400, 100, 700, 600)
    win.setWindowTitle('pyqtgraph example: ImageView')
    win.show()


    QtWidgets.QApplication.instance().exec_()


if __name__ == '__main__':
    LOG_FMT = '%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: pid=%(process)d: %(message)s'
    logging.basicConfig(level='INFO', format=LOG_FMT)

    main()
