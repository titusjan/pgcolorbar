""" Reimplementation of the PyQtGraph HistogramLUTItem.

    Currently only a histogram range in the imageChanged method is added. This prevents errors when
    the image contains NaNs. Later the mouse and scrolling behaviour may be altered.
"""

import numpy as np
import pyqtgraph as pg


from pyqtgraph.Qt import  QtWidgets



class ColorLegendItem(pg.GraphicsWidget):
    """ Color legend for an image plot.
    """
    def __init__(self):
        """ Constructor.
        """
        pg.GraphicsWidget.__init__(self)

        self.layout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        #self.viewBox = ViewBox(enableMenu=False, border=pg.getConfigOption('foreground'))
        self.viewBox = pg.ViewBox(enableMenu=False)
        # self.viewBox.setBackgroundColor("666666")
        self.axis = pg.AxisItem('left', linkView=self.viewBox, maxTickLength=-10, parent=self)


        self.rectItem = QtWidgets.QGraphicsRectItem()
        self.rectItem.setBrush(pg.fn.mkBrush("FF0000"))
        self.rectItem.setPen(pg.fn.mkPen(color="FFFF00", width=1, cosmetic=True))
        self.rectItem.setParentItem(self.viewBox.background)
        self.rectItem.setRect(0, 0, 40, 10)
        #self.viewBox.addItem(rectItem)

        lut = np.array([(237,248,251), (178,226,226), (102,194,164), (35,139,69)])
        barWidth = 10
        lutImg = np.ones(shape=(len(lut), barWidth, 3), dtype=lut.dtype)
        lutImg[...] = lut[:, np.newaxis, :]

        colorScaleImageItem = pg.ImageItem()
        colorScaleImageItem.setImage(lutImg)
        #self.colorScaleViewBox = ViewBox(enableMenu=False)
        self.colorScaleViewBox = pg.ViewBox(enableMenu=False, border=pg.getConfigOption('foreground'))
        self.colorScaleViewBox.addItem(colorScaleImageItem)
        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)

        self.layout.addItem(self.axis, 0, 0)
        self.layout.addItem(self.colorScaleViewBox, 0, 1)
        self.layout.addItem(self.viewBox, 0, 2)

        self.colorScaleViewBox.setRange(xRange=[0, barWidth], yRange=[0, len(lut)], padding=0.0)
        print("viewRange: {}".format(self.colorScaleViewBox.viewRange()))

        plotDataItem = pg.PlotDataItem()
        plotDataItem.setData([5, 7, 12])
        self.viewBox.addItem(plotDataItem)


