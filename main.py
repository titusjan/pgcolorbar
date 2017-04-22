"""

"""
import sys
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui
import pyqtgraph as pg

def main():

    app = QtGui.QApplication([])

    ## Create window with ImageView widget
    win = QtGui.QMainWindow()
    win.resize(800,800)
    imv = pg.ImageView()
    win.setCentralWidget(imv)
    win.show()
    win.setWindowTitle('pyqtgraph example: ImageView')

    ## Create random 3D data set with noisy signals
    img = pg.gaussianFilter(np.random.normal(size=(200, 200)), (5, 5)) * 20 + 100
    img = img[np.newaxis,:,:]
    decay = np.exp(-np.linspace(0,0.3,100))[:,np.newaxis,np.newaxis]
    data = np.random.normal(size=(100, 200, 200))
    data += img * decay
    data += 2

    ## Add time-varying signal
    sig = np.zeros(data.shape[0])
    sig[30:] += np.exp(-np.linspace(1,10, 70))
    sig[40:] += np.exp(-np.linspace(1,10, 60))
    sig[70:] += np.exp(-np.linspace(1,10, 30))

    sig = sig[:,np.newaxis,np.newaxis] * 3
    data[:,50:60,30:40] += sig


    ## Display the data and assign each frame a time value from 1.0 to 3.0
    imv.setImage(data, xvals=np.linspace(1., 3., data.shape[0]))

    ## Set a custom color map
    colors = [
        (0, 0, 0),
        (45, 5, 61),
        (84, 42, 55),
        (150, 87, 60),
        (208, 171, 141),
        (255, 255, 255)
    ]
    cmap = pg.ColorMap(pos=np.linspace(0.0, 1.0, 6), color=colors)
    imv.setColorMap(cmap)

    QtGui.QApplication.instance().exec_()


if __name__ == '__main__':


    # Interpret image data as row-major instead of col-major
    pg.setConfigOptions(imageAxisOrder='row-major')

    main()
