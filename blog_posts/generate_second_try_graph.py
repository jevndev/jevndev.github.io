import typing
import matplotlib.pyplot as plt
import matplotlib.axes
import matplotlib.colors

import numpy as np

white = np.array((245, 247, 255)) / 255
black = np.array([38, 44, 44]) / 255
grey = np.array([76, 77, 77]) / 255
green = np.array([75, 125, 78]) / 255
purple = np.array([142, 123, 147]) / 255


fig, ax = plt.subplots(1, 1)
ax = typing.cast(matplotlib.axes.Axes, ax)
fig.set_facecolor(white)
ax.set_facecolor(white)

x = np.arange(10)


ax.spines[["right", "top"]].set_visible(False)
ax.spines[["bottom", "left"]].set_color(black)
ax.yaxis.label.set_color(black)
ax.xaxis.label.set_color(black)
ax.plot(x, 2 ** (x.size - x), c=purple)
ax.set_yticks([])

ax.xaxis.label.set_fontsize("large")
ax.yaxis.label.set_fontsize("large")

ax.set(xlabel="Iteration of project", ylabel="Amount of benefit gained")

plt.show()
