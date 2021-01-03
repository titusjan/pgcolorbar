""" Demo program for the pgcolorbar module
"""
from __future__ import print_function, division

import logging
import sys

import numpy as np
import pyqtgraph as pg

from pgcolorbar.bindings import QtWidgets, QtCore
from pgcolorbar.colorlegend import ColorLegendItem

logger = logging.getLogger(__name__)
logger.setLevel('INFO')

class ImageLevelsConfigWidget(QtWidgets.QWidget):
    """ Config widget with two spinboxes that control the image levels.
    """
    def __init__(self, colorLegendItem, label=None, parent=None):
        """ Constructor
        """
        super(ImageLevelsConfigWidget, self).__init__(parent=parent)

        self.colorLegendItem = colorLegendItem
        self.colorLegendItem.setEdgeMargins(50) # add some space for user to drag edges

        self.resetAction = QtWidgets.QAction("reset", self)
        self.resetAction.triggered.connect(self.colorLegendItem.autoScaleFromImage)
        self.resetAction.setShortcut("Ctrl+0")
        self.addAction(self.resetAction)

        self.toggleHistogramAction = QtWidgets.QAction("histogram", self)
        self.toggleHistogramAction.setCheckable(True)
        self.toggleHistogramAction.setChecked(self.colorLegendItem.histogramIsVisible)
        self.toggleHistogramAction.triggered.connect(self.colorLegendItem.showHistogram)
        self.toggleHistogramAction.setShortcut("Ctrl+H")
        self.addAction(self.toggleHistogramAction)

        self.toggleDragLinesAction = QtWidgets.QAction("drag lines", self)
        self.toggleDragLinesAction.setCheckable(True)
        self.toggleDragLinesAction.setChecked(bool(self.colorLegendItem.edgePen))
        self.toggleDragLinesAction.triggered.connect(self.colorLegendItem.showDragLines)
        self.addAction(self.toggleDragLinesAction)

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

        try:
            self.minLevelSpinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
            self.maxLevelSpinBox.setStepType(QtWidgets.QAbstractSpinBox.AdaptiveDecimalStepType)
        except AttributeError:
            logger.warning("Unable to QSpinBox.setStepType (only available in Qt 5.12 and later")


        self.minLevelSpinBox.valueChanged.connect(lambda val: self.setLevels((val, None)))
        self.maxLevelSpinBox.valueChanged.connect(lambda val: self.setLevels((None, val)))
        self.colorLegendItem.sigLevelsChanged.connect(self._updateSpinBoxLevels)

        self.resetButton = QtWidgets.QToolButton()
        self.resetButton.setDefaultAction(self.resetAction)
        self.mainLayout.addWidget(self.resetButton)

        self.histogramButton = QtWidgets.QToolButton()
        self.histogramButton.setDefaultAction(self.toggleHistogramAction)
        self.mainLayout.addWidget(self.histogramButton)

        self.dragLinesButton = QtWidgets.QToolButton()
        self.dragLinesButton.setDefaultAction(self.toggleDragLinesAction)
        self.mainLayout.addWidget(self.dragLinesButton)



    def finalize(self):
        """ Should be called manually before object deletion
        """
        logger.debug("Finalizing: {}".format(self))
        super(ImageLevelsConfigWidget, self).finalize()


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
        super(DemoWindow, self).__init__(parent=parent)

        self._setupActions()
        self._setupMenus()
        self._setupViews(lut, showHistogram)
        self._setDataToNoise()

        self.imgLevelsConfigWidget.toggleHistogramAction.setChecked(showHistogram)


    def _setupActions(self):
        """ Creates the UI actions.
        """
        self.clearImgAction = QtWidgets.QAction("Clear", self)
        self.clearImgAction.setToolTip("Removes all image data")
        self.clearImgAction.triggered.connect(self.clearImage)
        self.clearImgAction.setShortcut("Ctrl+C")
        self.addAction(self.clearImgAction)

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
        self.dataMenu.addAction(self.clearImgAction)
        self.dataMenu.addAction(self.noiseImgAction)
        #self.dataMenu.addAction(self.myTestAction)


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
            imageItem=self.imageItem,
            showHistogram=showHistogram,
            #histHeightPercentile=99.0, # Uncomment to discard the outliers in the histogram height
            label='Random data')
        self.colorLegendItem.setMinimumHeight(60)

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


    def clearImage(self):
        """ Removes the image data
        """
        self.imageItem.clear()

        # Unfortunately PyQtGraph doesn't emit this signal when the image is cleared.
        self.imageItem.sigImageChanged.emit()


    def setImage(self, img):
        """ Sets the image data
        """
        # PyQtGraph uses the following dimension order: T, X, Y, Color.
        self.imageItem.setImage(img.T)
        nRows, nCols = img.shape
        self.plotItem.setRange(xRange=[0, nCols], yRange=[0, nRows])
        self.colorLegendItem.autoScaleFromImage()


    def _setDataToNoise(self):
        """ Sets image data to noise
        """
        logger.debug("_setDataToNoise")

        # img = np.random.randint(100, 150, size=(1216, 1936), dtype=np.uint16)
        img = pg.gaussianFilter(np.random.normal(size=(300, 200)), (5, 5)) * 20
        # img = np.random.normal(size=(300, 200)) * 100

        # Add rectangle with outliers to demonstrate the histHeightPercentile parameter
        img[15:45, 25:75] = 2.5

        # For testing issue 792
        # maxVal = 1.0
        # img = np.random.uniform(0.0, 1.0, size=(300, 300)) * maxVal
        # img[200:205, :] = maxVal

        self.setImage(img)


    def myTest(self):

        logger.info("myTest called")
        self.colorLegendItem.colorScaleViewBox.setRange(
            xRange=[0, 1], yRange=[0,5], padding=0.0)


def main():

    logger.info("Python executable: {}".format(sys.executable))
    logger.info("Python version: {}".format(sys.version))
    logger.info("PyQt bindings: {}".format(pg.Qt.QT_LIB))
    logger.info("Qt version: {}".format(pg.QtCore.QT_VERSION_STR))
    logger.info("PyQtGraph version: {}".format(pg.__version__))

    app = QtWidgets.QApplication([])


    cmap = pg.ColorMap([0, 0.25, 0.75, 1], [[0, 0, 0, 255], [255, 0, 0, 255], [255, 255, 0, 255], [255, 255, 255, 255]])
    lut0 = cmap.getLookupTable()
    lut1 = np.array([(237,248,251), (178,226,226), (102,194,164), (35,139,69), (0, 0, 0)])
    lut2 = np.array([(237,248,251), (204,236,230), (153,216,201), (102,194,164),
                     (65,174,118), (35,139,69), (0,88,36)])

    lut = lut1.astype(np.uint8) # Use uint8 so that the resulting image will also be of that type/
    lut = np.flipud(lut) # test reversed map
    win = DemoWindow(lut=lut, showHistogram=True)
    win.setGeometry(400, 100, 700, 600)
    win.setWindowTitle('PgColorbar Demo')
    win.show()
    app.exec_()


if __name__ == '__main__':
    LOG_FMT = '%(asctime)s %(filename)20s:%(lineno)-4d : %(levelname)-7s: %(message)s'
    logging.basicConfig(level='DEBUG', format=LOG_FMT)

    main()
