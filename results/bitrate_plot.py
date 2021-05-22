import matplotlib.pyplot as plt
import pandas as pd

def plot(comb):
    # comb.plot()
    window = 1
    comb.rolling(window).mean().plot(xlabel='Time (s)',ylabel=f'Mean Bitrate (bits/s)',figsize=[10,5],grid=True)
    plt.title(f"Mean Receiver Bitrate (window size {window})")
    # comb.plot()
    plt.show()

# single_df = pd.read_csv ('results/single_cam.csv', usecols=['All packets'])
# double_df = pd.read_csv ('results/double_cam.csv', usecols=['All packets'])
# double_off_df = pd.read_csv ('results/double_cam_off.csv', usecols=['All packets'])
# comb = pd.concat([single_df, double_df, double_off_df], axis=1)
# comb.columns = ['Single Cam','Double Cam (On)','Double Cam (Off)']
# print(len(comb))
# print(comb.mean())
# print((double_off_df - single_df).mean())

fps30 = pd.read_csv ('results/30_fps.csv', usecols=['All packets'])
fps25 = pd.read_csv ('results/25_fps.csv', usecols=['All packets'])
fps15 = pd.read_csv ('results/15_fps.csv', usecols=['All packets'])
fps40 = pd.read_csv ('results/40_fps.csv', usecols=['All packets'])
comb = pd.concat([fps40, fps30, fps25, fps15], axis=1)
comb.columns = ['40 FPS','30 FPS','25 FPS','15 FPS']
plot(comb)

