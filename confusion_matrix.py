import numpy as np
import matplotlib.pyplot as plt


def get_confusion_matrix(filename, confusion_matrix, class_labels):
    assert np.array(class_labels).shape[0] == np.array(confusion_matrix).shape[0], "Labels don't match confusion " \
                                                                                   "matrix shape. "
    norm_conf = []
    for i in confusion_matrix:
        a = 0
        tmp_arr = []
        a = sum(i, 0)
        for j in i:
            tmp_arr.append(float(j) / float(a))
        norm_conf.append(tmp_arr)

    fig = plt.figure()
    plt.clf()
    ax = fig.add_subplot(111)
    ax.set_aspect(1)
    res = ax.imshow(np.array(norm_conf), cmap=plt.cm.jet,
                    interpolation='nearest')

    width, height = confusion_matrix.shape

    for x in xrange(width):
        for y in xrange(height):
            ax.annotate(str(confusion_matrix[x][y]), xy=(y, x),
                        horizontalalignment='center',
                        verticalalignment='center')

    cb = fig.colorbar(res)
    plt.xticks(range(width), class_labels[:width])
    plt.yticks(range(height), class_labels[:height])
    plt.savefig(filename)