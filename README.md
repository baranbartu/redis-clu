# redis-clu
Redis Cluster Management Tool (Still development)
Create and manage redis cluster easily.

Also you can use monitoring script which is 'watch-cluster.sh'. (Recommended with 'watch')
watch -d -n 1 'rclu status localhost:6376;./watch-cluster.sh -c localhost:6376'

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
# <cluster> <master>,<slave>
rclu replicate localhost:6376 localhost:6377,localhost:6385
```


##### Fix cluster

```bash
rclu fix localhost:6376
```


##### Reshard cluster

```bash
rclu reshard localhost:6376
```


##### Remove master

```bash
# <cluster> <master>
rclu remove localhost:6376 localhost:6380
```


##### Destroy cluster

```bash
rclu destroy localhost:6376
```


