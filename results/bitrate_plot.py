import matplotlib.pyplot as plt
import pandas as pd

single_df = pd.read_csv ('results/single_cam.csv', usecols=['All packets'])
double_df = pd.read_csv ('results/double_cam.csv', usecols=['All packets'])
double_off_df = pd.read_csv ('results/double_cam_off.csv', usecols=['All packets'])
comb = pd.concat([single_df, double_df, double_off_df], axis=1)
comb.columns = ['Single Cam','Double Cam (On)','Double Cam (Off)']
print(len(comb))
print(comb.mean())
print((double_off_df - single_df).mean())
comb.plot()
window = 30
comb.rolling(window).mean().plot(xlabel='Time (s)',ylabel=f'Mean Bitrate (bits/s)',figsize=[10,5],grid=True)
plt.title(f"Mean Receiver Bitrate (window size {window})")
# comb.plot()
plt.show()