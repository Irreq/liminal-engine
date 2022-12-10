#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# File: utils.py
# Author: Irreq
# Date: 10/12-2022

import numpy as np
import matplotlib.pyplot as plt
import cv2

def create_darkness_mask():
    print("Generating darkness")
    X = 500
    Y = 500

    x_axis = np.linspace(-5, 5, X)[:, None]
    y_axis = np.linspace(-5, 5, Y)[None, :]


    times = 2
    arr = np.sqrt(x_axis ** times + y_axis ** times)

    arr = np.ones_like(arr) - arr

    arr -= arr.min()
    t = arr
    t **= 7

    t/= t.max()

    t = np.repeat(arr, 4).reshape((X, Y, 4))

    t[:,:,3] *= 255

    t[:,:,3] = 255 - t[:,:,3]

    plt.imshow(t, cmap="gray")
    file = "darkness.png"
    cv2.imwrite(file, t)
    print("Created: ", file)


if __name__ == "__main__":
    create_darkness_mask()
    