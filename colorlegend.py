""" Reimplementation of the PyQtGraph HistogramLUTItem.

    Currently only a histogram range in the imageChanged method is added. This prevents errors when
    the image contains NaNs. Later the mouse and scrolling behaviour may be altered.
"""

import numpy as np
import pyqtgraph as pg


from pyqtgraph.Qt import QtWidgets



class ColorLegendItem(pg.GraphicsWidget):
    """ Color legend for an image plot.
    """
    def __init__(self, lut, imageItem=None, barWidth=10):
        """ Constructor.
        """
        pg.GraphicsWidget.__init__(self)

        self.lut = lut
        self._imageItem = imageItem
        self.barWidth = barWidth
        self.histogramFilled = True

        # Histogram
        self.histViewBox = pg.ViewBox(enableMenu=False)
        self.histViewBox.setMouseEnabled(x=False, y=True)
        self.histPlotDataItem = pg.PlotDataItem()
        self.histPlotDataItem.rotate(-90)
        self.histViewBox.addItem(self.histPlotDataItem)
        self.fillHistogram(self.histogramFilled)

        # Axis
        self.layout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        self.axisItem = pg.AxisItem('left', linkView=self.histViewBox,
                                    maxTickLength=-10, parent=self)

        # Image
        lutImg = np.ones(shape=(len(lut), self.barWidth, 3), dtype=lut.dtype)
        lutImg[...] = lut[:, np.newaxis, :]

        colorScaleImageItem = pg.ImageItem()
        colorScaleImageItem.setImage(lutImg)
        self.colorScaleViewBox = pg.ViewBox(enableMenu=False,
                                            border=pg.getConfigOption('foreground'))
        self.colorScaleViewBox.addItem(colorScaleImageItem)
        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)
        self.colorScaleViewBox.setRange(xRange=[0, self.barWidth],
                                        yRange=[0, len(lut)],
                                        padding=0.0)

        self.layout.addItem(self.axisItem, 0, 0)
        self.layout.addItem(self.colorScaleViewBox, 0, 1)
        self.layout.addItem(self.histViewBox, 0, 2)

        self.histViewBox.sigYRangeChanged.connect(
            lambda _viewBox, range: self.setRange(range[0], range[1]))


        self.imageChanged(autoLevel=True)


    @property
    def imageItem(self):
        """ Returns the ImageItem that this legend is linked to.
        """
        return self._imageItem


    def setRange(self, rangeMin, rangeMax):
        """ Sets the value range of the legend
        """
        if self.imageItem is not None:
            print("setRange: {} {}".format(rangeMin, rangeMax))
            self.imageItem.setLevels((rangeMin, rangeMax))


    def axisChanging(self):
        """
        """
        if self.imageItem() is not None:
            self.imageItem().setLevels(self.region.getRegion())
        self.sigLevelsChanged.emit(self)
        self.update()


    def fillHistogram(self, fill=True, level=0.0, color=(100, 100, 200)):
        if fill:
            self.histPlotDataItem.setFillLevel(level)
            self.histPlotDataItem.setFillBrush(color)
        else:
            self.histPlotDataItem.setFillLevel(None)


    def imageChanged(self, autoLevel=False):

        img = self.imageItem.image
        if img is None:
            histRange = None
        else:
            histRange = (np.nanmin(img), np.nanmax(img))

        h = self.imageItem.getHistogram(range=histRange)
        if h[0] is None:
            return
        self.histPlotDataItem.setData(*h)

        # if autoLevel:
        #     mn = h[0][0]
        #     mx = h[0][-1]
        #     self.region.setRegion([mn, mx])
