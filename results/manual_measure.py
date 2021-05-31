import numpy as np
import matplotlib.pyplot as plt
################# DATA ###########################
rev_off = [170,190,220,220,160,200,280,190,170,200,310,210]
rev_on = [190,180,170,710,190,180,160,190,210,200,260]

def print_stats(d):
  print(np.mean(d), np.median(d), np.std(d))

plt.hist(rev_off)
print_stats(rev_off)


plt.figure()
plt.hist(rev_on)
print_stats(rev_on)
# plt.show()