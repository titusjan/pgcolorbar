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


        self.layout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        #self.histViewBox = ViewBox(enableMenu=False, border=pg.getConfigOption('foreground'))
        self.histViewBox = pg.ViewBox(enableMenu=False) # TODO
        # self.histViewBox.setBackgroundColor("666666")
        self.axisItem = pg.AxisItem('left', linkView=self.histViewBox, maxTickLength=-10, parent=self)

        # Test rectangle.
        self.rectItem = QtWidgets.QGraphicsRectItem()
        self.rectItem.setBrush(pg.fn.mkBrush("FF0000"))
        self.rectItem.setPen(pg.fn.mkPen(color="FFFF00", width=1, cosmetic=True))
        self.rectItem.setParentItem(self.histViewBox.background)
        self.rectItem.setRect(0, 0, 40, 10)
        self.histViewBox.addItem(self.rectItem)

        lutImg = np.ones(shape=(len(lut), self.barWidth, 3), dtype=lut.dtype)
        lutImg[...] = lut[:, np.newaxis, :]

        colorScaleImageItem = pg.ImageItem()
        colorScaleImageItem.setImage(lutImg)
        #self.colorScaleViewBox = ViewBox(enableMenu=False)
        self.colorScaleViewBox = pg.ViewBox(enableMenu=False, border=pg.getConfigOption('foreground'))
        self.colorScaleViewBox.addItem(colorScaleImageItem)
        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)

        self.layout.addItem(self.axisItem, 0, 0)
        self.layout.addItem(self.colorScaleViewBox, 0, 1)
        self.layout.addItem(self.histViewBox, 0, 2)

        self.colorScaleViewBox.setRange(xRange=[0, self.barWidth], yRange=[0, len(lut)], padding=0.0)
        print("viewRange: {}".format(self.colorScaleViewBox.viewRange()))

        plotDataItem = pg.PlotDataItem()
        plotDataItem.setData([5, 7, 12])
        self.histViewBox.addItem(plotDataItem)


        self.histViewBox.sigYRangeChanged.connect(
            lambda _viewBox, range: self.setRange(range[0], range[1]))


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

