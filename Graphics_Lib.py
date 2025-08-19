'''
Here is a lib made by stu warren at PSI to take a 
list of components and generate a graphical representtion
of the beam line in question usign the vpython libs 
'''
import matplotlib.pyplot as plt
import sys
from vpython import *
import numpy as np

class Beam_Graphix():
        def __int__(self):
                self.fig = plt.figure()
                self.canv = canvas()
        def Draw_QP(self, QP = {}, Props = {'colour':color.blue,'alpha':0.9}):

                try:
                        poleRpos =QP['HalfApature']
                        PoleR = 1.147* poleRpos
                        poleLen =  QP['Len[m]']
                        #generte shape
                        Zloc = QP['Zpos']
                except:
                        print('QP paramiters are not set correct....check input')
                        return
                for i in range(4):
                        theta = (i/2)*pi + pi/4
                        x = (PoleR+poleRpos)*np.cos(theta)
                        y = (PoleR+poleRpos)*np.sin(theta)
                        extrusion(path=[vec(0, 0, Zloc), vec(0, 0, Zloc+poleLen)],
                                  color=Props['colour'],
                                  shape=[shapes.circle(radius=PoleR, angle1=0, angle2=pi/2)])


    
        