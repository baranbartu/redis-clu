# redis-clu
Redis Cluster Management Tool (Still development)
Create and manage redis cluster easily.

Also you can make your own monitoring screen using 'watch'.

    brew install watch (For Mac OSx)
    rclu status <cluster_node>
    watch -d -n 1 'rclu status localhost:6376'

Monitoring will help you to make an action.


##### Create cluster

```bash
rclu create localhost:6376,localhost:6377,localhost:6378
```


##### Show status

```bash
rclu status localhost:6376
```


##### Add masters

```bash
# single node:
rclu add localhost:6379

# multiple nodes:
# recommended for dynamic scaling, it will be split cluster into subclusters
# and each subcluster will be resharding simultaneously
# <cluster> <masters>
rclu multi_add localhost:6376 localhost:6381,localhost:6382
```


##### Add slaves

```bash
# <master> <slave>
rclu replicate localhost:6376 localhost:6385
```


##### Fix cluster

```bash
rclu fix localhost:6376
```


##### Reshard cluster (Slot balancing)

```bash
rclu reshard localhost:6376
```


##### Remove node

```bash
# <cluster> <master>
rclu remove localhost:6376 localhost:6380
```


##### Destroy cluster

```bash
rclu destroy localhost:6376
```


