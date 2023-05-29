'''
!cluster will partition input vectors into n clusters,
using k-means clustering which minimises within cluster
variances.
'''

from typing import List

from aipl import defop

@defop('cluster', 1, 1, 1)
def op_cluster(aipl, v:List[List[float]], n=10):
    'Find n clusters in the input vectors.'
    import numpy as np
    from sklearn.cluster import KMeans

    matrix = np.vstack(v)
    kmeans = KMeans(n_clusters=n, init='k-means++', random_state=42, n_init='auto')
    kmeans.fit(matrix)

    return [int(x) for x in kmeans.labels_]
