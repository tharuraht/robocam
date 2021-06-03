import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
from statistics import median
# style.use('fivethirtyeight')

fig = plt.figure(figsize=(50,100))
ax1 = fig.add_subplot(1,1,1)

window_sz = 1

def animate(i):
    y_window = []
    graph_data = open('rec_bitrate.csv','r').read()
    lines = graph_data.split('\n')
    xs = []
    ys = []
    if len(lines) > 0:
        time_offset = int(lines[0].split(',')[0])
    for line in lines:
      # print(line)
        # if len(line) > 1:
        #     x, y = line.split(',')
        #     # y = min(int(y),1000)
        #     # y = max(int(y), -50)
        #     x = int(x) - time_offset

        #     if len(y_window) >= window_sz:
        #         y_window.pop(0) # Remove oldest value
        #     y_window.append(int(y))

        #     xs.append(int(x))
        #     ys.append(median(y_window))
      if line is not '':
        ys.append(int(line))
    ax1.clear()
    # ax1.set_ylim(-50,500)
    ax1.grid()
    plt.ylabel("Bitrate (bps)")
    # plt.xlabel("Time elapsed (ms)")
    ax1.plot(ys)

ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()