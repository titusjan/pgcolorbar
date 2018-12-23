import numpy as np
import pyqtgraph as pg

lut1 = np.array([(0, 0, 0), (1, 1, 1), (2, 2, 2)])

vector = np.linspace(0.0, 1.0, 11)
data = np.expand_dims(vector, axis=0)
print("data: {}".format(data))

levels = np.amin(data), np.amax(data)

for scale in [None, 2, 3]:
    res, _ = pg.makeARGB(data, lut1, levels=levels, scale=scale)
    # print("scale={}, res (shape {}): \n{}".format(scale, res.shape, res))
    print("\nScale: {}".format(scale))
    for idx, val in enumerate(vector):
        color = res[0, idx, :]
        print("    Value {:5.2f} ->  RGBA {} ".format(val, color))



