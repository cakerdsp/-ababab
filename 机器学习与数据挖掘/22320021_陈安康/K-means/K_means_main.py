from K_means import Kmeans
import matplotlib.pyplot as plt
k_means = Kmeans(init_type='K++')
k_means2 = Kmeans(init_type='random')
k_means3 = Kmeans(init_type='distance_based')
k_means.kmeans()
k_means2.kmeans()
k_means3.kmeans()
k_means.show()
k_means2.show()
k_means3.show()
plt.show()