# encoding: utf-8
import matplotlib as mpl
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import time
from datetime import datetime
import pandas
import numpy as np
#the style of matplotlib.pyplot
plt.style.use('ggplot')
#用来正常显示中文标签
mpl.rcParams['font.sans-serif'] = ['SimHei']
#用来正常显示负号
mpl.rcParams['axes.unicode_minus'] = False
#设置坐标轴刻度显示大小
mpl.rc('xtick', labelsize=12)
mpl.rc('ytick', labelsize=12)

#the interval of the x axes
SCALE_INTERVAL = "1min"
#the scale of the axis
SCALE_Y = 100
#the interval of painting the figure
PAINTING_INTERVAL = 1 * 1000
#the start of the y axes
START_Y = -5
#the interval of tick and tick
TICK_INTERVAL = 60
#label of the figure
LABLE_LINE = u'最高请求量-%d'
#tile of the mearchat website
TITLE = u"官网实时请求量"
#label of y axis
LABEL_Y = u"请求量"
#color of the line
COLOR_LINE = '#4A7EBB'
#the alpha of the line 2d
ALPHA = .8

class Line(object):
    def __init__(self,fig,ax,real_time_data_method,dt=0.01):
        self.fig = fig
        self.ax = ax
        self.dt = dt
        self.crt_time = int(time.time())
        self.count = 0

        #max request access
        self.MAX_REQUEST = 0

        #initalize the Line2D which will paint in the figure
        self.xdata = []
        self.ydata = []
        self.line = Line2D(self.xdata,self.ydata,linewidth=1)
        #put the line 2d into the figure
        self.ax.add_line(self.line)

        #update the xticks and the yticks
        self.update_xaxis(self.ax)
        self.update_yaxis(self.ax,0)

        #aquire the data for updating each interval
        self.real_time_data_method = real_time_data_method
        if self.real_time_data_method is None:
            raise TypeError("function emitter will acquire data from real_time_data_method,but Real_time_data is None")

        self.format(self.ax)

    def format(self,ax):
        ax.grid(color='white', linestyle='solid')
        #add handle and legend
        ax.legend(handles=[self.line],labels=[LABLE_LINE % self.MAX_REQUEST])
        self.line.set_color(COLOR_LINE)
        ax.set_ylabel(LABEL_Y)
        self.line.set_alpha(ALPHA)
        plt.title(TITLE)
        pass

    def update_xaxis(self,ax):
        '''
        the start_datetime is the start of the scale and the end_datetime is the end of the scale
        '''
        self.xdata = []
        self.ydata = []
        start_hour,end_hour,start_secs,end_secs = self.tick_hour()
        xticks = pandas.date_range(start_hour,end_hour,freq=SCALE_INTERVAL)
        ax.xaxis.set_ticks([])
        ax.set_xlim(start_secs-self.crt_time, end_secs-self.crt_time)
        ax.xaxis.set_ticks(np.arange(start_secs-self.crt_time, end_secs-self.crt_time, TICK_INTERVAL))
        ax.xaxis.set_ticklabels([xtick.strftime("%H:%M") for xtick in xticks])
        plt.xticks(rotation=270)
        self.max_x = end_secs - self.crt_time
        self.ax.figure.canvas.draw()

    def update_yaxis(self,ax,crt_y):
        #with a multiple growth
        self.max_y = (crt_y / SCALE_Y) * SCALE_Y + SCALE_Y
        ax.set_ylim(START_Y,self.max_y)
        ax.figure.canvas.draw()

    def stamp_to_datetime(self,stamp):
        #convert stamp time to the datetime
        return datetime.fromtimestamp(stamp)

    def now_datetime(self):
        #return the current datetime
        return datetime.fromtimestamp(int(time.time()))

    def tick_hour(self):
        '''
        aquire the start seconds of current hour and the end seconds of current hour.The following is the sample.
        Eg: 2016-08-18 00:00:00 ~ 2016-08-18 00:59:59
        '''
        localtime = time.localtime()
        return datetime(localtime.tm_year,localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,00,00),\
               datetime(localtime.tm_year,localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,59,59),\
               int(time.mktime((localtime.tm_year,localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,00,00,
                            localtime.tm_wday,localtime.tm_yday,localtime.tm_isdst))),\
               int(time.mktime((localtime.tm_year,localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,59,59,
                            localtime.tm_wday,localtime.tm_yday,localtime.tm_isdst)))

        '''
        return datetime(localtime.tm_year,localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,localtime.tm_min,0),\
               datetime(localtime.tm_year,localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,localtime.tm_min,59),\
               int(time.mktime((localtime.tm_year,localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,localtime.tm_min,0,
                            localtime.tm_wday,localtime.tm_yday,localtime.tm_isdst))),\
               int(time.mktime((localtime.tm_year,localtime.tm_mon,localtime.tm_mday,localtime.tm_hour,localtime.tm_min,59,
                            localtime.tm_wday,localtime.tm_yday,localtime.tm_isdst)))
        '''

    def update(self,num):
        crt_x,crt_y = self.real_time_data_method()
        crt_x = crt_x - self.crt_time

        if crt_y > self.MAX_REQUEST:
            self.MAX_REQUEST = crt_y
            self.ax.legend(handles=[self.line],labels=[LABLE_LINE % self.MAX_REQUEST])


        # reset the arrays
        if crt_x > self.max_x and not crt_y > self.max_y:
            self.update_xaxis(self.ax)
        elif crt_y > self.max_y and not crt_x > self.max_x:
            self.update_yaxis(self.ax,crt_y)
        elif crt_x > self.max_x and crt_y > self.max_y:
            self.update_xaxis(self.ax)
            self.update_yaxis(self.ax,crt_y)

        self.xdata.append(crt_x)
        self.ydata.append(crt_y)
        self.line.set_data(self.xdata, self.ydata)
        return self.line,

    def paint(self):
        # pass a generator in "emitter" to produce data for the update func
        ani = animation.FuncAnimation(self.fig,self.update,interval=PAINTING_INTERVAL,blit=False)
        plt.show()


class Draw(object):
    def __init__(self,shape="",real_time_data_method=None):
        assert shape != ""
        self.shape = ""
        if shape == "line":
            fig, ax = plt.subplots(subplot_kw=dict(axisbg='#EEEEEE'))
            #fig = plt.figure()
            #ax = fig.add_subplot(111)
            self.shape = Line(fig,ax,real_time_data_method)
        elif shape == "circle":
            pass
        else:
            pass

    @property
    def Shape(self):
        return self.shape

if __name__ == '__main__':
    draw = Draw("line",lambda :(time.time(),0))
    draw.Shape.paint()