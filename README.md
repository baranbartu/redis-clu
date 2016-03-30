# redis-clu
Redis Cluster Management Tool (Still development)
Create and manage redis cluster easily.

Also you can make your own monitoring screen using 'watch'.

    brew install watch (For Mac OSx)
    redis-clu status <cluster_node>
    watch -d -n 1 'redis-clu status localhost:6376'

Monitoring will help you to make an action.


##### Create cluster

```bash
redis-clu create localhost:6376,localhost:6377,localhost:6378
```


##### Show status

```bash
redis-clu status localhost:6376
```


##### Add masters

```bash
# single node:
redis-clu add localhost:6379

# multiple nodes:
# recommended for dynamic scaling, it will be split cluster into subclusters
# and each subcluster will be resharding simultaneously
# <cluster> <masters>
redis-clu multi_add localhost:6376 localhost:6381,localhost:6382
```


##### Add slaves

```bash
# <master> <slave>
redis-clu replicate localhost:6376 localhost:6385
```


##### Fix cluster

```bash
redis-clu fix localhost:6376
```


##### Reshard cluster (Slot balancing)

```bash
redis-clu reshard localhost:6376
```


##### Remove node

```bash
# <cluster> <node(master or slave)>
redis-clu remove localhost:6376 localhost:6380
```


##### Flush/Destroy cluster

```bash
# flush cluster (initialize with 0 keys):
redis-clu reset localhost:6376

# destroy cluster:
redis-clu reset localhost:6376 --hard 1
```


# Monitoring

![ScreenShot](https://raw.github.com/baranbartu/redis-clu/master/screenshot.png)


